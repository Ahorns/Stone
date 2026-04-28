"""Dataset extraction for the learned next-step predictor.

Produces (X, Y, agent_type) numpy arrays from validation scenarios:

    X[i]          = AgentFeatureExtractor.extract(...).vector  shape (44,)
    Y[i]          = (Δforward, Δlateral, Δheading) in EGO frame  shape (3,)
    agent_type[i] = 1 vehicle / 2 pedestrian / 3 cyclist         shape ()

Targets are expressed in the agent's ego frame at time t:
    Δforward =  Δx_world cos(h) + Δy_world sin(h)
    Δlateral = -Δx_world sin(h) + Δy_world cos(h)

This makes the regression rotation-invariant — the same physical "step
forward" produces the same target regardless of the scenario's world
orientation.

Each sample is one valid (t, t+1) transition for one sim-agent in one scenario.
Train/val split is by scenario_id to avoid leakage.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

from darwin_waymo.features.agent_features import (
    AgentFeatureExtractor, TOTAL_FEATURES,
)
from darwin_waymo.features.scenario_parser import ParsedScenario


N_TARGET = 3  # Δx, Δy, Δheading


def _wrap_angle(a: np.ndarray) -> np.ndarray:
    return (a + np.pi) % (2 * np.pi) - np.pi


def extract_scenario_samples(
    parsed: ParsedScenario,
    *,
    use_history_steps: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract every valid (t, t+1) transition for every sim-agent in one scenario.

    Args:
        parsed: A parsed Waymo scenario.
        use_history_steps: If True, include transitions in the history window
            (t < current_time_index). Future transitions are always used.

    Returns:
        X         (N, 44)
        Y         (N, 3)   — (Δx, Δy, Δheading) at +1 step
        atype     (N,)     — int agent type (1/2/3)
    """
    extractor = AgentFeatureExtractor(parsed)
    n_steps = parsed.n_timesteps
    t0 = parsed.current_time_index
    start_t = 0 if use_history_steps else t0

    Xs: List[np.ndarray] = []
    Ys: List[np.ndarray] = []
    Ts: List[int] = []

    for aid in parsed.sim_agent_ids:
        track = parsed.agents.get(aid)
        if track is None:
            continue
        states = track.states           # (n_steps, 10)
        valid = track.valid             # (n_steps,)
        for t in range(start_t, n_steps - 1):
            if not (valid[t] and valid[t + 1]):
                continue
            feat = extractor.extract(aid, t)
            if feat is None:
                continue
            dx_w = states[t + 1, 0] - states[t, 0]
            dy_w = states[t + 1, 1] - states[t, 1]
            dh = _wrap_angle(states[t + 1, 3] - states[t, 3])
            # Rotate (dx_w, dy_w) into ego frame using current heading
            h = states[t, 3]
            cos_h, sin_h = np.cos(h), np.sin(h)
            dx_ego = dx_w * cos_h + dy_w * sin_h
            dy_ego = -dx_w * sin_h + dy_w * cos_h
            Xs.append(feat.vector)
            Ys.append(np.array([dx_ego, dy_ego, dh], dtype=np.float32))
            Ts.append(track.agent_type)

    if not Xs:
        return (np.zeros((0, TOTAL_FEATURES), dtype=np.float32),
                np.zeros((0, N_TARGET), dtype=np.float32),
                np.zeros((0,), dtype=np.int32))

    return (np.stack(Xs).astype(np.float32),
            np.stack(Ys).astype(np.float32),
            np.array(Ts, dtype=np.int32))


@dataclass
class DatasetStats:
    n_samples: int
    n_scenarios: int
    agent_type_counts: dict
    target_mean: np.ndarray
    target_std: np.ndarray


def stats_from_arrays(X: np.ndarray, Y: np.ndarray, atype: np.ndarray) -> DatasetStats:
    return DatasetStats(
        n_samples=int(Y.shape[0]),
        n_scenarios=-1,  # filled in by the caller
        agent_type_counts={int(k): int(v) for k, v in zip(*np.unique(atype, return_counts=True))},
        target_mean=Y.mean(axis=0).astype(np.float32),
        target_std=Y.std(axis=0).astype(np.float32),
    )


def save_npz(path: Path, X: np.ndarray, Y: np.ndarray, atype: np.ndarray,
             scenario_ids: List[str]) -> None:
    np.savez_compressed(
        path,
        X=X.astype(np.float32),
        Y=Y.astype(np.float32),
        agent_type=atype.astype(np.int32),
        scenario_ids=np.array(scenario_ids, dtype=object),
    )


def load_npz(path: Path):
    data = np.load(path, allow_pickle=True)
    return (data["X"], data["Y"], data["agent_type"], data["scenario_ids"].tolist())
