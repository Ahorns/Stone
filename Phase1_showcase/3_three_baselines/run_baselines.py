#!/usr/bin/env python3
"""Phase 1B Step 3 — score three baselines under the official WOSAC metrics.

Baselines (all defined in darwin_waymo.policies.baselines):
    1. log_replay         — copy the recorded ground-truth future
    2. constant_velocity  — extrapolate last (vx, vy) in a straight line
    3. rule_based         — lane-keeping + IDM + traffic-light + collision avoidance
                            (32 diverse parameter draws via existing RolloutEngine)

For each (scenario, baseline) pair:
    - run 32 rollouts × 80 steps
    - validate against submission_specs
    - compute the WOSAC SimAgentMetrics
    - record per-scenario dict

Outputs go under waymo/results/baselines/:
    - baseline_comparison.csv   one row per (scenario, baseline)
    - baseline_summary.md       aggregate summary table

Usage:
    python waymo/scripts/run_baselines.py                   # default 5 scenarios
    python waymo/scripts/run_baselines.py --limit 20        # 20 scenarios
    python waymo/scripts/run_baselines.py --limit 5 --baselines log_replay rule_based
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
# Don't blanket-disable CUDA — PyTorch needs it for the 'learned' baseline.
# TF 2.12 can't find its CUDA libs anyway, so it falls back to CPU on its own.

# Make darwin_waymo importable when run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import tensorflow as tf

# Pin TF to CPU explicitly so it doesn't fight PyTorch over CUDA libs.
# (TF 2.12's bundled CUDA expectations don't match PyTorch 2.6's CUDA 12.4 —
# initialising both leads to a segfault.)
try:
    tf.config.set_visible_devices([], "GPU")
except Exception:
    pass

from tqdm import tqdm

# Capture the original cwd before WOSAC's chdir so relative output paths
# resolve against the user's working directory, not the package install dir.
_ORIG_CWD = Path.cwd()

# WOSAC metrics need the package install dir as cwd to find their bundled config
import waymo_open_dataset
_pkg_root = os.path.dirname(waymo_open_dataset.__path__[0])
os.chdir(_pkg_root)

from waymo_open_dataset.protos import scenario_pb2
from waymo_open_dataset.utils.sim_agents import submission_specs
from waymo_open_dataset.wdl_limited.sim_agents_metrics import metrics

from darwin_waymo import paths
from darwin_waymo.features.scenario_parser import ScenarioParser
from darwin_waymo.submission.rollout_engine import RolloutEngine
from darwin_waymo.policies.baselines import BASELINES


CHALLENGE_TYPE = submission_specs.ChallengeType.SIM_AGENTS

# Fields we keep in the CSV. metametric is the headline score.
METRIC_FIELDS = [
    "metametric",
    "average_displacement_error",
    "min_average_displacement_error",
    "linear_speed_likelihood",
    "linear_acceleration_likelihood",
    "angular_speed_likelihood",
    "angular_acceleration_likelihood",
    "distance_to_nearest_object_likelihood",
    "collision_indication_likelihood",
    "time_to_collision_likelihood",
    "distance_to_road_edge_likelihood",
    "offroad_indication_likelihood",
    "traffic_light_violation_likelihood",
    "simulated_collision_rate",
    "simulated_offroad_rate",
    "simulated_traffic_light_violation_rate",
]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limit", type=int, default=5,
                   help="Number of scenarios from the shard (default 5)")
    p.add_argument("--shard", type=str, default=str(paths.DEFAULT_VALIDATION_SHARD),
                   help="Path to validation tfrecord shard")
    p.add_argument("--baselines", nargs="+", default=list(BASELINES.keys()),
                   choices=list(BASELINES.keys()), help="Subset of baselines to run")
    p.add_argument("--output", type=str, default=str(paths.BASELINES_RESULTS_DIR),
                   help="Output directory")
    return p.parse_args()


def metrics_to_dict(m) -> dict:
    """Extract scalar fields from a SimAgentMetrics proto."""
    out = {}
    for f in METRIC_FIELDS:
        if hasattr(m, f):
            out[f] = float(getattr(m, f))
        else:
            out[f] = float("nan")
    return out


def run_one(parsed, raw_proto, baseline_name: str, config) -> tuple[dict, float]:
    """Run one baseline on one scenario; return (metric_dict, wall_seconds) or ({}, t).

    Returns ({}, t) on failure so the runner can continue.
    """
    rollout_fn = BASELINES[baseline_name]
    t0 = time.time()
    try:
        sim_states = rollout_fn(parsed)
    except Exception as e:
        return {"error": f"rollout: {type(e).__name__}: {e}"}, time.time() - t0

    # Reuse the existing packager — it's policy-agnostic
    engine = RolloutEngine(n_rollouts=sim_states.shape[0])
    rollouts_proto = engine.package_submission(parsed, sim_states)

    try:
        submission_specs.validate_scenario_rollouts(rollouts_proto, raw_proto)
    except Exception as e:
        return {"error": f"validate: {type(e).__name__}: {e}"}, time.time() - t0

    try:
        m = metrics.compute_scenario_metrics_for_bundle(config, raw_proto, rollouts_proto)
    except Exception as e:
        return {"error": f"metric: {type(e).__name__}: {e}"}, time.time() - t0

    return metrics_to_dict(m), time.time() - t0


def main():
    args = parse_args()
    # Resolve relative paths against the *original* cwd captured at module
    # import (before the WOSAC chdir at the top of this file).
    def _abs(p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else (_ORIG_CWD / pp).resolve()
    out_dir = _abs(args.output)
    args.shard = str(_abs(args.shard))
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 64)
    print("  Phase 1B · Step 3 — Baseline Comparison")
    print("=" * 64)
    print(f"  shard      : {args.shard}")
    print(f"  scenarios  : {args.limit}")
    print(f"  baselines  : {', '.join(args.baselines)}")
    print(f"  output dir : {out_dir}")
    print("=" * 64)

    parser = ScenarioParser()
    config = metrics.load_metrics_config(CHALLENGE_TYPE)

    dataset = tf.data.TFRecordDataset([args.shard])
    raw_scenarios = list(dataset.take(args.limit).as_numpy_iterator())

    # ---- Stage 0 lesson: write per-scenario rows immediately ----
    csv_path = out_dir / "baseline_comparison.csv"
    status_path = out_dir / "status.json"
    fieldnames = ["scenario_id", "scenario_idx", "baseline", "n_sim_agents",
                  "wall_seconds"] + METRIC_FIELDS + ["error"]
    csv_fh = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_fh, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    csv_fh.flush()

    def write_status(scenarios_done: int, last_wall: float | None = None,
                     finished: bool = False):
        status = {
            "started": t_start_iso,
            "shard": str(args.shard),
            "baselines": list(args.baselines),
            "total": int(args.limit),
            "done": int(scenarios_done),
            "elapsed_seconds": round(time.time() - t_start, 1),
            "finished": bool(finished),
        }
        if last_wall is not None:
            status["last_baseline_seconds"] = round(last_wall, 2)
        status_path.write_text(json.dumps(status, indent=2))

    rows: list[dict] = []
    t_start = time.time()
    t_start_iso = time.strftime("%Y-%m-%d %H:%M:%S")
    write_status(0)

    for i, raw_bytes in enumerate(tqdm(raw_scenarios, desc="scenarios")):
        raw_proto = scenario_pb2.Scenario.FromString(raw_bytes)
        parsed = parser.parse(raw_proto)
        scenario_id = parsed.scenario_id

        for baseline in args.baselines:
            scores, wall = run_one(parsed, raw_proto, baseline, config)
            row = {
                "scenario_id": scenario_id,
                "scenario_idx": i,
                "baseline": baseline,
                "n_sim_agents": parsed.n_sim_agents,
                "wall_seconds": round(wall, 2),
            }
            row.update(scores)
            rows.append(row)
            # Append to CSV immediately + flush so the file is always current
            writer.writerow(row)
            csv_fh.flush()
            write_status(i, last_wall=wall)
            if "error" in scores:
                tqdm.write(f"  [{baseline}] {scenario_id[:8]}: ERROR — {scores['error']}")
            else:
                tqdm.write(f"  [{baseline}] {scenario_id[:8]}: metametric={scores.get('metametric', float('nan')):.3f} ({wall:.1f}s)")

    elapsed = time.time() - t_start
    csv_fh.close()
    write_status(args.limit, finished=True)
    print(f"\nWrote {csv_path}  ({len(rows)} rows)")

    # ---------------- aggregate summary ----------------
    summary: dict[str, dict[str, float]] = {b: {} for b in args.baselines}
    for b in args.baselines:
        baseline_rows = [r for r in rows if r["baseline"] == b and "error" not in r]
        if not baseline_rows:
            continue
        for f in METRIC_FIELDS:
            vals = [r[f] for r in baseline_rows if not (isinstance(r[f], float) and np.isnan(r[f]))]
            if vals:
                summary[b][f] = float(np.mean(vals))
            else:
                summary[b][f] = float("nan")
        summary[b]["n_scored"] = len(baseline_rows)
        summary[b]["mean_wall_seconds"] = float(np.mean([r["wall_seconds"] for r in baseline_rows]))

    md_path = out_dir / "baseline_summary.md"
    with open(md_path, "w") as fh:
        fh.write("# Phase 1B · Step 3 — Baseline Comparison\n\n")
        fh.write(f"- Shard: `{Path(args.shard).name}`\n")
        fh.write(f"- Scenarios scored: {args.limit}\n")
        fh.write(f"- Total wall time: {elapsed:.1f} s\n")
        fh.write(f"- Generated: `python waymo/scripts/run_baselines.py --limit {args.limit}`\n\n")

        fh.write("## Headline metric (metametric — higher is better)\n\n")
        fh.write("| Baseline | metametric | scenarios | mean wall (s) |\n")
        fh.write("|---|---|---|---|\n")
        for b in args.baselines:
            s = summary.get(b, {})
            mm = s.get("metametric", float("nan"))
            n = s.get("n_scored", 0)
            wt = s.get("mean_wall_seconds", float("nan"))
            fh.write(f"| `{b}` | {mm:.4f} | {n} | {wt:.2f} |\n")

        fh.write("\n## Sub-metrics (mean across scenarios)\n\n")
        # Wide table — baselines as columns
        fh.write("| Metric | " + " | ".join(f"`{b}`" for b in args.baselines) + " |\n")
        fh.write("|---" * (1 + len(args.baselines)) + "|\n")
        for f in METRIC_FIELDS:
            row = [f]
            for b in args.baselines:
                val = summary.get(b, {}).get(f, float("nan"))
                row.append(f"{val:.4f}" if not np.isnan(val) else "—")
            fh.write("| " + " | ".join(row) + " |\n")

        fh.write("\n## Reference scores (from WOSAC paper / leaderboard)\n\n")
        fh.write("| System | metametric |\n|---|---|\n")
        fh.write("| Random Gaussian        | 0.155 |\n")
        fh.write("| Constant Velocity      | 0.287 |\n")
        fh.write("| CV + Gaussian Noise    | 0.324 |\n")
        fh.write("| SBTA-AIDA              | 0.338 |\n")
        fh.write("| Wayformer (Diverse)    | 0.531 |\n")

        fh.write("\n## Diagnostic notes\n\n")
        fh.write("- `log_replay` and `constant_velocity` produce 32 *identical* rollouts (no diversity).\n")
        fh.write("  WOSAC scores rollouts as a distribution match, so identical rollouts under-score on\n")
        fh.write("  diversity-sensitive features. The gap between log_replay and Wayformer is partly diversity.\n")
        fh.write("- `rule_based` gets diversity for free via parameter perturbation in `RolloutEngine`.\n")
        fh.write("- This is a single shard (~290 scenarios). Aggregate scores will move once the full validation\n")
        fh.write("  set is available.\n")

    print(f"Wrote {md_path}")
    print(f"\nDone in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
