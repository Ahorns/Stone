"""Three Phase 1B baselines, each producing the WOSAC rollout array.

All three return an array of shape (n_rollouts, n_agents, 80, 4) where
the last dim is (x, y, z, heading), compatible with
`RolloutEngine.package_submission`.

Baselines:
    - log_replay_rollout       : copy the recorded ground-truth future
    - constant_velocity_rollout: extrapolate last valid (vx, vy)
    - rule_based_rollout       : delegates to RolloutEngine (rule_engine policy)

Diversity note:
    log_replay and constant_velocity are deterministic — every one of the 32
    rollouts is identical. This is intentional. The WOSAC metric rewards
    distribution match, so a single deterministic trajectory underscores how
    much of the score comes from diversity. Rule-based gets diversity for free
    via parameter perturbation in `RolloutEngine._create_diverse_policies`.
"""
from __future__ import annotations

import numpy as np

from darwin_waymo.features.scenario_parser import ParsedScenario


N_SIM_STEPS = 80
N_ROLLOUTS = 32


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_shape(arr: np.ndarray) -> np.ndarray:
    assert arr.ndim == 4 and arr.shape[2] == N_SIM_STEPS and arr.shape[3] == 4, (
        f"baseline must return (n_rollouts, n_agents, {N_SIM_STEPS}, 4) — got {arr.shape}"
    )
    return arr.astype(np.float32, copy=False)


def _last_valid_xyz_heading(track, up_to: int) -> np.ndarray:
    """Return [x, y, z, heading] of the most recent valid step at or before `up_to`."""
    for t in range(up_to, -1, -1):
        if track.valid[t]:
            s = track.states[t]
            return np.array([s[0], s[1], s[2], s[3]], dtype=np.float32)
    # No valid state found — should be rare; return zeros.
    return np.zeros(4, dtype=np.float32)


def _last_valid_full(track, up_to: int) -> np.ndarray:
    """Return the full 10-d state at the most recent valid step (or zeros)."""
    for t in range(up_to, -1, -1):
        if track.valid[t]:
            return track.states[t].copy()
    return np.zeros(10, dtype=np.float32)


# ---------------------------------------------------------------------------
# Baseline 1 — log replay (the recorded ground truth)
# ---------------------------------------------------------------------------

def log_replay_rollout(parsed: ParsedScenario, n_rollouts: int = N_ROLLOUTS) -> np.ndarray:
    """Copy the recorded ground-truth future; forward-fill invalid steps.

    Valid only on training/validation (test set has no future). Useful as a
    diagnostic *upper bound* for the WOSAC score on validation.
    """
    sim_ids = parsed.sim_agent_ids
    n_agents = len(sim_ids)
    t0 = parsed.current_time_index  # last observed step

    rollout = np.zeros((n_agents, N_SIM_STEPS, 4), dtype=np.float32)

    for idx, aid in enumerate(sim_ids):
        track = parsed.agents[aid]
        last = _last_valid_xyz_heading(track, t0)
        cur = last.copy()
        for step in range(N_SIM_STEPS):
            t = t0 + 1 + step
            if t < track.states.shape[0] and track.valid[t]:
                s = track.states[t]
                cur = np.array([s[0], s[1], s[2], s[3]], dtype=np.float32)
            # else: forward-fill the most recent valid value
            rollout[idx, step] = cur

    out = np.broadcast_to(rollout, (n_rollouts,) + rollout.shape).copy()
    return _ensure_shape(out)


# ---------------------------------------------------------------------------
# Baseline 2 — constant velocity (linear extrapolation)
# ---------------------------------------------------------------------------

def constant_velocity_rollout(
    parsed: ParsedScenario,
    n_rollouts: int = N_ROLLOUTS,
    dt: float = 0.1,
) -> np.ndarray:
    """Each agent extrapolates its last valid (vx, vy) in a straight line.

    Heading and z are held constant from the last valid frame.
    Identical across all 32 rollouts — no diversity by design.
    """
    sim_ids = parsed.sim_agent_ids
    n_agents = len(sim_ids)
    t0 = parsed.current_time_index

    rollout = np.zeros((n_agents, N_SIM_STEPS, 4), dtype=np.float32)

    for idx, aid in enumerate(sim_ids):
        track = parsed.agents[aid]
        s = _last_valid_full(track, t0)
        x0, y0, z0, heading0 = s[0], s[1], s[2], s[3]
        vx, vy = s[4], s[5]
        for step in range(N_SIM_STEPS):
            dt_total = (step + 1) * dt
            rollout[idx, step] = (
                x0 + vx * dt_total,
                y0 + vy * dt_total,
                z0,
                heading0,
            )

    out = np.broadcast_to(rollout, (n_rollouts,) + rollout.shape).copy()
    return _ensure_shape(out)


# ---------------------------------------------------------------------------
# Baseline 3 — rule-based (lane-keep + IDM + traffic-light + collision avoid)
# ---------------------------------------------------------------------------

def rule_based_rollout(
    parsed: ParsedScenario,
    n_rollouts: int = N_ROLLOUTS,
    seed: int = 42,
) -> np.ndarray:
    """Delegate to the existing RolloutEngine (32 diverse rule-based policies)."""
    # Local import to avoid circular import via policies/__init__
    from darwin_waymo.submission.rollout_engine import RolloutEngine
    engine = RolloutEngine(n_rollouts=n_rollouts)
    return _ensure_shape(engine.run_scenario(parsed, seed=seed))


# ---------------------------------------------------------------------------
# Baseline 4 — learned next-step predictor (Step 4 deliverable)
# ---------------------------------------------------------------------------

def learned_rollout(
    parsed: ParsedScenario,
    n_rollouts: int = N_ROLLOUTS,
    seed: int = 42,
) -> np.ndarray:
    """Wrap the trained MLPNextStep model as a baseline.

    Reads the checkpoint at the default path
        waymo/results/step4/checkpoints/best_val.pt
    so the runner can call this without extra config. Override via the env
    var DARWIN_WAYMO_LEARNED_CKPT if needed.
    """
    import os
    from pathlib import Path
    from darwin_waymo import paths
    from darwin_waymo.learned.policy import learned_rollout as _impl

    ckpt = os.environ.get(
        "DARWIN_WAYMO_LEARNED_CKPT",
        str(paths.RESULTS_DIR / "step4" / "checkpoints" / "best_val.pt"),
    )
    if not Path(ckpt).exists():
        raise FileNotFoundError(
            f"Learned-model checkpoint not found at {ckpt}. "
            "Run `python waymo/scripts/prepare_dataset.py` then "
            "`python waymo/scripts/train_step4.py` first."
        )
    # CPU is faster and conflict-free in a process where TF is already loaded;
    # PyTorch + TF 2.12 fight over CUDA libs and segfault. Override via
    # DARWIN_WAYMO_LEARNED_DEVICE if your environment is clean.
    device = os.environ.get("DARWIN_WAYMO_LEARNED_DEVICE", "cpu")
    sample = os.environ.get("DARWIN_WAYMO_LEARNED_SAMPLE", "1") != "0"
    return _ensure_shape(_impl(
        parsed, checkpoint_path=ckpt, n_rollouts=n_rollouts, seed=seed,
        device=device, sample=sample,
    ))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

BASELINES = {
    "log_replay": log_replay_rollout,
    "constant_velocity": constant_velocity_rollout,
    "rule_based": rule_based_rollout,
    "learned": learned_rollout,
}
