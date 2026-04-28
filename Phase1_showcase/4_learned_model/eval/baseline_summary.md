# Phase 1B · Step 3 — Baseline Comparison

- Shard: `validation.tfrecord-00000-of-00150`
- Scenarios scored: 5
- Total wall time: 1693.4 s
- Generated: `python waymo/scripts/run_baselines.py --limit 5`

## Headline metric (metametric — higher is better)

| Baseline | metametric | scenarios | mean wall (s) |
|---|---|---|---|
| `log_replay` | 0.8632 | 5 | 51.10 |
| `constant_velocity` | 0.5605 | 5 | 50.70 |
| `learned` | 0.2063 | 5 | 236.85 |

## Sub-metrics (mean across scenarios)

| Metric | `log_replay` | `constant_velocity` | `learned` |
|---|---|---|---|
| metametric | 0.8632 | 0.5605 | 0.2063 |
| average_displacement_error | 0.0000 | 7.3237 | 45.5549 |
| min_average_displacement_error | 0.0000 | 7.3237 | 29.0929 |
| linear_speed_likelihood | 0.5106 | 0.0106 | 0.0379 |
| linear_acceleration_likelihood | 0.5058 | 0.0853 | 0.0131 |
| angular_speed_likelihood | 0.7373 | 0.4243 | 0.0149 |
| angular_acceleration_likelihood | 0.8361 | 0.6345 | 0.0070 |
| distance_to_nearest_object_likelihood | 0.4792 | 0.3049 | 0.2067 |
| collision_indication_likelihood | 1.0000 | 0.6002 | 0.1576 |
| time_to_collision_likelihood | 0.9470 | 0.8584 | 0.8295 |
| distance_to_road_edge_likelihood | 0.8213 | 0.6939 | 0.1913 |
| offroad_indication_likelihood | 1.0000 | 0.6067 | 0.0003 |
| traffic_light_violation_likelihood | 1.0000 | 1.0000 | 1.0000 |
| simulated_collision_rate | 0.0000 | 0.3333 | 0.8342 |
| simulated_offroad_rate | 0.1067 | 0.2933 | 1.0000 |
| simulated_traffic_light_violation_rate | 0.0000 | 0.0000 | 0.0000 |

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
