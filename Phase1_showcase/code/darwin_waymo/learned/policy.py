"""LearnedPolicy: rollout the trained next-step predictor for WOSAC scoring.

Produces a (n_rollouts, n_agents, 80, 4) array compatible with
RolloutEngine.package_submission.

Design notes:
    - Inputs come from the existing AgentFeatureExtractor (44 dim).
    - Per step, all agents are batched into one GPU forward pass.
    - Diversity across the 32 rollouts comes from per-rollout sampling noise.
    - The model predicts in EGO frame (Δfwd, Δlat, Δh); we rotate to world.
    - Z is held constant from the last observed frame.

Known limitations (for the Step 4 report):
    - The feature extractor's "previous step" used for accel/heading_rate uses
      the recorded track, even during rollout. For history steps this is
      correct; for future steps near t0 it's ~OK; for steps deeper into the
      rollout the discrepancy compounds. Phase 2 will address.
    - Per-agent independent prediction. WOSAC factorisation is satisfied
      because each agent's next state depends only on the previous joint
      state — but social interaction has to come through neighbour features
      alone. Phase 2 will add explicit agent–agent attention.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from darwin_waymo.features.agent_features import (
    AgentFeatureExtractor, TOTAL_FEATURES,
)
from darwin_waymo.features.scenario_parser import (
    AgentState, ParsedScenario,
    AGENT_TYPE_VEHICLE,
)
from darwin_waymo.learned.model import MLPNextStep, ModelConfig


N_SIM_STEPS = 80
N_ROLLOUTS = 32


@dataclass
class _AgentSnapshot:
    x: float
    y: float
    z: float
    heading: float
    vx: float
    vy: float
    speed: float
    length: float
    width: float
    height: float
    valid: bool = True

    def to_state(self) -> AgentState:
        return AgentState(
            x=self.x, y=self.y, z=self.z, heading=self.heading,
            vx=self.vx, vy=self.vy, speed=self.speed,
            length=self.length, width=self.width, height=self.height,
            valid=self.valid,
        )


def load_checkpoint(path: str | Path, device: str = "cuda") -> tuple[MLPNextStep, np.ndarray, np.ndarray]:
    """Returns (model on device, x_mean, x_std)."""
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"
    ckpt = torch.load(path, map_location=device, weights_only=False)
    cfg = ModelConfig(**ckpt["model_cfg"])
    model = MLPNextStep(cfg).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    x_mean = ckpt["x_mean"].astype(np.float32)
    x_std = ckpt["x_std"].astype(np.float32)
    return model, x_mean, x_std


def _wrap_angle(a: float) -> float:
    return (a + np.pi) % (2 * np.pi) - np.pi


def learned_rollout(
    parsed: ParsedScenario,
    *,
    checkpoint_path: str | Path,
    n_rollouts: int = N_ROLLOUTS,
    device: str = "cuda",
    seed: int = 42,
    sample: bool = True,
) -> np.ndarray:
    """Run the learned next-step predictor as a sim-agent policy.

    Args:
        parsed: parsed scenario.
        checkpoint_path: path to a .pt produced by train.py.
        n_rollouts: number of rollouts (default 32).
        device: 'cuda' or 'cpu'.
        seed: base RNG seed (per-rollout offset added).
        sample: if True, sample from Gaussian; else use the mean (deterministic).

    Returns:
        sim_states: (n_rollouts, n_agents, 80, 4) — (x, y, z, heading)
    """
    model, x_mean, x_std = load_checkpoint(checkpoint_path, device=device)
    x_mean_t = torch.from_numpy(x_mean).to(device)
    x_std_t = torch.from_numpy(x_std).to(device)

    sim_ids = parsed.sim_agent_ids
    n_agents = len(sim_ids)
    t0 = parsed.current_time_index

    # Static box dimensions per agent (frozen at t0 per WOSAC rules)
    static_dims: dict[int, tuple[float, float, float]] = {}
    for aid in sim_ids:
        track = parsed.agents[aid]
        s = track.last_valid_state(t0)
        if s is not None:
            static_dims[aid] = (s.length, s.width, s.height)
        else:
            static_dims[aid] = (4.5, 2.0, 1.6)  # vehicle defaults

    # Build a single AgentFeatureExtractor for this scenario (reused across
    # rollouts and steps; cheap because it caches the map extractor).
    extractor = AgentFeatureExtractor(parsed)

    out = np.zeros((n_rollouts, n_agents, N_SIM_STEPS, 4), dtype=np.float32)

    # Per-rollout RNG (numpy for diversity; torch for sampling on device)
    for r in range(n_rollouts):
        rng = np.random.default_rng(seed + r)
        torch_gen = torch.Generator(device=device)
        torch_gen.manual_seed(seed + r)

        # Initialise current snapshots from last observed states
        current: dict[int, _AgentSnapshot] = {}
        for aid in sim_ids:
            track = parsed.agents[aid]
            s = track.last_valid_state(t0)
            L, W, H = static_dims[aid]
            if s is not None:
                current[aid] = _AgentSnapshot(
                    x=float(s.x), y=float(s.y), z=float(s.z),
                    heading=float(s.heading),
                    vx=float(s.vx), vy=float(s.vy), speed=float(s.speed),
                    length=L, width=W, height=H,
                )
            else:
                current[aid] = _AgentSnapshot(
                    x=0.0, y=0.0, z=0.0, heading=0.0,
                    vx=0.0, vy=0.0, speed=0.0,
                    length=L, width=W, height=H, valid=False,
                )

        for step in range(N_SIM_STEPS):
            # Build dict of current AgentStates for the extractor
            all_states = {aid: snap.to_state() for aid, snap in current.items()}
            # Extract features for every agent in one batch
            feats = np.zeros((n_agents, TOTAL_FEATURES), dtype=np.float32)
            for idx, aid in enumerate(sim_ids):
                f = extractor.extract(aid, t0 + step + 1, all_agent_states=all_states)
                if f is not None:
                    feats[idx] = f.vector
            X = torch.from_numpy(feats).to(device)
            X = (X - x_mean_t) / x_std_t

            with torch.no_grad():
                mu, log_sigma = model(X)
                if sample:
                    sigma = log_sigma.exp()
                    eps = torch.randn(mu.shape, generator=torch_gen, device=device)
                    delta = (mu + sigma * eps).cpu().numpy()
                else:
                    delta = mu.cpu().numpy()

            # delta is (n_agents, 3) in EGO frame
            for idx, aid in enumerate(sim_ids):
                snap = current[aid]
                d_fwd, d_lat, d_h = float(delta[idx, 0]), float(delta[idx, 1]), float(delta[idx, 2])
                cos_h, sin_h = np.cos(snap.heading), np.sin(snap.heading)
                dx = d_fwd * cos_h - d_lat * sin_h
                dy = d_fwd * sin_h + d_lat * cos_h
                snap.x += dx
                snap.y += dy
                snap.heading = _wrap_angle(snap.heading + d_h)
                # Update velocity proxy from displacement (10 Hz)
                snap.vx = dx * 10.0
                snap.vy = dy * 10.0
                snap.speed = float(np.hypot(snap.vx, snap.vy))
                # Z held constant
                out[r, idx, step, 0] = snap.x
                out[r, idx, step, 1] = snap.y
                out[r, idx, step, 2] = snap.z
                out[r, idx, step, 3] = snap.heading

    return out
