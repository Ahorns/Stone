#!/usr/bin/env python3
"""Stage 1 — build the learned-model training dataset from a validation shard.

For each sim-agent in each scenario:
    extract every valid (t, t+1) transition as (features 44-d, target 3-d).

Train/val split is by scenario id (~80/20 default).
Outputs:
    waymo/results/step4/dataset/train.npz
    waymo/results/step4/dataset/val.npz
    waymo/results/step4/dataset/stats.json

Usage:
    python waymo/scripts/prepare_dataset.py                     # full shard
    python waymo/scripts/prepare_dataset.py --limit 5           # smoke test
    python waymo/scripts/prepare_dataset.py --val-frac 0.2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")  # TF stays on CPU

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import tensorflow as tf
from tqdm import tqdm

from waymo_open_dataset.protos import scenario_pb2

from darwin_waymo import paths
from darwin_waymo.features.scenario_parser import ScenarioParser
from darwin_waymo.learned.dataset import (
    extract_scenario_samples, save_npz, stats_from_arrays,
)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--shard", default=str(paths.DEFAULT_VALIDATION_SHARD))
    p.add_argument("--limit", type=int, default=None,
                   help="Max scenarios from shard (default = all in shard)")
    p.add_argument("--val-frac", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default=str(paths.RESULTS_DIR / "step4" / "dataset"))
    p.add_argument("--no-history", action="store_true",
                   help="Skip transitions in the history window (use only future)")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 64)
    print("  Phase 1B · Step 4 · Stage 1 — Dataset extraction")
    print("=" * 64)
    print(f"  shard      : {args.shard}")
    print(f"  limit      : {args.limit if args.limit else 'all'}")
    print(f"  val-frac   : {args.val_frac}")
    print(f"  output     : {out_dir}")
    print(f"  use_history: {not args.no_history}")
    print("=" * 64)

    parser = ScenarioParser()
    dataset = tf.data.TFRecordDataset([args.shard])
    if args.limit:
        dataset = dataset.take(args.limit)
    raw_scenarios = list(dataset.as_numpy_iterator())

    rng = np.random.default_rng(args.seed)
    n_total = len(raw_scenarios)
    perm = rng.permutation(n_total)
    n_val = int(round(args.val_frac * n_total))
    val_idx = set(perm[:n_val].tolist())

    train_X, train_Y, train_T, train_ids = [], [], [], []
    val_X, val_Y, val_T, val_ids = [], [], [], []
    skipped = 0

    status_path = out_dir / "status.json"

    def write_status(done: int, last_scenario_seconds: float | None = None,
                     finished: bool = False):
        s = {
            "started": t0_iso,
            "shard": str(args.shard),
            "limit": args.limit,
            "total": int(n_total),
            "done": int(done),
            "skipped": int(skipped),
            "n_train_samples_so_far": int(sum(x.shape[0] for x in train_X)),
            "n_val_samples_so_far": int(sum(x.shape[0] for x in val_X)),
            "elapsed_seconds": round(time.time() - t0, 1),
            "finished": bool(finished),
        }
        if last_scenario_seconds is not None:
            s["last_scenario_seconds"] = round(last_scenario_seconds, 2)
        status_path.write_text(json.dumps(s, indent=2))

    t0 = time.time()
    t0_iso = time.strftime("%Y-%m-%d %H:%M:%S")
    write_status(0)

    for i, raw in enumerate(raw_scenarios):
        t_sc = time.time()
        try:
            proto = scenario_pb2.Scenario.FromString(raw)
            parsed = parser.parse(proto)
            X, Y, T = extract_scenario_samples(parsed, use_history_steps=not args.no_history)
            if X.shape[0] == 0:
                skipped += 1
            elif i in val_idx:
                val_X.append(X); val_Y.append(Y); val_T.append(T)
                val_ids.append(parsed.scenario_id)
            else:
                train_X.append(X); train_Y.append(Y); train_T.append(T)
                train_ids.append(parsed.scenario_id)
        except Exception as e:
            print(f"  scenario {i}: skipped ({type(e).__name__}: {e})", flush=True)
            skipped += 1
        sc_secs = time.time() - t_sc
        if (i + 1) % 10 == 0 or i == n_total - 1:
            print(f"  [{i+1:>3d}/{n_total}] last_scenario={sc_secs:.1f}s  "
                  f"train={sum(x.shape[0] for x in train_X):>7d}  "
                  f"val={sum(x.shape[0] for x in val_X):>6d}  "
                  f"elapsed={time.time()-t0:.1f}s", flush=True)
        write_status(i + 1, last_scenario_seconds=sc_secs)

    elapsed = time.time() - t0
    write_status(n_total, finished=True)

    train_X = np.concatenate(train_X) if train_X else np.zeros((0, 44), np.float32)
    train_Y = np.concatenate(train_Y) if train_Y else np.zeros((0, 3), np.float32)
    train_T = np.concatenate(train_T) if train_T else np.zeros((0,), np.int32)
    val_X = np.concatenate(val_X) if val_X else np.zeros((0, 44), np.float32)
    val_Y = np.concatenate(val_Y) if val_Y else np.zeros((0, 3), np.float32)
    val_T = np.concatenate(val_T) if val_T else np.zeros((0,), np.int32)

    save_npz(out_dir / "train.npz", train_X, train_Y, train_T, train_ids)
    save_npz(out_dir / "val.npz", val_X, val_Y, val_T, val_ids)

    train_stats = stats_from_arrays(train_X, train_Y, train_T)
    val_stats = stats_from_arrays(val_X, val_Y, val_T)
    train_stats.n_scenarios = len(train_ids)
    val_stats.n_scenarios = len(val_ids)

    summary = {
        "shard": args.shard,
        "limit": args.limit,
        "n_scenarios_total": n_total,
        "n_scenarios_skipped": skipped,
        "elapsed_seconds": round(elapsed, 1),
        "use_history": not args.no_history,
        "train": {
            "n_scenarios": train_stats.n_scenarios,
            "n_samples": train_stats.n_samples,
            "agent_type_counts": train_stats.agent_type_counts,
            "target_mean": train_stats.target_mean.tolist(),
            "target_std": train_stats.target_std.tolist(),
        },
        "val": {
            "n_scenarios": val_stats.n_scenarios,
            "n_samples": val_stats.n_samples,
            "agent_type_counts": val_stats.agent_type_counts,
            "target_mean": val_stats.target_mean.tolist(),
            "target_std": val_stats.target_std.tolist(),
        },
    }
    (out_dir / "stats.json").write_text(json.dumps(summary, indent=2))

    print(f"\n  scenarios     : {n_total} (skipped {skipped})")
    print(f"  train samples : {train_stats.n_samples:>9d}  ({train_stats.n_scenarios} scenarios)")
    print(f"  val samples   : {val_stats.n_samples:>9d}  ({val_stats.n_scenarios} scenarios)")
    print(f"  elapsed       : {elapsed:.1f} s")
    print(f"  saved to      : {out_dir}")


if __name__ == "__main__":
    main()
