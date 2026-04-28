"""Rollout engine — runs closed-loop simulation and packages for WOSAC.

This is the bridge between Darwin policies and the Waymo evaluation.
Runs 32 rollouts per scenario, each with a different policy or noise seed.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from waymo_open_dataset.protos import sim_agents_submission_pb2
from waymo_open_dataset.utils.sim_agents import submission_specs

from darwin_waymo.features.scenario_parser import (
    ParsedScenario, AgentState, AGENT_TYPE_VEHICLE,
)
from darwin_waymo.features.map_features import MapFeatureExtractor
from darwin_waymo.policies.kinematic_model import KinematicModel, KinematicState
from darwin_waymo.policies.rule_engine import RuleEngine, BehavioralParams


N_ROLLOUTS = 32
N_SIM_STEPS = 80


class RolloutEngine:
    """Runs closed-loop simulation for a scenario.

    For each rollout:
    1. Initialize all sim agents at their last observed state
    2. Step forward 80 times at 10Hz
    3. At each step: extract features → policy → kinematic model → new state
    4. Package results into WOSAC submission format
    """

    def __init__(self, n_rollouts: int = N_ROLLOUTS):
        self.n_rollouts = n_rollouts
        self.kinematic = KinematicModel()

    def run_scenario(
        self,
        scenario: ParsedScenario,
        policies: List[RuleEngine] = None,
        seed: int = 42,
    ) -> np.ndarray:
        """Run all rollouts for a scenario.

        Args:
            scenario: Parsed WOSAC scenario.
            policies: List of policies (one per rollout), or None for default.
            seed: Random seed for noise diversity.

        Returns:
            simulated_states: shape (n_rollouts, n_agents, n_sim_steps, 4)
                              where 4 = (x, y, z, heading)
        """
        map_ext = MapFeatureExtractor(scenario)
        t0 = scenario.current_time_index  # last observed timestep

        # Get initial states for all sim agents
        sim_ids = scenario.sim_agent_ids
        n_agents = len(sim_ids)

        # Initialize: get last valid state for each sim agent
        init_states = {}
        agent_types = {}
        for aid in sim_ids:
            track = scenario.agents[aid]
            state = track.last_valid_state(t0)
            if state is not None:
                init_states[aid] = KinematicState.from_agent_state(state)
                agent_types[aid] = track.agent_type
            else:
                # Fallback: zero state
                init_states[aid] = KinematicState(0, 0, 0, 0, 0, 0, 0)
                agent_types[aid] = AGENT_TYPE_VEHICLE

        # Create default policies if not provided
        if policies is None:
            policies = self._create_diverse_policies(self.n_rollouts, seed)

        # Run rollouts
        all_states = np.zeros(
            (self.n_rollouts, n_agents, N_SIM_STEPS, 4),
            dtype=np.float32,
        )

        for r in range(self.n_rollouts):
            policy = policies[r % len(policies)]
            rng = np.random.default_rng(seed + r)

            # Copy initial states
            current = {aid: KinematicState(
                s.x, s.y, s.z, s.heading, s.speed, s.vx, s.vy
            ) for aid, s in init_states.items()}

            for step in range(N_SIM_STEPS):
                # Build current agent states dict for feature extraction
                current_agent_states = {}
                for aid, ks in current.items():
                    current_agent_states[aid] = AgentState(
                        x=ks.x, y=ks.y, z=ks.z, heading=ks.heading,
                        vx=ks.vx, vy=ks.vy, speed=ks.speed,
                        length=scenario.agents[aid].states[t0, 7],
                        width=scenario.agents[aid].states[t0, 8],
                        height=scenario.agents[aid].states[t0, 9],
                        valid=True,
                    )

                # Step each agent
                for idx, aid in enumerate(sim_ids):
                    agent_state = current_agent_states[aid]
                    at = agent_types[aid]

                    # Compute action from policy
                    accel, steer = policy.compute_action(
                        agent_state=agent_state,
                        agent_type=at,
                        map_extractor=map_ext,
                        all_agents=current_agent_states,
                        agent_id=aid,
                        timestep=t0 + step + 1,
                        scenario=scenario,
                        rng=rng,
                    )

                    # Apply kinematic model
                    new_ks = self.kinematic.step(current[aid], accel, steer, at)
                    current[aid] = new_ks

                    # Record state
                    all_states[r, idx, step] = new_ks.to_array()

        return all_states

    def _create_diverse_policies(self, n: int, seed: int) -> List[RuleEngine]:
        """Create n diverse rule-based policies by varying behavioral parameters."""
        rng = np.random.default_rng(seed)
        policies = []

        for i in range(n):
            params = BehavioralParams(
                speed_factor=rng.uniform(0.7, 1.1),
                follow_time_gap=rng.uniform(1.0, 2.5),
                min_follow_dist=rng.uniform(2.0, 5.0),
                lane_steer_gain=rng.uniform(1.0, 2.5),
                heading_steer_gain=rng.uniform(1.5, 3.0),
                stop_decel=rng.uniform(-4.0, -2.0),
                yield_distance=rng.uniform(10.0, 25.0),
                noise_scale=rng.uniform(0.005, 0.03),
            )
            policies.append(RuleEngine(params))

        return policies

    def package_submission(
        self,
        scenario: ParsedScenario,
        simulated_states: np.ndarray,
    ) -> sim_agents_submission_pb2.ScenarioRollouts:
        """Package simulated states into WOSAC submission format.

        Args:
            scenario: The parsed scenario.
            simulated_states: shape (n_rollouts, n_agents, n_sim_steps, 4)

        Returns:
            ScenarioRollouts protobuf ready for submission.
        """
        sim_ids = scenario.sim_agent_ids
        joint_scenes = []

        for r in range(simulated_states.shape[0]):
            trajectories = []
            for idx, aid in enumerate(sim_ids):
                states = simulated_states[r, idx]  # (80, 4)
                trajectories.append(
                    sim_agents_submission_pb2.SimulatedTrajectory(
                        center_x=states[:, 0].tolist(),
                        center_y=states[:, 1].tolist(),
                        center_z=states[:, 2].tolist(),
                        heading=states[:, 3].tolist(),
                        object_id=aid,
                    )
                )
            joint_scenes.append(
                sim_agents_submission_pb2.JointScene(
                    simulated_trajectories=trajectories,
                )
            )

        return sim_agents_submission_pb2.ScenarioRollouts(
            joint_scenes=joint_scenes,
            scenario_id=scenario.scenario_id,
        )
