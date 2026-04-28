"""
Waymo Sim Agents Tutorial — adapted from tutorial_sim_agents.ipynb
Runs on server with 1 downloaded validation shard.
"""
import os
import sys
import tarfile
from pathlib import Path

# Make darwin_waymo importable when run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import tqdm

from waymo_open_dataset.protos import scenario_pb2
from waymo_open_dataset.protos import sim_agents_submission_pb2
from waymo_open_dataset.utils import trajectory_utils
from waymo_open_dataset.utils.sim_agents import submission_specs
from waymo_open_dataset.utils.sim_agents import visualizations
from waymo_open_dataset.wdl_limited.sim_agents_metrics import metric_features
from waymo_open_dataset.wdl_limited.sim_agents_metrics import metrics

from darwin_waymo import paths
paths.ensure_dirs()

# ============================================================
# 1. LOAD DATA
# ============================================================
DATA_FILE = str(paths.DEFAULT_VALIDATION_SHARD)
OUTPUT_DIR = str(paths.VIZ_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("STEP 1: Loading data")
print("=" * 60)

dataset = tf.data.TFRecordDataset([DATA_FILE])
dataset_iterator = dataset.as_numpy_iterator()

bytes_example = next(dataset_iterator)
scenario = scenario_pb2.Scenario.FromString(bytes_example)
print(f'Type: {type(scenario)}')
print(f'Loaded scenario with ID: {scenario.scenario_id}')
print(f'Number of tracks: {len(scenario.tracks)}')
print(f'Number of timesteps: {len(scenario.timestamps_seconds)}')
print(f'Current time index: {scenario.current_time_index}')

# ============================================================
# 2. SIMULATION SPECS
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Simulation specifications")
print("=" * 60)

challenge_type = submission_specs.ChallengeType.SIM_AGENTS
submission_config = submission_specs.get_submission_config(challenge_type)

print(f'Simulation length, in steps: {submission_config.n_simulation_steps}')
print(f'Step duration: {submission_config.step_duration_seconds}s '
      f'(frequency: {1/submission_config.step_duration_seconds}Hz)')
print(f'Number of parallel simulations: {submission_config.n_rollouts}')

# ============================================================
# 3. VISUALIZE SCENARIO
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Visualizing scenario")
print("=" * 60)

fig, ax = plt.subplots(1, 1, figsize=(10, 10))
visualizations.add_map(ax, scenario)

def plot_track_trajectory(track, ax):
    valids = np.array([state.valid for state in track.states])
    if np.any(valids):
        x = np.array([state.center_x for state in track.states])
        y = np.array([state.center_y for state in track.states])
        ax.plot(x[valids], y[valids], linewidth=5)

for track in scenario.tracks:
    plot_track_trajectory(track, ax)

plt.savefig(os.path.join(OUTPUT_DIR, 'scenario_map.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/scenario_map.png')

# ============================================================
# 4. AGENTS TO SIMULATE
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Agents to simulate")
print("=" * 60)

sim_agent_ids = submission_specs.get_sim_agent_ids(scenario, challenge_type)
print(f'Objects to resimulate: {sim_agent_ids}')
print(f'Total objects: {len(sim_agent_ids)}')

eval_agent_ids = submission_specs.get_evaluation_sim_agent_ids(scenario, challenge_type)
print(f'Objects to evaluate: {eval_agent_ids}')

fig, ax = plt.subplots(1, 1, figsize=(10, 10))
visualizations.add_map(ax, scenario)
for track in scenario.tracks:
    if track.id in sim_agent_ids:
        plot_track_trajectory(track, ax)
plt.savefig(os.path.join(OUTPUT_DIR, 'sim_agents_tracks.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/sim_agents_tracks.png')

# ============================================================
# 5. SIMULATE WITH LINEAR EXTRAPOLATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Running simulation (linear extrapolation)")
print("=" * 60)

def simulate_with_extrapolation(scenario, print_verbose_comments=True):
    vprint = print if print_verbose_comments else lambda arg: None

    logged_trajectories = trajectory_utils.ObjectTrajectories.from_scenario(scenario)
    vprint(f'Original shape: {logged_trajectories.valid.shape} (n_objects, n_steps)')

    logged_trajectories = logged_trajectories.gather_objects_by_id(
        tf.convert_to_tensor(submission_specs.get_sim_agent_ids(scenario, challenge_type))
    )
    logged_trajectories = logged_trajectories.slice_time(
        start_index=0, end_index=submission_config.current_time_index + 1
    )
    vprint(f'Filtered shape: {logged_trajectories.valid.shape} (n_objects, n_steps)')
    vprint(f'All agents valid at last step: {tf.reduce_all(logged_trajectories.valid[:, -1]).numpy()}')

    states = tf.stack([
        logged_trajectories.x, logged_trajectories.y,
        logged_trajectories.z, logged_trajectories.heading,
    ], axis=-1)
    n_objects, _, _ = states.shape
    last_velocities = states[:, -1, :3] - states[:, -2, :3]
    last_velocities = tf.concat([last_velocities, tf.zeros((n_objects, 1))], axis=-1)

    valid_diff = tf.logical_and(
        logged_trajectories.valid[:, -1], logged_trajectories.valid[:, -2]
    )
    last_velocities = tf.where(
        valid_diff[:, tf.newaxis], last_velocities, tf.zeros_like(last_velocities)
    )
    vprint(f'Max velocity: {tf.reduce_max(tf.abs(last_velocities)).numpy():.4f}')

    NOISE_SCALE = 0.01
    max_action = tf.reduce_max(last_velocities, axis=0)
    simulated_states = tf.tile(
        states[tf.newaxis, :, -1:, :], [submission_config.n_rollouts, 1, 1, 1]
    )

    for _ in range(submission_config.n_simulation_steps):
        current_state = simulated_states[:, :, -1, :]
        action_noise = tf.random.normal(current_state.shape, mean=0.0, stddev=NOISE_SCALE)
        actions_with_noise = last_velocities[None, :, :] + (action_noise * max_action)
        next_state = current_state + actions_with_noise
        simulated_states = tf.concat([simulated_states, next_state[:, :, None, :]], axis=2)

    simulated_states = simulated_states[:, :, 1:, :]
    vprint(f'Simulated states shape: {simulated_states.shape}')

    return logged_trajectories, simulated_states

logged_trajectories, simulated_states = simulate_with_extrapolation(scenario)

# ============================================================
# 6. VISUALIZE SIMULATED TRAJECTORIES
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: Visualizing simulated trajectories")
print("=" * 60)

n_objects = logged_trajectories.valid.shape[0]
lengths = tf.broadcast_to(
    logged_trajectories.length[:, 10, tf.newaxis],
    (n_objects, submission_config.n_simulation_steps),
)
widths = tf.broadcast_to(
    logged_trajectories.width[:, 10, tf.newaxis],
    (n_objects, submission_config.n_simulation_steps),
)

# Plot first rollout trajectories as static image
fig, ax = plt.subplots(1, 1, figsize=(10, 10))
visualizations.add_map(ax, scenario)
for i in range(min(n_objects, 20)):
    ax.plot(
        simulated_states[0, i, :, 0].numpy(),
        simulated_states[0, i, :, 1].numpy(),
        linewidth=2, alpha=0.7
    )
plt.title('Rollout 0 — Simulated Trajectories')
plt.savefig(os.path.join(OUTPUT_DIR, 'simulated_trajectories.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/simulated_trajectories.png')

# ============================================================
# 7. PACKAGE INTO SUBMISSION PROTOS
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: Packaging submission protos")
print("=" * 60)

def joint_scene_from_states(states, object_ids):
    states = states.numpy()
    simulated_trajectories = []
    for i_object in range(len(object_ids)):
        simulated_trajectories.append(
            sim_agents_submission_pb2.SimulatedTrajectory(
                center_x=states[i_object, :, 0],
                center_y=states[i_object, :, 1],
                center_z=states[i_object, :, 2],
                heading=states[i_object, :, 3],
                object_id=object_ids[i_object],
            )
        )
    return sim_agents_submission_pb2.JointScene(
        simulated_trajectories=simulated_trajectories
    )

def scenario_rollouts_from_states(scenario, states, object_ids):
    joint_scenes = []
    for i_rollout in range(states.shape[0]):
        joint_scenes.append(joint_scene_from_states(states[i_rollout], object_ids))
    return sim_agents_submission_pb2.ScenarioRollouts(
        joint_scenes=joint_scenes,
        scenario_id=scenario.scenario_id,
    )

# Validate single joint scene
joint_scene = joint_scene_from_states(
    simulated_states[0, :, :, :], logged_trajectories.object_id
)
submission_specs.validate_joint_scene(joint_scene, scenario, challenge_type)
print('JointScene validation: PASSED')

# Validate full scenario rollouts
scenario_rollouts = scenario_rollouts_from_states(
    scenario, simulated_states, logged_trajectories.object_id
)
submission_specs.validate_scenario_rollouts(scenario_rollouts, scenario)
print('ScenarioRollouts validation: PASSED')

# ============================================================
# 8. LOCAL EVALUATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 8: Local metric evaluation")
print("=" * 60)

single_scene_features = metric_features.compute_metric_features(scenario, joint_scene)

print(f'Evaluated objects: {submission_specs.get_evaluation_sim_agent_ids(scenario, challenge_type)}')
print(f'Evaluated objects in features: {single_scene_features.object_id.numpy()}')
print(f'All agents valid: {tf.reduce_all(single_scene_features.valid).numpy()}')
print(f'ADE: {tf.reduce_mean(single_scene_features.average_displacement_error).numpy():.4f}')

# Kinematic features plot
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for i_object in range(len(single_scene_features.object_id)):
    _oid = single_scene_features.object_id[i_object].numpy()
    axes[0].plot(single_scene_features.linear_speed[0, i_object, :], label=str(_oid))
    axes[1].plot(single_scene_features.linear_acceleration[0, i_object, :], label=str(_oid))
    axes[2].plot(single_scene_features.angular_speed[0, i_object, :], label=str(_oid))
    axes[3].plot(single_scene_features.angular_acceleration[0, i_object, :], label=str(_oid))

for ax, title in zip(axes, ['linear_speed', 'linear_accel', 'angular_speed', 'angular_accel']):
    ax.legend(fontsize=6)
    ax.set_title(title)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'kinematic_features.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/kinematic_features.png')

# Interactive features plot
print(f'Collisions: {single_scene_features.collision_per_step[0].numpy()}')
fig, axes = plt.subplots(1, 2, figsize=(8, 4))
for i_object in range(len(single_scene_features.object_id)):
    _oid = single_scene_features.object_id[i_object].numpy()
    axes[0].plot(single_scene_features.distance_to_nearest_object[0, i_object, :], label=str(_oid))
    axes[1].plot(single_scene_features.time_to_collision[0, i_object, :], label=str(_oid))
for ax, title in zip(axes, ['dist to nearest object', 'time to collision']):
    ax.legend(fontsize=6)
    ax.set_title(title)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'interactive_features.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/interactive_features.png')

# Map features plot
print(f'Offroad: {single_scene_features.offroad_per_step[0].numpy()}')
fig, ax = plt.subplots(1, 1, figsize=(4, 4))
for i_object in range(len(single_scene_features.object_id)):
    _oid = single_scene_features.object_id[i_object].numpy()
    ax.plot(single_scene_features.distance_to_road_edge[0, i_object, :], label=str(_oid))
ax.legend(fontsize=6)
ax.set_title('distance to road edge')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'map_features.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {OUTPUT_DIR}/map_features.png')

# Final meta-metric
config = metrics.load_metrics_config(challenge_type)
scenario_metrics = metrics.compute_scenario_metrics_for_bundle(
    config, scenario, scenario_rollouts
)
print(f'\nFinal scenario metrics:\n{scenario_metrics}')

# ============================================================
# 9. GENERATE SUBMISSION ARCHIVE (demo with 2 scenarios)
# ============================================================
print("\n" + "=" * 60)
print("STEP 9: Generating submission archive (demo)")
print("=" * 60)

SUBMISSION_DIR = str(paths.SUBMISSIONS_DIR)
os.makedirs(SUBMISSION_DIR, exist_ok=True)

filenames = [DATA_FILE]
output_filenames = []

for shard_filename in tqdm.tqdm(filenames, desc='Processing shards'):
    shard_suffix = '-00000-of-00150'

    # Process only 2 scenarios per shard (demo)
    shard_dataset = tf.data.TFRecordDataset([shard_filename]).take(2)
    shard_iterator = shard_dataset.as_numpy_iterator()

    shard_rollouts = []
    for scenario_bytes in shard_iterator:
        scenario = scenario_pb2.Scenario.FromString(scenario_bytes)
        logged_traj, sim_states = simulate_with_extrapolation(scenario, print_verbose_comments=False)
        sr = scenario_rollouts_from_states(scenario, sim_states, logged_traj.object_id)
        submission_specs.validate_scenario_rollouts(sr, scenario)
        shard_rollouts.append(sr)

    shard_submission = sim_agents_submission_pb2.SimAgentsChallengeSubmission(
        scenario_rollouts=shard_rollouts,
        submission_type=sim_agents_submission_pb2.SimAgentsChallengeSubmission.SIM_AGENTS_SUBMISSION,
        account_name='ms3169@cam.ac.uk',
        unique_method_name='sim_agents_tutorial',
        authors=['test'],
        affiliation='cambridge',
        description='Tutorial submission',
        method_link='',
        uses_lidar_data=False,
        uses_camera_data=False,
        uses_public_model_pretraining=False,
        num_model_parameters='24',
        acknowledge_complies_with_closed_loop_requirement=True,
    )

    output_filename = f'submission.binproto{shard_suffix}'
    with open(os.path.join(SUBMISSION_DIR, output_filename), 'wb') as f:
        f.write(shard_submission.SerializeToString())
    output_filenames.append(output_filename)

# Create tar.gz
archive_path = os.path.join(SUBMISSION_DIR, 'submission.tar.gz')
with tarfile.open(archive_path, 'w:gz') as tar:
    for output_filename in output_filenames:
        tar.add(
            os.path.join(SUBMISSION_DIR, output_filename),
            arcname=output_filename,
        )

print(f'\nSubmission archive: {archive_path}')
print(f'Archive size: {os.path.getsize(archive_path) / 1024:.1f} KB')

print("\n" + "=" * 60)
print("TUTORIAL COMPLETE!")
print("=" * 60)
print(f'All outputs saved to: {OUTPUT_DIR}/')
