"""Parse Waymo scenario protobufs into structured numpy arrays.

Converts the raw protobuf format into clean numpy arrays that
the Darwin policy and feature extractor can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import tensorflow as tf

from waymo_open_dataset.protos import scenario_pb2
from waymo_open_dataset.utils.sim_agents import submission_specs


# Agent type constants (matching Waymo proto enum)
AGENT_TYPE_VEHICLE = 1
AGENT_TYPE_PEDESTRIAN = 2
AGENT_TYPE_CYCLIST = 3


@dataclass
class AgentState:
    """State of a single agent at a single timestep."""
    x: float
    y: float
    z: float
    heading: float  # radians, counter-clockwise from X-axis
    vx: float
    vy: float
    speed: float
    length: float
    width: float
    height: float
    valid: bool

    @property
    def position(self) -> np.ndarray:
        return np.array([self.x, self.y], dtype=np.float32)


@dataclass
class AgentTrack:
    """Full trajectory of a single agent across all timesteps."""
    agent_id: int
    agent_type: int  # 1=vehicle, 2=pedestrian, 3=cyclist
    states: np.ndarray  # shape: (n_steps, 10) = [x,y,z,heading,vx,vy,speed,length,width,height]
    valid: np.ndarray   # shape: (n_steps,) bool

    @property
    def is_vehicle(self) -> bool:
        return self.agent_type == AGENT_TYPE_VEHICLE

    @property
    def is_pedestrian(self) -> bool:
        return self.agent_type == AGENT_TYPE_PEDESTRIAN

    @property
    def is_cyclist(self) -> bool:
        return self.agent_type == AGENT_TYPE_CYCLIST

    def state_at(self, t: int) -> Optional[AgentState]:
        if not self.valid[t]:
            return None
        s = self.states[t]
        return AgentState(
            x=s[0], y=s[1], z=s[2], heading=s[3],
            vx=s[4], vy=s[5], speed=s[6],
            length=s[7], width=s[8], height=s[9],
            valid=True,
        )

    def last_valid_state(self, up_to: int) -> Optional[AgentState]:
        for t in range(up_to, -1, -1):
            if self.valid[t]:
                return self.state_at(t)
        return None


@dataclass
class LaneInfo:
    """Parsed lane centerline with metadata."""
    lane_id: int
    polyline: np.ndarray     # shape: (N, 3) — x, y, z points
    speed_limit_mph: float
    lane_type: int           # 0=undefined, 1=freeway, 2=surface, 3=bike
    entry_lanes: List[int]
    exit_lanes: List[int]


@dataclass
class RoadEdgeInfo:
    """Parsed road edge."""
    edge_id: int
    polyline: np.ndarray  # shape: (N, 3)
    edge_type: int        # 1=boundary, 2=median


@dataclass
class TrafficSignalState:
    """Traffic signal state at a given timestep."""
    lane_id: int
    state: int  # From proto enum


@dataclass
class ParsedScenario:
    """A fully parsed Waymo scenario ready for Darwin."""
    scenario_id: str
    n_timesteps: int
    current_time_index: int  # observation cutoff (t=0 for simulation)
    timestamps: np.ndarray   # shape: (n_timesteps,)

    # Agents
    agents: Dict[int, AgentTrack]  # agent_id -> AgentTrack
    sim_agent_ids: List[int]       # IDs of agents to simulate
    eval_agent_ids: List[int]      # IDs of agents to evaluate
    sdc_track_index: int           # index of the autonomous vehicle

    # Map
    lanes: Dict[int, LaneInfo]
    road_edges: List[RoadEdgeInfo]
    stop_signs: List[Tuple[np.ndarray, List[int]]]  # (position, lane_ids)
    crosswalks: List[np.ndarray]   # polygons

    # Traffic signals per timestep
    traffic_signals: Dict[int, List[TrafficSignalState]]  # timestep -> signals

    @property
    def n_sim_agents(self) -> int:
        return len(self.sim_agent_ids)

    @property
    def history_steps(self) -> int:
        return self.current_time_index + 1

    @property
    def future_steps(self) -> int:
        return self.n_timesteps - self.current_time_index - 1

    def get_agent(self, agent_id: int) -> Optional[AgentTrack]:
        return self.agents.get(agent_id)

    def get_agents_at(self, t: int) -> List[Tuple[int, AgentState]]:
        """Get all valid agents at timestep t."""
        result = []
        for aid, track in self.agents.items():
            if track.valid[t]:
                result.append((aid, track.state_at(t)))
        return result


class ScenarioParser:
    """Parses raw Waymo protobuf scenarios into structured data."""

    def parse(self, scenario: scenario_pb2.Scenario) -> ParsedScenario:
        """Parse a single scenario protobuf into ParsedScenario."""
        n_steps = len(scenario.timestamps_seconds)
        current_t = scenario.current_time_index

        # Parse agents
        agents = {}
        for track in scenario.tracks:
            states = np.zeros((n_steps, 10), dtype=np.float32)
            valid = np.zeros(n_steps, dtype=bool)

            for t, s in enumerate(track.states):
                if s.valid:
                    speed = np.sqrt(s.velocity_x**2 + s.velocity_y**2)
                    states[t] = [
                        s.center_x, s.center_y, s.center_z, s.heading,
                        s.velocity_x, s.velocity_y, speed,
                        s.length, s.width, s.height,
                    ]
                    valid[t] = True

            agents[track.id] = AgentTrack(
                agent_id=track.id,
                agent_type=track.object_type,
                states=states,
                valid=valid,
            )

        # Sim agent IDs
        challenge_type = submission_specs.ChallengeType.SIM_AGENTS
        sim_ids = list(submission_specs.get_sim_agent_ids(scenario, challenge_type))
        eval_ids = list(submission_specs.get_evaluation_sim_agent_ids(scenario, challenge_type))

        # Parse map
        lanes, road_edges, stop_signs, crosswalks = self._parse_map(scenario)

        # Parse traffic signals
        traffic_signals = self._parse_traffic_signals(scenario)

        return ParsedScenario(
            scenario_id=scenario.scenario_id,
            n_timesteps=n_steps,
            current_time_index=current_t,
            timestamps=np.array(scenario.timestamps_seconds, dtype=np.float64),
            agents=agents,
            sim_agent_ids=sim_ids,
            eval_agent_ids=eval_ids,
            sdc_track_index=scenario.sdc_track_index,
            lanes=lanes,
            road_edges=road_edges,
            stop_signs=stop_signs,
            crosswalks=crosswalks,
            traffic_signals=traffic_signals,
        )

    def _parse_map(self, scenario) -> Tuple:
        lanes = {}
        road_edges = []
        stop_signs = []
        crosswalks = []

        for mf in scenario.map_features:
            fid = mf.id

            if mf.HasField('lane'):
                lane = mf.lane
                polyline = np.array(
                    [[p.x, p.y, p.z] for p in lane.polyline],
                    dtype=np.float32,
                )
                lanes[fid] = LaneInfo(
                    lane_id=fid,
                    polyline=polyline,
                    speed_limit_mph=lane.speed_limit_mph if lane.speed_limit_mph > 0 else 25.0,
                    lane_type=lane.type,
                    entry_lanes=list(lane.entry_lanes),
                    exit_lanes=list(lane.exit_lanes),
                )

            elif mf.HasField('road_edge'):
                edge = mf.road_edge
                polyline = np.array(
                    [[p.x, p.y, p.z] for p in edge.polyline],
                    dtype=np.float32,
                )
                road_edges.append(RoadEdgeInfo(
                    edge_id=fid,
                    polyline=polyline,
                    edge_type=edge.type,
                ))

            elif mf.HasField('stop_sign'):
                ss = mf.stop_sign
                pos = np.array([ss.position.x, ss.position.y, ss.position.z],
                               dtype=np.float32)
                stop_signs.append((pos, list(ss.lane)))

            elif mf.HasField('crosswalk'):
                cw = mf.crosswalk
                polygon = np.array(
                    [[p.x, p.y, p.z] for p in cw.polygon],
                    dtype=np.float32,
                )
                crosswalks.append(polygon)

        return lanes, road_edges, stop_signs, crosswalks

    def _parse_traffic_signals(self, scenario) -> Dict[int, List[TrafficSignalState]]:
        signals = {}
        for t, dms in enumerate(scenario.dynamic_map_states):
            step_signals = []
            for ls in dms.lane_states:
                step_signals.append(TrafficSignalState(
                    lane_id=ls.lane,
                    state=ls.state,
                ))
            if step_signals:
                signals[t] = step_signals
        return signals

    def load_from_tfrecord(self, path: str, max_scenarios: int = None):
        """Load scenarios from a TFRecord file. Yields ParsedScenario."""
        dataset = tf.data.TFRecordDataset([path])
        count = 0
        for raw in dataset.as_numpy_iterator():
            scenario = scenario_pb2.Scenario.FromString(raw)
            yield self.parse(scenario)
            count += 1
            if max_scenarios and count >= max_scenarios:
                break
