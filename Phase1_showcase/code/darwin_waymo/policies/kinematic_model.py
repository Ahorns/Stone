"""Kinematic vehicle model — enforces physical constraints on actions.

Uses a simple point-mass model with heading. This ensures all
simulated trajectories are physically plausible regardless of
what the policy outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class KinematicState:
    """Mutable agent state for simulation."""
    x: float
    y: float
    z: float
    heading: float
    speed: float
    vx: float
    vy: float

    def to_array(self) -> np.ndarray:
        """Return (x, y, z, heading) for submission."""
        return np.array([self.x, self.y, self.z, self.heading], dtype=np.float32)

    @staticmethod
    def from_agent_state(agent_state) -> "KinematicState":
        return KinematicState(
            x=agent_state.x, y=agent_state.y, z=agent_state.z,
            heading=agent_state.heading, speed=agent_state.speed,
            vx=agent_state.vx, vy=agent_state.vy,
        )


class KinematicModel:
    """Point-mass kinematic model with heading and speed constraints.

    Converts (acceleration, steering_rate) commands into next state,
    enforcing physical limits.
    """

    # Physical limits
    MAX_ACCEL = 4.0        # m/s^2 (comfortable acceleration)
    MAX_DECEL = -6.0       # m/s^2 (hard braking)
    MAX_SPEED = 35.0       # m/s (~126 km/h)
    MAX_STEER_RATE = 0.8   # rad/s (max heading change rate)
    DT = 0.1               # 10 Hz

    # Pedestrian/cyclist limits
    PED_MAX_SPEED = 3.0    # m/s (~10.8 km/h)
    PED_MAX_ACCEL = 2.0    # m/s^2
    CYCLIST_MAX_SPEED = 12.0  # m/s (~43 km/h)

    def step(self, state: KinematicState, accel: float, steer_rate: float,
             agent_type: int = 1) -> KinematicState:
        """Advance state by one timestep (0.1s).

        Args:
            state: Current kinematic state.
            accel: Desired acceleration (m/s^2), positive = speed up.
            steer_rate: Desired heading change rate (rad/s), positive = left.
            agent_type: 1=vehicle, 2=pedestrian, 3=cyclist.

        Returns:
            New KinematicState after applying constrained action.
        """
        # Select limits by agent type
        if agent_type == 2:  # pedestrian
            max_speed = self.PED_MAX_SPEED
            max_accel = self.PED_MAX_ACCEL
            max_decel = -self.PED_MAX_ACCEL
        elif agent_type == 3:  # cyclist
            max_speed = self.CYCLIST_MAX_SPEED
            max_accel = self.MAX_ACCEL
            max_decel = self.MAX_DECEL
        else:  # vehicle
            max_speed = self.MAX_SPEED
            max_accel = self.MAX_ACCEL
            max_decel = self.MAX_DECEL

        # Clip actions to physical limits
        accel = np.clip(accel, max_decel, max_accel)
        steer_rate = np.clip(steer_rate, -self.MAX_STEER_RATE, self.MAX_STEER_RATE)

        # Update speed
        new_speed = state.speed + accel * self.DT
        new_speed = np.clip(new_speed, 0.0, max_speed)

        # Update heading
        new_heading = state.heading + steer_rate * self.DT
        # Wrap to [-pi, pi]
        new_heading = (new_heading + np.pi) % (2 * np.pi) - np.pi

        # Update position using new heading and speed
        new_vx = new_speed * np.cos(new_heading)
        new_vy = new_speed * np.sin(new_heading)
        new_x = state.x + new_vx * self.DT
        new_y = state.y + new_vy * self.DT

        return KinematicState(
            x=new_x, y=new_y, z=state.z,
            heading=new_heading, speed=new_speed,
            vx=new_vx, vy=new_vy,
        )
