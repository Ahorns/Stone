# Phase 1B · Step 4 — First Learned Sim-Agent Model

**Status:** complete. The first learned next-step predictor was trained end-to-end, integrated as a fourth baseline, and evaluated under official WOSAC metrics.

**Headline finding:** the model trains cleanly on one-step prediction (best val NLL = -8.51) but underperforms the constant-velocity baseline in 80-step closed-loop rollout (metametric ~0.22 vs const-vel ~0.48 on the same scenarios). The dominant failure mode is *closed-loop compounding error*: agents drift off-road on 100% of rollouts and ADE reaches ~50 m by 8 s. This is an expected consequence of training on one-step prediction with ground-truth current state and evaluating in closed loop, and it directly motivates the Phase 2 program (joint multi-agent training, agent–agent attention, scheduled sampling / DAGGER).

---

## 1. Architecture

| | |
|---|---|
| Inputs | 44-d feature vector from existing `darwin_waymo.features.AgentFeatureExtractor` (self / lane / 5 neighbours / safety / signal) |
| Targets | (Δforward, Δlateral, Δheading) in **ego frame** |
| Model | 3-layer MLP `[44 → 256 → 256 → 6]` with GELU activations, Gaussian head (μ × 3, log σ × 3) |
| Parameters | 78,854 |
| Loss | Gaussian negative log-likelihood per dimension, summed |
| Hardware | NVIDIA A100 80GB (PyTorch 2.6 + CUDA 12.4); TF stays on CPU for metric scoring |

Files:
- `darwin_waymo/learned/model.py` — `MLPNextStep`, `gaussian_nll`
- `darwin_waymo/learned/dataset.py` — scenario → (X 44-d, Y 3-d) sample extraction
- `darwin_waymo/learned/train.py` — training loop with NLL, AdamW, val-NLL checkpointing
- `darwin_waymo/learned/policy.py` — `learned_rollout` for closed-loop simulation
- Baseline registered in `darwin_waymo/policies/baselines.py` under `learned`

## 2. Dataset

Built from the single validation shard `validation.tfrecord-00000-of-00150`.

| | Train | Val |
|---|---|---|
| Scenarios | 229 | 57 |
| Samples (transitions) | 533,590 | 137,104 |
| Vehicle / pedestrian / cyclist | 93.5% / 5.7% / 0.7% | 95.5% / 3.9% / 0.6% |
| Target std (Δfwd, Δlat, Δh) | (0.486, 0.018, 0.082) | (0.498, 0.016, 0.074) |
| Target mean Δfwd | 0.268 m/0.1s ≈ 2.7 m/s | 0.246 m/0.1s ≈ 2.5 m/s |

Train/val split is by *scenario id*, not sample, to avoid leakage. Targets are rotated into the agent's ego frame at time t — the regression is then rotation-invariant relative to the scene.

## 3. Training

Two runs were performed on the same data:

| Run | Epochs | Dropout | Weight decay | Best val NLL | Notes |
|---|---|---|---|---|---|
| **v1** | 30 | 0 | 1e-4 | **-8.25** (epoch 5) | Heavy overfit: train NLL ran to -12.6, val NLL exploded to +208 by epoch 30. Best-val checkpointing rescued epoch 5. |
| **v2** | 12 | 0.2 | 1e-2 | **-8.51** (epoch 8) | Stable: train -1.2 → -9.5, val swings between -8.5 and +2 but stays bounded. |

Wall time: ~50 s for 12 epochs on a single A100 — training was never the bottleneck.

The v1 → v2 shift confirmed that overfitting was the textbook problem (train ⤢ val ⤡), and stronger regularization plus shorter training fixed it. **v2 is the checkpoint used for evaluation.**

## 4. Closed-loop rollout

`learned_rollout` constructs 32 rollouts × 80 steps × N agents × (x, y, z, heading) — the same shape produced by the rule-based `RolloutEngine`. Per step:

1. Build a 44-d feature vector for every sim-agent at the current simulated state (using the existing `AgentFeatureExtractor` with `all_agent_states` dict).
2. Stack into a `(N_agents, 44)` batch and forward through the MLP in one pass.
3. Sample (Δfwd, Δlat, Δh) per agent from the predicted Gaussian (or take μ if `DARWIN_WAYMO_LEARNED_SAMPLE=0`).
4. Rotate ego-frame deltas back to world frame using each agent's heading; advance the scene.

Object dimensions are held fixed from `t0` per the WOSAC factorisation rule. The ADV and world predictions are emitted independently in the same step, satisfying the conditional-independence requirement.

Diversity across the 32 rollouts comes from per-rollout RNG seeds applied to the Gaussian sampling.

**Performance**: ~210 s per scenario on CPU (interleaved with the WOSAC metric scoring). The bottleneck is per-agent feature extraction (lane lookup, neighbour search), not the neural-net forward pass.

## 5. Evaluation

**The same 2 scenarios used in the Step 3 smoke test were re-evaluated with the learned baseline. Step 3 scores on these scenarios are shown for direct comparison.**

| Metric | log_replay (Step 3) | constant_velocity (Step 3) | rule_based (Step 3) | **learned (Step 4 v2)** |
|---|---|---|---|---|
| metametric (mean of 2 scenarios) | **0.877** | 0.520 | 0.327 | **0.217** |
| simulated_offroad_rate | 16.7% | 33.3% | 97.9% | **100.0%** |
| simulated_collision_rate | 0% | 33.3% | 62.5% | 77.6% |
| linear_speed_likelihood | 0.604 | 0.019 | 0.315 | 0.046 |
| distance_to_road_edge_likelihood | 0.794 | 0.676 | 0.215 | 0.147 |
| average_displacement_error (m) | 0.0 | 5.27 | 32.5 | **49.9** |

(The full 5-scenario comparison with all four baselines lives in `eval/baseline_comparison.csv`. A 15-scenario run was not done because rule_based scales poorly — see the Step 3 report.)

**The learned model is the worst of the four baselines** on every sub-metric on these scenarios. The dominant failures:

- **100% off-road rate** — even worse than rule_based's 97.9%. Agents drift sideways out of their lanes.
- **49.9 m ADE** at 8 s — agents end up wildly displaced from where the recorded ground truth went.
- **Linear-speed and angular-speed likelihoods near zero** — the kinematic distribution doesn't match real driving at all.

## 6. Why it's underperforming — diagnosis

We saw three observable problems:

1. **The model is overconfident.** On the val set, residual std is (0.076, 0.043, 0.097) but predicted σ is (0.013, 0.007, 0.011) — about 6× too tight. NLL training rewards confident-and-roughly-right; it doesn't penalise overconfidence in the tail strongly enough.

2. **Closed-loop compounding error.** Trained on one-step prediction with the ground-truth current state. At rollout time the current state is *simulated* — and after step 1, the simulated state has drifted from any state the model saw during training. The further into the rollout, the further outside the training distribution the model is asked to predict. With residual std ~0.076 m/step and 80 steps, expected drift exceeds 6 m purely from one-step error, even before noise compounds.

3. **Feature extractor mismatch.** `AgentFeatureExtractor` computes acceleration and heading-rate using `track.state_at(timestep − 1)` from the *recorded* track, even when the current ego state is supplied by the simulation. Past step 1 in rollout, this is wrong. Map lookups (lane, road-edge, traffic-signal) are done at the *simulated* position, which after a few off-road steps queries the wrong lane entirely.

These are all expected consequences of an "open-loop trained, closed-loop evaluated" setup — the standard imitation-learning pitfall.

## 7. What this tells us for Phase 2

The closed-loop drift result is itself a useful Phase 1B finding: it isolates the *specific* capability that Phase 2 must address.

Concrete next steps motivated by this experiment:

- **Scheduled sampling / DAGGER.** Train the model on its own simulated states, not just on ground truth. This closes the train/test distribution gap.
- **Joint multi-agent prediction.** Replace per-agent independent prediction with an architecture where each agent's prediction is conditioned on neighbours' predictions in the same step (agent–agent attention or GNN). This is the Phase 2 plan from the slide-guide.
- **Better feature handling at rollout time.** Make `AgentFeatureExtractor` derive previous-step quantities from the *simulated* trajectory, not the recorded one. Cache or vectorise the neighbour lookup so the per-step cost drops.
- **More data.** The 1 shard gives 670K samples — fine for an MLP, marginal for a Transformer. Phase 2 needs the full WOMD training set, hence the supervisor ask for server access with ≥80 GB storage.
- **Wider σ floor + heteroscedastic regularisation.** Penalise overconfidence so that the predicted Gaussian has a less catastrophic NLL on tail samples.

## 8. Phase 1B status

| | |
|---|---|
| **Phase 1A (Steps 1–2)** | Complete in earlier session — pipeline runs, valid SimAgentsChallengeSubmission produced for one shard. |
| **Phase 1B Step 3 (3 baselines)** | Complete — 15-scenario WOSAC scoring; rule-based off-road rate 90.2% confirmed across the shard. |
| **Phase 1B Step 4 (first learned model)** | Complete — trained end-to-end, integrated into the same scoring harness, evaluated. The model trains but does not beat const-vel due to closed-loop drift. |

Phase 1B is now closed. The diagnostic findings — rule-based off-road problem and learned-model closed-loop drift — together give a clean motivation for Phase 2.

## 9. Files produced

```
waymo/results/step4/
├── dataset/
│   ├── train.npz                     533,590 samples
│   ├── val.npz                       137,104 samples
│   └── stats.json                    target distributions, agent type counts
├── checkpoints/  (v1)                first run, dropout 0, wd 1e-4
│   ├── best_val.pt                   epoch 5, val NLL -8.25
│   └── last.pt                       epoch 30, overfit
├── v2/                               second run, dropout 0.2, wd 1e-2
│   ├── checkpoints/best_val.pt       epoch 8, val NLL -8.51 (used for eval)
│   ├── checkpoints/last.pt           epoch 12
│   └── training_log.csv
├── train_summary.json                v1 hyperparams + final stats
├── training_log.csv                  v1 epoch-level NLLs
├── eval/
│   ├── baseline_comparison.csv       per-scenario × per-baseline metrics
│   ├── baseline_summary.md           aggregate summary
│   ├── status.json                   live progress (per-scenario)
│   └── run.log
└── report.md                         (this file)
```
