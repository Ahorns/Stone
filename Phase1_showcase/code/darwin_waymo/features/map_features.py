"""Map feature extraction — lane finding, road edges, intersections.

Converts raw map geometry into agent-relative features that
the driving policy can consume.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from darwin_waymo.features.scenario_parser import (
    LaneInfo, RoadEdgeInfo, ParsedScenario,
)


@dataclass
class NearestLane:
    """Result of finding the nearest lane to an agent."""
    lane_id: int
    dist_to_center: float       # lateral distance to lane centerline (m)
    angle_to_heading: float     # angle between agent heading and lane heading (rad)
    curvature: float            # local lane curvature (1/m)
    dist_to_lane_end: float     # distance along lane to its end (m)
    speed_limit_mps: float      # speed limit in m/s
    lane_type: int              # 0=undefined, 1=freeway, 2=surface, 3=bike
    nearest_point: np.ndarray   # closest point on lane centerline


class MapFeatureExtractor:
    """Extracts map-relative features for agents."""

    def __init__(self, scenario: ParsedScenario):
        self.scenario = scenario
        self.lanes = scenario.lanes
        self.road_edges = scenario.road_edges

        # Pre-compute all lane polyline arrays for fast lookup
        self._lane_points = {}  # lane_id -> (N, 2) array
        self._lane_headings = {}  # lane_id -> (N-1,) heading per segment
        self._lane_cumlen = {}  # lane_id -> (N,) cumulative length
        for lid, lane in self.lanes.items():
            pts = lane.polyline[:, :2]  # (N, 2) — x, y
            self._lane_points[lid] = pts
            if len(pts) > 1:
                diffs = np.diff(pts, axis=0)
                self._lane_headings[lid] = np.arctan2(diffs[:, 1], diffs[:, 0])
                seg_lens = np.linalg.norm(diffs, axis=1)
                self._lane_cumlen[lid] = np.concatenate([[0], np.cumsum(seg_lens)])
            else:
                self._lane_headings[lid] = np.array([0.0])
                self._lane_cumlen[lid] = np.array([0.0])

        # Build spatial index: grid cells -> lane IDs with points in that cell
        self._grid_size = 20.0  # meters per cell
        self._lane_grid = {}  # (gx, gy) -> set of lane_ids
        for lid, pts in self._lane_points.items():
            for pt in pts:
                gx = int(pt[0] // self._grid_size)
                gy = int(pt[1] // self._grid_size)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        key = (gx + dx, gy + dy)
                        if key not in self._lane_grid:
                            self._lane_grid[key] = set()
                        self._lane_grid[key].add(lid)

        # Pre-compute road edge points for fast distance queries
        self._edge_points_list = []
        for edge in self.road_edges:
            if len(edge.polyline) > 0:
                self._edge_points_list.append(edge.polyline[:, :2])
        # Concatenate all edge points for vectorized distance
        if self._edge_points_list:
            self._all_edge_points = np.vstack(self._edge_points_list)
        else:
            self._all_edge_points = np.zeros((1, 2), dtype=np.float32)

    def find_nearest_lane(self, x: float, y: float, heading: float) -> Optional[NearestLane]:
        """Find the nearest lane to a position and return lane-relative features."""
        pos = np.array([x, y], dtype=np.float32)
        best_dist = float('inf')
        best_lane_id = None
        best_seg_idx = 0
        best_proj_point = pos

        # Use spatial grid to only check nearby lanes
        gx = int(x // self._grid_size)
        gy = int(y // self._grid_size)
        candidate_lanes = self._lane_grid.get((gx, gy), set())

        # Fallback: if grid cell is empty, check all lanes
        if not candidate_lanes:
            candidate_lanes = self._lane_points.keys()

        for lid in candidate_lanes:
            pts = self._lane_points[lid]
            if len(pts) < 2:
                continue
            dist, seg_idx, proj = self._point_to_polyline(pos, pts)
            if dist < best_dist:
                best_dist = dist
                best_lane_id = lid
                best_seg_idx = seg_idx
                best_proj_point = proj

        if best_lane_id is None:
            return None

        lane = self.lanes[best_lane_id]
        headings = self._lane_headings[best_lane_id]
        cumlen = self._lane_cumlen[best_lane_id]

        # Lane heading at the nearest segment
        seg_heading = headings[min(best_seg_idx, len(headings) - 1)]
        angle_diff = self._wrap_angle(heading - seg_heading)

        # Curvature: heading change per unit distance
        curvature = 0.0
        if len(headings) > 1 and best_seg_idx < len(headings) - 1:
            dh = self._wrap_angle(headings[best_seg_idx + 1] - headings[best_seg_idx])
            ds = cumlen[best_seg_idx + 2] - cumlen[best_seg_idx] if best_seg_idx + 2 < len(cumlen) else 1.0
            curvature = dh / max(ds, 0.1)

        # Distance to lane end
        total_len = cumlen[-1]
        pos_along = cumlen[best_seg_idx] + np.linalg.norm(best_proj_point - self._lane_points[best_lane_id][best_seg_idx])
        dist_to_end = max(0, total_len - pos_along)

        return NearestLane(
            lane_id=best_lane_id,
            dist_to_center=best_dist,
            angle_to_heading=angle_diff,
            curvature=curvature,
            dist_to_lane_end=dist_to_end,
            speed_limit_mps=lane.speed_limit_mph * 0.44704,  # mph -> m/s
            lane_type=lane.lane_type,
            nearest_point=best_proj_point,
        )

    def dist_to_road_edge(self, x: float, y: float) -> float:
        """Distance from position to nearest road edge."""
        pos = np.array([x, y], dtype=np.float32)
        dists = np.linalg.norm(self._all_edge_points - pos, axis=1)
        return float(np.min(dists)) if len(dists) > 0 else 50.0

    def is_in_intersection(self, x: float, y: float) -> bool:
        """Check if position is in an intersection (lane endpoints converge)."""
        pos = np.array([x, y])
        # Heuristic: if multiple lanes have endpoints within 5m, it's an intersection
        nearby_endpoints = 0
        for lid, pts in self._lane_points.items():
            if len(pts) < 2:
                continue
            # Check distance to lane start and end
            if np.linalg.norm(pts[0] - pos) < 8.0 or np.linalg.norm(pts[-1] - pos) < 8.0:
                nearby_endpoints += 1
        return nearby_endpoints >= 3

    def get_lane_centerline_ahead(self, x: float, y: float, heading: float,
                                   max_dist: float = 30.0) -> np.ndarray:
        """Get lane centerline points ahead of the agent for path planning.
        Returns (N, 2) array of xy points along the lane ahead."""
        nl = self.find_nearest_lane(x, y, heading)
        if nl is None:
            # Return straight-ahead default
            dx = np.cos(heading)
            dy = np.sin(heading)
            return np.array([[x + dx * d, y + dy * d] for d in range(1, int(max_dist) + 1)],
                            dtype=np.float32)

        pts = self._lane_points[nl.lane_id]
        cumlen = self._lane_cumlen[nl.lane_id]

        # Find the segment we're on
        pos = np.array([x, y])
        _, seg_idx, _ = self._point_to_polyline(pos, pts)

        # Collect points ahead
        ahead = []
        cum = 0.0
        for i in range(seg_idx + 1, len(pts)):
            ahead.append(pts[i])
            if i > seg_idx + 1:
                cum += np.linalg.norm(pts[i] - pts[i - 1])
            if cum > max_dist:
                break

        # If lane ends, try to follow exit lanes
        if cum < max_dist and nl.lane_id in self.lanes:
            lane = self.lanes[nl.lane_id]
            for exit_id in lane.exit_lanes[:1]:  # follow first exit
                if exit_id in self._lane_points:
                    exit_pts = self._lane_points[exit_id]
                    for pt in exit_pts:
                        ahead.append(pt)
                        cum += np.linalg.norm(pt - ahead[-2]) if len(ahead) > 1 else 0
                        if cum > max_dist:
                            break

        if len(ahead) == 0:
            dx = np.cos(heading)
            dy = np.sin(heading)
            return np.array([[x + dx * d, y + dy * d] for d in range(1, 6)],
                            dtype=np.float32)

        return np.array(ahead, dtype=np.float32)

    @staticmethod
    def _point_to_polyline(point: np.ndarray, polyline: np.ndarray
                            ) -> Tuple[float, int, np.ndarray]:
        """Find closest point on a polyline to a given point.
        Returns (distance, segment_index, projected_point)."""
        # Vectorized segment projection
        p1 = polyline[:-1]  # (N-1, 2)
        p2 = polyline[1:]   # (N-1, 2)
        d = p2 - p1
        seg_len_sq = np.sum(d * d, axis=1)  # (N-1,)
        seg_len_sq = np.maximum(seg_len_sq, 1e-8)

        t = np.sum((point - p1) * d, axis=1) / seg_len_sq
        t = np.clip(t, 0.0, 1.0)

        proj = p1 + t[:, np.newaxis] * d  # (N-1, 2)
        dists = np.linalg.norm(proj - point, axis=1)  # (N-1,)

        best_idx = np.argmin(dists)
        return float(dists[best_idx]), int(best_idx), proj[best_idx]

    @staticmethod
    def _wrap_angle(angle: float) -> float:
        """Wrap angle to [-pi, pi]."""
        return (angle + np.pi) % (2 * np.pi) - np.pi
