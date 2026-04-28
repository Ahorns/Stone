# Phase 1B · Step 4 — First Learned Sim-Agent Model

**Goal:** train a small neural next-step predictor on the validation shard, plug it into the existing rollout/scoring harness as a 4th baseline, and beat `constant_velocity` on at least one WOSAC sub-metric.

**Hardware:** PyTorch 2.6 + CUDA 12.4. 4× NVIDIA A100-SXM4-80GB visible (`torch.cuda.is_available() == True`). TF stays on CPU for metric scoring (TF 2.12 can't see the GPUs — see Step 3 lessons).

**Out of scope:** SOTA performance, full WOMD training set, agent–agent attention / GNN. Those belong to Phase 2.

---

## Lessons applied from Step 3

The 1h 47m baseline run was painful. Concrete fixes encoded into Step 4:

| Step 3 problem | Step 4 fix |
|---|---|
| Runner only wrote results at the end | All scripts append per-scenario CSV rows + write status JSON every iteration. |
| Time estimates were 2× off | Smoke-test before any long run; multiply gut estimate by 1.5. |
| `nohup` + tqdm-to-file gave no progress visibility | Status JSON readable any time via `cat`. |
| Profile-late surprised us | Profile a single rollout step on day 1 before committing to N rollouts × M scenarios. |
| GPU was disabled blindly | All learned-model code uses PyTorch on GPU. Only TF metric scoring stays on CPU. |

---

## Architecture decision

**Per-agent next-step Gaussian predictor** (small MLP first, Transformer optional later).

- **Input** (per agent, per timestep): the existing `AgentFeatureExtractor` 44-dim vector (self + lane + 5 neighbours + safety + signal). Already implemented in `darwin_waymo/features/agent_features.py`.
- **Output**: Gaussian over (Δx, Δy, Δheading) — 6 numbers (μ × 3, log σ × 3).
- **Loss**: Gaussian negative log-likelihood against recorded next-step transitions.
- **Rollout**: 80 steps, sample once per rollout from the predicted Gaussian, advance scene.
- **Diversity for 32 rollouts**: independent samples per rollout, plus mild input dropout for additional spread.
- **WOSAC factorisation**: per-agent prediction conditioned only on the *previous* joint state — the conditional-independence requirement is automatically satisfied because each agent is predicted independently within a step.

**Why MLP first, not Transformer.** Phase 1B's bar is "first learned model trains end-to-end and beats constant velocity on at least one sub-metric." MLP gets us there in hours, not days. Transformer is the natural Phase 2 upgrade and we have GPU headroom for it later. Starting bigger now risks burning a day on training-loop bugs that an MLP would have surfaced in 5 minutes.

**Model size.** ~50K-100K params. Trains in <5 min on A100 for 1 shard, even at 50+ epochs.

```
features (44)  ─►  MLP [44→256→256→6]  ─►  (μ_dx, μ_dy, μ_dh, log σ_dx, log σ_dy, log σ_dh)
```

---

## File layout

New code:
```
darwin_waymo/learned/
├── __init__.py
├── dataset.py        # ParsedScenario → (X, Y) numpy → save .npz
├── model.py          # PyTorch MLP with Gaussian head
├── train.py          # NLL training loop, checkpoint, GPU
└── policy.py         # LearnedPolicy: torch model → 32×n_agents×80×4 rollout

waymo/scripts/
├── prepare_dataset.py    # one-shot: shard → training tensors on disk
├── train_step4.py        # CLI wrapper around darwin_waymo.learned.train
└── (run_baselines.py)    # patched for incremental writes; register 'learned' baseline

waymo/results/
├── baselines/   (existing — Step 3 artefacts)
└── step4/       (NEW — checkpoints + training curves + eval)
```

Patches to existing code:
- `darwin_waymo/policies/baselines.py` — add `learned_rollout(parsed)` and register in `BASELINES`.
- `waymo/scripts/run_baselines.py` — append rows incrementally; write status JSON; pre-loaded learned model for `learned` baseline.

---

## Stages and exit criteria

Each stage has a concrete artefact and an exit check. Don't move on until the check passes.

### Stage 0 — encode the Step 3 lesson (15 min)

**Deliverable:** patched `run_baselines.py` that writes per-scenario CSV rows immediately and a `status.json` after each.
**Exit check:** `python waymo/scripts/run_baselines.py --limit 1 --baselines log_replay` produces a CSV with the row visible mid-run, plus a `status.json` showing `{"done": 1, "total": 1}`.

### Stage 1 — dataset extraction (1-2 hr)

**Deliverable:** `darwin_waymo/learned/dataset.py` + `waymo/scripts/prepare_dataset.py` that turns the validation shard into `train.npz` and `val.npz` files.

For each (scenario, agent, future timestep with valid current+next states):
- `X[i] = AgentFeatureExtractor.extract(agent_id, t, ...)` — 44-dim vector
- `Y[i] = (x[t+1]-x[t], y[t+1]-y[t], wrap(heading[t+1]-heading[t]))` — 3-dim target
- `agent_type[i]` — bookkeeping

Train/val split by **scenario id**, not sample (avoid leakage). 80/20.

**Exit check:**
- `prepare_dataset.py` runs end-to-end on 5 scenarios in <2 min.
- Histograms of Y look sane: Δx ranges ~[-3, 3] m at 0.1 s, Δheading rarely exceeds 0.2 rad/step, ~10% of samples have |Δx|<0.01 (parked/stopped).
- `X` shape `(N, 44)`, `Y` shape `(N, 3)`. No NaN/Inf.

### Stage 2 — model + training (2-3 hr)

**Deliverable:** `darwin_waymo/learned/model.py` (`MLPNextStep`) + `darwin_waymo/learned/train.py` + `waymo/scripts/train_step4.py`.

- Loss: Gaussian NLL `0.5 * ((y - μ)/σ)² + log σ` per dimension, averaged.
- Optimiser: AdamW, lr 1e-3, batch 1024.
- Checkpoint: `waymo/results/step4/checkpoints/last.pt` and `best_val.pt`.
- Logs: `waymo/results/step4/training_log.csv` per epoch (train/val NLL).

**Exit check:**
- Training runs on GPU (`nvidia-smi` shows utilisation during the run).
- Validation NLL strictly decreases for at least the first 5 epochs.
- Training one epoch takes <2 min on A100.

### Stage 3 — LearnedPolicy + rollout integration (1-2 hr)

**Deliverable:** `darwin_waymo/learned/policy.py` exposing `learned_rollout(parsed, checkpoint_path)`. Update `policies/baselines.py` to register it.

For each rollout `r`:
1. Initialise scene from last observed step (same as RolloutEngine).
2. For step `s` in 0..79:
   a. Build per-agent feature vectors from current scene.
   b. Batch all agents into one GPU forward pass (saves time vs per-agent loop).
   c. Sample (Δx, Δy, Δh) per agent from predicted Gaussian.
   d. Apply update: `(x, y, h) += (Δx, Δy, Δh)`. (Z held constant.)
   e. Advance to next step.
3. Stack into `(32, n_agents, 80, 4)` array.

Diversity comes from per-rollout sampling noise.

**Exit check:**
- Single-scenario smoke produces `(32, n_agents, 80, 4)` array.
- `submission_specs.validate_scenario_rollouts(...)` passes.
- One rollout step takes <100 ms on GPU; full scenario rollout (32 × 80 steps) <30 s.

### Stage 4 — evaluate against the 3 baselines (~10 min runtime)

**Deliverable:** updated `baseline_summary.md` with 4 columns (log_replay, constant_velocity, rule_based, **learned**) on at least 5 scenarios; ideally all 15.

Use the patched `run_baselines.py`:
```
python waymo/scripts/run_baselines.py --limit 5 --baselines log_replay constant_velocity learned
python waymo/scripts/run_baselines.py --limit 15  # full comparison
```

**Exit check:** `learned` beats `constant_velocity` on **at least one** sub-metric (target candidates: `linear_speed_likelihood`, `linear_acceleration_likelihood`, `min_average_displacement_error`). Bonus if it beats `rule_based` on `simulated_offroad_rate`.

### Stage 5 — write up (30 min)

**Deliverable:** short markdown report at `waymo/results/step4/report.md` summarising:
- Architecture + training hyperparameters.
- Dataset statistics (N_train, N_val, agent type distribution).
- Training curve (final train/val NLL).
- Baseline comparison table (5 baselines × WOSAC sub-metrics).
- Failure modes still present.
- What Phase 2 should target next.

---

## Time estimates (with GPU)

Best-case ~6 hours of focused work + ~30 min total runtime. Realistic ~1 day. I'll multiply by 1.5 per the Step 3 lesson, so plan for 1.5 days end-to-end if there are integration surprises.

| Stage | Code time | Run time |
|---|---|---|
| 0 — incremental writes patch | 15 min | 1 min smoke |
| 1 — dataset extraction | 1.5 hr | 2 min smoke / 5 min full extraction |
| 2 — model + training | 2 hr | 5-15 min training |
| 3 — LearnedPolicy + rollout | 1.5 hr | 1-2 min smoke |
| 4 — evaluation | 0 (already wired) | ~10 min for 15 scenarios |
| 5 — write-up | 30 min | — |
| **Total** | **5.5-6 hr** | **~30 min** |

---

## Outputs

After Step 4 is complete:

```
darwin_waymo/learned/                  # implementation
waymo/scripts/{prepare_dataset,train_step4}.py
waymo/results/step4/
├── checkpoints/{last,best_val}.pt
├── training_log.csv
├── eval/baseline_comparison.csv       # 60 rows = 15 scenarios × 4 baselines
├── eval/baseline_summary.md           # updated table
└── report.md                          # short Phase 1B Step 4 write-up
```

Together with the existing `waymo/results/baselines/` artefacts, this completes Phase 1B in full.
