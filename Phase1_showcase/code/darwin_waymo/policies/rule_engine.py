"""Rule-based driving policy — lane following + IDM + traffic signals.

This is the foundation that Darwin builds on. The rule engine handles
the 80% of driving that is predictable. Evolution optimizes the 20%
that rules can't capture (interaction, yielding, edge cases).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from darwin_waymo.features.scenario_parser import (
    AgentState, AgentTrack, ParsedScenario,
    AGENT_TYPE_VEHICLE, AGENT_TYPE_PEDESTRIAN, AGENT_TYPE_CYCLIST,
)
from darwin_waymo.features.map_features import MapFeatureExtractor
from darwin_waymo.policies.kinematic_model import KinematicModel, KinematicState


@dataclass
class BehavioralParams:
    """Tunable parameters for the rule engine.

    In Darwin v2, these become FloatGenes that evolution optimizes.
    For now, they're set to reasonable defaults.
    """
    speed_factor: float = 0.9       # fraction of speed limit to target
    follow_time_gap: float = 1.5    # desired time gap to leader (seconds)
    min_follow_dist: float = 3.0    # minimum gap to leader (meters)
    lane_steer_gain: float = 1.5    # P-gain for lateral lane correction
    heading_steer_gain: float = 2.0 # P-gain for heading alignment
    stop_decel: float = -3.0        # comfortable deceleration for stopping
    yield_distance: float = 15.0    # distance to start yielding at signals
    noise_scale: float = 0.01       # action noise for diversity


class RuleEngine:
    """Rule-based driving policy for Waymo sim agents.

    Implements three behaviors blended by priority:
    1. Traffic signal compliance (highest priority)
    2. Car following / IDM (if leader exists)
    3. Lane following (default behavior)
    """

    def __init__(self, params: BehavioralParams = None):
        self.params = params or BehavioralParams()
        self.kinematic = KinematicModel()

    def compute_action(
        self,
        agent_state: AgentState,
        agent_type: int,
        map_extractor: MapFeatureExtractor,
        all_agents: Dict[int, AgentState],
        agent_id: int,
        timestep: int,
        scenario: ParsedScenario,
        rng: np.random.Generator = None,
    ) -> Tuple[float, float]:
        """Compute (acceleration, steering_rate) for an agent.

        Returns:
            (accel, steer_rate) — raw action before kinematic constraints.
        """
        p = self.params

        # --- 1. Lane following (base behavior) ---
        accel, steer = self._lane_following(agent_state, agent_type, map_extractor)

        # --- 2. Car following / IDM (override accel if leader exists) ---
        leader = self._find_leader(agent_state, agent_id, all_agents, agent_type)
        if leader is not None:
            idm_accel = self._idm_acceleration(agent_state, leader, agent_type)
            accel = min(accel, idm_accel)  # IDM overrides if it wants to slow down

        # --- 3. Traffic signal compliance (highest priority) ---
        signal_accel = self._traffic_signal_response(
            agent_state, map_extractor, timestep, scenario
        )
        if signal_accel is not None:
            accel = min(accel, signal_accel)  # signal override

        # --- 4. Collision avoidance (emergency) ---
        avoid_accel, avoid_steer = self._collision_avoidance(
            agent_state, agent_id, all_agents
        )
        if avoid_accel is not None:
            accel = min(accel, avoid_accel)
        if avoid_steer is not None:
            steer += avoid_steer * 0.3  # gentle avoidance

        # --- 5. Add noise for diversity ---
        if rng is not None:
            accel += rng.normal(0, p.noise_scale * 2.0)
            steer += rng.normal(0, p.noise_scale * 0.5)

        return accel, steer

    def _lane_following(self, agent: AgentState, agent_type: int,
                        map_ext: MapFeatureExtractor) -> Tuple[float, float]:
        """Follow the nearest lane centerline."""
        p = self.params

        # Find nearest lane
        nl = map_ext.find_nearest_lane(agent.x, agent.y, agent.heading)
        if nl is None:
            # No lane found — maintain current heading, gentle decel
            return -0.5, 0.0

        # Steering: correct lateral offset and heading error
        lateral_error = nl.dist_to_center
        heading_error = nl.angle_to_heading

        # Sign of lateral error: positive if agent is to the right of lane center
        # We need the cross-product to determine side
        steer = (-p.lane_steer_gain * lateral_error
                 - p.heading_steer_gain * heading_error)

        # Acceleration: match speed limit
        if agent_type == AGENT_TYPE_PEDESTRIAN:
            target_speed = min(1.5 * p.speed_factor, 3.0)
        elif agent_type == AGENT_TYPE_CYCLIST:
            target_speed = min(nl.speed_limit_mps * p.speed_factor, 10.0)
        else:
            target_speed = nl.speed_limit_mps * p.speed_factor

        speed_error = target_speed - agent.speed
        accel = np.clip(speed_error * 2.0, -4.0, 3.0)  # P-controller

        return accel, steer

    def _idm_acceleration(self, ego: AgentState, leader: AgentState,
                          agent_type: int) -> float:
        """Intelligent Driver Model — car-following acceleration.

        IDM produces smooth, realistic following behavior.
        Reference: Treiber et al. (2000)
        """
        p = self.params

        # Parameters
        a_max = 3.0 if agent_type == AGENT_TYPE_VEHICLE else 1.5
        b_comfort = 2.0  # comfortable deceleration
        v0 = 15.0  # desired speed (will be overridden by lane limit)

        # Gap to leader
        dx = leader.x - ego.x
        dy = leader.y - ego.y
        gap = np.sqrt(dx * dx + dy * dy) - ego.length  # net gap
        gap = max(gap, 0.1)

        # Approach speed
        dv = ego.speed - leader.speed

        # Desired gap
        s_star = (p.min_follow_dist
                  + ego.speed * p.follow_time_gap
                  + ego.speed * dv / (2 * np.sqrt(a_max * b_comfort)))
        s_star = max(s_star, p.min_follow_dist)

        # IDM acceleration
        accel = a_max * (1 - (ego.speed / max(v0, 0.1))**4 - (s_star / gap)**2)

        return float(np.clip(accel, -6.0, a_max))

    def _find_leader(self, ego: AgentState, ego_id: int,
                     all_agents: Dict[int, AgentState],
                     agent_type: int) -> Optional[AgentState]:
        """Find the agent directly ahead in the same lane."""
        cos_h = np.cos(ego.heading)
        sin_h = np.sin(ego.heading)

        best_leader = None
        best_dist = 50.0  # max look-ahead

        for aid, other in all_agents.items():
            if aid == ego_id:
                continue

            dx = other.x - ego.x
            dy = other.y - ego.y

            # Transform to ego frame
            lon = cos_h * dx + sin_h * dy   # longitudinal (ahead)
            lat = -sin_h * dx + cos_h * dy  # lateral

            # Must be ahead and in same lane (within ~3m lateral)
            if lon > 0 and abs(lat) < 3.0 and lon < best_dist:
                best_dist = lon
                best_leader = other

        return best_leader

    def _traffic_signal_response(self, agent: AgentState,
                                  map_ext: MapFeatureExtractor,
                                  timestep: int,
                                  scenario: ParsedScenario) -> Optional[float]:
        """Respond to traffic signals — stop at red/yellow."""
        signals = scenario.traffic_signals.get(timestep, [])
        if not signals:
            return None

        nl = map_ext.find_nearest_lane(agent.x, agent.y, agent.heading)
        if nl is None:
            return None

        for sig in signals:
            if sig.lane_id == nl.lane_id:
                # Signal states: typically 1=green, 4=red, 7=yellow (varies)
                # Red or yellow states that should stop
                RED_STATES = {4, 5, 7, 8}  # STOP, CAUTION variants
                if sig.state in RED_STATES:
                    dist_to_stop = nl.dist_to_lane_end
                    if dist_to_stop < self.params.yield_distance and agent.speed > 0.5:
                        # Decelerate to stop at lane end
                        decel = -(agent.speed ** 2) / (2 * max(dist_to_stop, 1.0))
                        return float(np.clip(decel, -6.0, 0.0))
                    elif dist_to_stop < 2.0:
                        # Very close to stop line — hard stop
                        return -4.0

        return None

    def _collision_avoidance(self, ego: AgentState, ego_id: int,
                              all_agents: Dict[int, AgentState]
                              ) -> Tuple[Optional[float], Optional[float]]:
        """Emergency collision avoidance — brake and steer if too close."""
        cos_h = np.cos(ego.heading)
        sin_h = np.sin(ego.heading)

        for aid, other in all_agents.items():
            if aid == ego_id:
                continue

            dx = other.x - ego.x
            dy = other.y - ego.y
            dist = np.sqrt(dx * dx + dy * dy)

            # Emergency zone: within 3m
            if dist < 3.0 and ego.speed > 0.5:
                # Brake hard
                accel = -5.0
                # Steer away slightly
                lon = cos_h * dx + sin_h * dy
                lat = -sin_h * dx + cos_h * dy
                if lon > 0:  # object is ahead
                    steer = -np.sign(lat) * 0.3 if abs(lat) < 2.0 else 0.0
                    return accel, steer

        return None, None
