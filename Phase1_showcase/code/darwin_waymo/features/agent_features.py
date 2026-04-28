"""Agent feature extraction — ego-centric features for driving policies.

Converts raw scenario state into a fixed-size feature vector that
the evolved driving policy consumes. All features are ego-centric
(relative to the agent) so the policy generalizes across scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from darwin_waymo.features.scenario_parser import (
    AgentState, AgentTrack, ParsedScenario, TrafficSignalState,
    AGENT_TYPE_VEHICLE, AGENT_TYPE_PEDESTRIAN, AGENT_TYPE_CYCLIST,
)
from darwin_waymo.features.map_features import MapFeatureExtractor


# Feature vector size
N_SELF_FEATURES = 6
N_LANE_FEATURES = 7
N_NEIGHBORS = 5
N_NEIGHBOR_FEATURES = 5
N_SAFETY_FEATURES = 4
N_SIGNAL_FEATURES = 2
TOTAL_FEATURES = (N_SELF_FEATURES + N_LANE_FEATURES +
                  N_NEIGHBORS * N_NEIGHBOR_FEATURES +
                  N_SAFETY_FEATURES + N_SIGNAL_FEATURES)  # = 44


@dataclass
class AgentFeatures:
    """Fixed-size feature vector for a single agent at a single timestep."""
    vector: np.ndarray   # shape: (TOTAL_FEATURES,) = (44,)

    # Indices for interpretability
    SELF_SLICE = slice(0, N_SELF_FEATURES)                              # 0:6
    LANE_SLICE = slice(N_SELF_FEATURES, N_SELF_FEATURES + N_LANE_FEATURES)  # 6:13
    NEIGHBOR_SLICE = slice(
        N_SELF_FEATURES + N_LANE_FEATURES,
        N_SELF_FEATURES + N_LANE_FEATURES + N_NEIGHBORS * N_NEIGHBOR_FEATURES,
    )  # 13:38
    SAFETY_SLICE = slice(
        N_SELF_FEATURES + N_LANE_FEATURES + N_NEIGHBORS * N_NEIGHBOR_FEATURES,
        N_SELF_FEATURES + N_LANE_FEATURES + N_NEIGHBORS * N_NEIGHBOR_FEATURES + N_SAFETY_FEATURES,
    )  # 38:42
    SIGNAL_SLICE = slice(TOTAL_FEATURES - N_SIGNAL_FEATURES, TOTAL_FEATURES)  # 42:44

    @property
    def speed(self) -> float:
        return self.vector[0]

    @property
    def dist_to_lane_center(self) -> float:
        return self.vector[6]

    @property
    def time_to_collision(self) -> float:
        return self.vector[39]


class AgentFeatureExtractor:
    """Extracts ego-centric features for all agents in a scenario."""

    def __init__(self, scenario: ParsedScenario):
        self.scenario = scenario
        self.map_extractor = MapFeatureExtractor(scenario)

    def extract(self, agent_id: int, timestep: int,
                all_agent_states: dict = None) -> Optional[AgentFeatures]:
        """Extract features for a single agent at a single timestep.

        Args:
            agent_id: The agent to extract features for.
            timestep: Current timestep index.
            all_agent_states: Optional dict of {agent_id: AgentState} for current
                              timestep. If None, reads from scenario ground truth.

        Returns:
            AgentFeatures or None if agent is invalid at this timestep.
        """
        # Get agent state
        if all_agent_states and agent_id in all_agent_states:
            ego = all_agent_states[agent_id]
        else:
            track = self.scenario.agents.get(agent_id)
            if track is None or not track.valid[timestep]:
                return None
            ego = track.state_at(timestep)

        if ego is None:
            return None

        features = np.zeros(TOTAL_FEATURES, dtype=np.float32)

        # === 1. Self features (6) ===
        accel = 0.0
        heading_rate = 0.0
        track = self.scenario.agents.get(agent_id)
        if track and timestep > 0 and track.valid[timestep - 1]:
            prev = track.state_at(timestep - 1)
            accel = (ego.speed - prev.speed) * 10.0  # dt = 0.1s
            heading_rate = self._wrap_angle(ego.heading - prev.heading) * 10.0

        agent_type_norm = {
            AGENT_TYPE_VEHICLE: 0.0,
            AGENT_TYPE_PEDESTRIAN: 0.5,
            AGENT_TYPE_CYCLIST: 1.0,
        }.get(track.agent_type if track else AGENT_TYPE_VEHICLE, 0.0)

        features[0] = ego.speed
        features[1] = accel
        features[2] = heading_rate
        features[3] = agent_type_norm
        features[4] = ego.length
        features[5] = ego.width

        # === 2. Lane features (7) ===
        nl = self.map_extractor.find_nearest_lane(ego.x, ego.y, ego.heading)
        if nl is not None:
            features[6] = np.clip(nl.dist_to_center, -10, 10)
            features[7] = np.clip(nl.angle_to_heading, -np.pi, np.pi)
            features[8] = np.clip(nl.curvature, -1, 1)
            features[9] = np.clip(nl.dist_to_lane_end / 50.0, 0, 1)  # normalized
            features[10] = nl.speed_limit_mps
            features[11] = 1.0 if self.map_extractor.is_in_intersection(ego.x, ego.y) else 0.0
            features[12] = nl.lane_type / 3.0  # normalized

        # === 3. Neighbor features (5 neighbors × 5 features = 25) ===
        neighbors = self._get_neighbors(ego, agent_id, timestep, all_agent_states)
        for i, (rel_dx, rel_dy, rel_speed, rel_heading, n_type) in enumerate(neighbors[:N_NEIGHBORS]):
            base = N_SELF_FEATURES + N_LANE_FEATURES + i * N_NEIGHBOR_FEATURES
            features[base + 0] = rel_dx
            features[base + 1] = rel_dy
            features[base + 2] = rel_speed
            features[base + 3] = rel_heading
            features[base + 4] = n_type

        # === 4. Safety features (4) ===
        safety_base = N_SELF_FEATURES + N_LANE_FEATURES + N_NEIGHBORS * N_NEIGHBOR_FEATURES
        features[safety_base + 0] = np.clip(
            self.map_extractor.dist_to_road_edge(ego.x, ego.y) / 20.0, 0, 1
        )
        features[safety_base + 1] = np.clip(
            self._time_to_collision(ego, neighbors) / 10.0, 0, 1
        )
        features[safety_base + 2] = np.clip(
            self._dist_to_nearest(neighbors) / 20.0, 0, 1
        )
        features[safety_base + 3] = features[11]  # is_in_intersection (copy)

        # === 5. Traffic signal features (2) ===
        signal_state, signal_dist = self._get_traffic_signal(ego, timestep)
        features[TOTAL_FEATURES - 2] = signal_state / 8.0  # normalized enum
        features[TOTAL_FEATURES - 1] = np.clip(signal_dist / 30.0, 0, 1)

        return AgentFeatures(vector=features)

    def _get_neighbors(self, ego: AgentState, ego_id: int, timestep: int,
                       all_agent_states: dict = None) -> List[Tuple]:
        """Get K nearest neighbors in ego-centric frame.
        Returns list of (rel_dx, rel_dy, rel_speed, rel_heading, agent_type_norm)."""
        neighbors = []
        cos_h = np.cos(-ego.heading)
        sin_h = np.sin(-ego.heading)

        for aid, track in self.scenario.agents.items():
            if aid == ego_id:
                continue

            if all_agent_states and aid in all_agent_states:
                other = all_agent_states[aid]
            elif track.valid[timestep]:
                other = track.state_at(timestep)
            else:
                continue

            if other is None:
                continue

            # Transform to ego frame
            dx = other.x - ego.x
            dy = other.y - ego.y
            dist = np.sqrt(dx * dx + dy * dy)
            if dist > 50.0:  # ignore agents > 50m away
                continue

            # Rotate to ego heading frame
            rel_dx = cos_h * dx - sin_h * dy
            rel_dy = sin_h * dx + cos_h * dy
            rel_speed = other.speed - ego.speed
            rel_heading = self._wrap_angle(other.heading - ego.heading)

            n_type = {
                AGENT_TYPE_VEHICLE: 0.0,
                AGENT_TYPE_PEDESTRIAN: 0.5,
                AGENT_TYPE_CYCLIST: 1.0,
            }.get(track.agent_type, 0.0)

            neighbors.append((rel_dx, rel_dy, rel_speed, rel_heading, n_type, dist))

        # Sort by distance, return top K without the distance
        neighbors.sort(key=lambda n: n[5])
        return [(n[0], n[1], n[2], n[3], n[4]) for n in neighbors[:N_NEIGHBORS]]

    def _time_to_collision(self, ego: AgentState, neighbors: List[Tuple]) -> float:
        """Estimate time to collision with nearest agent ahead."""
        if not neighbors:
            return 10.0  # no collision risk

        for rel_dx, rel_dy, rel_speed, _, _ in neighbors:
            # Only consider agents ahead (positive rel_dx in ego frame)
            if rel_dx > 0 and abs(rel_dy) < 3.0:  # within lane width
                closing_speed = -rel_speed  # positive if approaching
                if closing_speed > 0.1:
                    dist = np.sqrt(rel_dx ** 2 + rel_dy ** 2)
                    ttc = dist / closing_speed
                    return min(ttc, 10.0)

        return 10.0

    def _dist_to_nearest(self, neighbors: List[Tuple]) -> float:
        """Distance to nearest neighbor."""
        if not neighbors:
            return 50.0
        dx, dy = neighbors[0][0], neighbors[0][1]
        return np.sqrt(dx * dx + dy * dy)

    def _get_traffic_signal(self, ego: AgentState, timestep: int
                            ) -> Tuple[float, float]:
        """Get traffic signal state relevant to agent. Returns (state, distance)."""
        signals = self.scenario.traffic_signals.get(timestep, [])
        if not signals:
            return 0.0, 30.0  # no signal, max distance

        # Find nearest lane's signal
        nl = self.map_extractor.find_nearest_lane(ego.x, ego.y, ego.heading)
        if nl is None:
            return 0.0, 30.0

        for sig in signals:
            if sig.lane_id == nl.lane_id:
                # Signal applies to our lane
                return float(sig.state), nl.dist_to_lane_end

        return 0.0, 30.0

    @staticmethod
    def _wrap_angle(angle: float) -> float:
        return (angle + np.pi) % (2 * np.pi) - np.pi
