"""Waymo fitness evaluation — fast proxy + optional full WOSAC.

The fast proxy computes lightweight metrics in pure numpy so evolution
can run hundreds of generations quickly. The full WOSAC evaluation
uses the official Waymo SDK and is used periodically for validation.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from darwin_waymo.features.scenario_parser import ParsedScenario, AgentState
from darwin_waymo.features.map_features import MapFeatureExtractor


def compute_proxy_fitness(
    simulated_states: np.ndarray,
    scenario: ParsedScenario,
    map_extractor: MapFeatureExtractor,
) -> float:
    """Fast proxy fitness for evolutionary selection.

    Args:
        simulated_states: shape (n_agents, n_steps, 4) — one rollout
        scenario: The parsed scenario with ground truth
        map_extractor: For road edge / offroad checks

    Returns:
        Fitness score in [0, 1] range. Higher is better.
    """
    n_agents, n_steps, _ = simulated_states.shape
    sim_ids = scenario.sim_agent_ids
    t0 = scenario.current_time_index

    # === 1. Kinematic realism (0.25 weight) ===
    # Check speed and acceleration distributions match ground truth
    kinematic_score = _kinematic_realism(simulated_states, scenario, sim_ids, t0)

    # === 2. Collision avoidance (0.30 weight — 2x in WOSAC) ===
    collision_rate = _collision_rate(simulated_states, scenario, sim_ids, t0)
    collision_score = 1.0 - collision_rate

    # === 3. Map compliance / offroad (0.30 weight — 2x in WOSAC) ===
    offroad_rate = _offroad_rate(simulated_states, map_extractor)
    map_score = 1.0 - offroad_rate

    # === 4. Trajectory smoothness (0.15 weight) ===
    smoothness = _smoothness_score(simulated_states)

    fitness = (
        0.25 * kinematic_score
        + 0.30 * collision_score
        + 0.30 * map_score
        + 0.15 * smoothness
    )

    return float(np.clip(fitness, 0.0, 1.0))


def _kinematic_realism(
    sim_states: np.ndarray,
    scenario: ParsedScenario,
    sim_ids: List[int],
    t0: int,
) -> float:
    """Check if simulated speeds match the ground truth distribution."""
    # Get GT speeds at observation time
    gt_speeds = []
    for aid in sim_ids:
        track = scenario.agents[aid]
        if track.valid[t0]:
            state = track.state_at(t0)
            gt_speeds.append(state.speed)

    if not gt_speeds:
        return 0.5

    gt_mean_speed = np.mean(gt_speeds)
    gt_std_speed = max(np.std(gt_speeds), 0.1)

    # Get simulated speeds (from position differences)
    dx = np.diff(sim_states[:, :, 0], axis=1)  # (n_agents, n_steps-1)
    dy = np.diff(sim_states[:, :, 1], axis=1)
    sim_speeds = np.sqrt(dx**2 + dy**2) / 0.1  # convert to m/s

    sim_mean_speed = np.mean(sim_speeds)

    # Score based on how close means are
    speed_error = abs(sim_mean_speed - gt_mean_speed) / max(gt_mean_speed, 1.0)
    speed_score = max(0, 1.0 - speed_error)

    # Penalize unrealistic speeds (>40 m/s or negative-implied)
    max_sim_speed = np.max(sim_speeds) if sim_speeds.size > 0 else 0
    if max_sim_speed > 40.0:
        speed_score *= 0.5

    return float(speed_score)


def _collision_rate(
    sim_states: np.ndarray,
    scenario: ParsedScenario,
    sim_ids: List[int],
    t0: int,
) -> float:
    """Fraction of timesteps with at least one collision."""
    n_agents, n_steps, _ = sim_states.shape
    if n_agents < 2:
        return 0.0

    # Get agent sizes
    sizes = np.zeros((n_agents, 2), dtype=np.float32)  # (length, width)
    for idx, aid in enumerate(sim_ids):
        track = scenario.agents[aid]
        sizes[idx, 0] = track.states[t0, 7]  # length
        sizes[idx, 1] = track.states[t0, 8]  # width

    collision_steps = 0
    # Check every 5th step for speed (collisions are persistent)
    check_steps = range(0, n_steps, 5)

    for step in check_steps:
        positions = sim_states[:, step, :2]  # (n_agents, 2)
        # Pairwise distances
        diffs = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]  # (N, N, 2)
        dists = np.linalg.norm(diffs, axis=2)  # (N, N)

        # Collision threshold: sum of half-lengths (simplified box check)
        min_dists = (sizes[:, 0, np.newaxis] + sizes[np.newaxis, :, 0]) * 0.4
        np.fill_diagonal(dists, 999.0)  # ignore self
        np.fill_diagonal(min_dists, 0.0)

        if np.any(dists < min_dists):
            collision_steps += 1

    return collision_steps / max(len(check_steps), 1)


def _offroad_rate(
    sim_states: np.ndarray,
    map_extractor: MapFeatureExtractor,
) -> float:
    """Fraction of agent-steps that are off-road."""
    n_agents, n_steps, _ = sim_states.shape
    offroad_count = 0
    total_count = 0

    # Sample every 10th step and every agent for speed
    for step in range(0, n_steps, 10):
        for agent_idx in range(n_agents):
            x = float(sim_states[agent_idx, step, 0])
            y = float(sim_states[agent_idx, step, 1])
            dist = map_extractor.dist_to_road_edge(x, y)
            # Consider offroad if more than 5m from any road edge
            # (road edge = boundary, so being far from it means inside the road
            #  but being very close to it means near the edge)
            # Actually: dist_to_road_edge measures distance to the boundary.
            # On-road = small-to-moderate distance. Very far = also on road (center).
            # But if the nearest lane is far, we're likely offroad.
            nl = map_extractor.find_nearest_lane(x, y, 0.0)
            if nl is not None and nl.dist_to_center > 8.0:
                offroad_count += 1
            total_count += 1

    return offroad_count / max(total_count, 1)


def _smoothness_score(sim_states: np.ndarray) -> float:
    """Penalize jerky trajectories — reward smooth acceleration/steering."""
    # Compute heading changes
    headings = sim_states[:, :, 3]  # (n_agents, n_steps)
    heading_diffs = np.diff(headings, axis=1)
    # Wrap to [-pi, pi]
    heading_diffs = (heading_diffs + np.pi) % (2 * np.pi) - np.pi

    # Jerk = second derivative of heading
    heading_jerk = np.diff(heading_diffs, axis=1)
    mean_jerk = np.mean(np.abs(heading_jerk))

    # Score: low jerk = high score
    # Typical good jerk < 0.01, bad jerk > 0.1
    jerk_score = max(0, 1.0 - mean_jerk * 10.0)

    # Also check speed smoothness
    dx = np.diff(sim_states[:, :, 0], axis=1)
    dy = np.diff(sim_states[:, :, 1], axis=1)
    speeds = np.sqrt(dx**2 + dy**2) / 0.1
    accel = np.diff(speeds, axis=1) / 0.1
    mean_accel_change = np.mean(np.abs(np.diff(accel, axis=1))) if accel.size > 1 else 0
    accel_score = max(0, 1.0 - mean_accel_change * 0.05)

    return float(0.5 * jerk_score + 0.5 * accel_score)
