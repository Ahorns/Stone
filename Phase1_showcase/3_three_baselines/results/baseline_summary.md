# Phase 1B · Step 3 — Baseline Comparison

- Shard: `validation.tfrecord-00000-of-00150`
- Scenarios scored: 1
- Total wall time: 27.2 s
- Generated: `python waymo/scripts/run_baselines.py --limit 1`

## Headline metric (metametric — higher is better)

| Baseline | metametric | scenarios | mean wall (s) |
|---|---|---|---|
| `log_replay` | 0.8634 | 1 | 27.23 |

## Sub-metrics (mean across scenarios)

| Metric | `log_replay` |
|---|---|
| metametric | 0.8634 |
| average_displacement_error | 0.0000 |
| min_average_displacement_error | 0.0000 |
| linear_speed_likelihood | 0.5285 |
| linear_acceleration_likelihood | 0.5278 |
| angular_speed_likelihood | 0.9871 |
| angular_acceleration_likelihood | 0.9521 |
| distance_to_nearest_object_likelihood | 0.2400 |
| collision_indication_likelihood | 1.0000 |
| time_to_collision_likelihood | 0.9996 |
| distance_to_road_edge_likelihood | 0.7935 |
| offroad_indication_likelihood | 1.0000 |
| traffic_light_violation_likelihood | 1.0000 |
| simulated_collision_rate | 0.0000 |
| simulated_offroad_rate | 0.0000 |
| simulated_traffic_light_violation_rate | 0.0000 |

## Reference scores (from WOSAC paper / leaderboard)

| System | metametric |
|---|---|
| Random Gaussian        | 0.155 |
| Constant Velocity      | 0.287 |
| CV + Gaussian Noise    | 0.324 |
| SBTA-AIDA              | 0.338 |
| Wayformer (Diverse)    | 0.531 |

## Diagnostic notes

- `log_replay` and `constant_velocity` produce 32 *identical* rollouts (no diversity).
  WOSAC scores rollouts as a distribution match, so identical rollouts under-score on
  diversity-sensitive features. The gap between log_replay and Wayformer is partly diversity.
- `rule_based` gets diversity for free via parameter perturbation in `RolloutEngine`.
- This is a single shard (~290 scenarios). Aggregate scores will move once the full validation
  set is available.
