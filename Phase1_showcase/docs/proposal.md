# CASA Dissertation Proposal — Complete Draft

---

## Form Fields Overview

| # | Field | Type | Required |
|---|-------|------|----------|
| 1 | Proposed title | Text | * |
| 2 | Proposed research question (50–100 words) | Text | * |
| 3 | Summary of existing literature incl. references (200 words) | Text | * |
| 4 | Proposed methodologies | Text | * |
| 5 | Proposed data — where will you get it | Text | * |
| 6 | Summary of planned analysis (200 words) | Text | * |
| 7 | Project partner (company) and email | Text | Optional |
| 8 | Planning field work? | Radio: Yes / Maybe / No | * |
| 9 | If yes/maybe, which UCL forms needed | Text | Conditional |
| 10 | Ethical considerations (100–200 words) | Text | * |
| 11 | Will you need ethical approval? | Radio: No / Yes low risk / Yes moderate-high / I don't know | * |

---

## Suggested Project Titles

### Option A (Recommended)

Comparative Evaluation of Multi-Agent Trajectory Prediction Methods for Autonomous Driving Using the Waymo Open Motion Dataset

### Option B

From Heuristics to Deep Generative Models: A Systematic Study of Motion Forecasting Approaches in Urban Driving Scenarios

### Option C

Multi-Agent Motion Forecasting in Autonomous Driving: Developing and Benchmarking Baseline-to-Advanced Prediction Pipelines on Large-Scale Real-World Data

**Recommendation:** Option A — most precise, clearly scoping the dataset, the task (multi-agent trajectory prediction), and the methodology (comparative evaluation). It reads naturally for a UK MSc dissertation and avoids overpromising.

> 中文说明：推荐选项A，因为它最清晰地界定了数据集（Waymo）、任务（多智能体轨迹预测）和方法论（对比评估）。标题简洁、学术化，适合硕士论文。

---

## Field 1 — Proposed Title

**Main version:**

> Comparative Evaluation of Multi-Agent Trajectory Prediction Methods for Autonomous Driving Using the Waymo Open Motion Dataset

**Stronger alternative:**

> Benchmarking Multi-Agent Trajectory Forecasting in Urban Driving: A Progressive Evaluation from Rule-Based Baselines to Data-Driven Generative Models on the Waymo Open Motion Dataset

> 中文说明：标题明确点出了三个核心要素：多智能体轨迹预测、自动驾驶、Waymo数据集，并强调这是一个"对比评估"研究，而非竞赛。

---

## Field 2 — Proposed Research Question (50–100 words)

**Main version:**

> How effectively can progressively complex trajectory prediction methods — from simple rule-based heuristics (constant velocity, lane-following extrapolation) to data-driven generative models (Conditional Variational Autoencoders and Transformer-based architectures) — forecast the joint future motion of multiple interacting agents in real-world urban driving scenarios? This project investigates the trade-offs between model complexity, computational cost, and prediction accuracy using the Waymo Open Motion Dataset, evaluating each method against standardised realism metrics encompassing kinematic fidelity, inter-agent interaction quality, and map compliance.

(~75 words)

**Stronger alternative:**

> To what extent do data-driven generative models for multi-agent trajectory prediction improve upon rule-based heuristics in capturing the stochastic, interactive nature of real-world urban traffic, and what are the marginal returns of increased model complexity when evaluated against distributional realism metrics on the Waymo Open Motion Dataset?

> 中文说明：研究问题概括了项目核心：从简单基线到复杂模型，逐步比较不同轨迹预测方法在真实城市驾驶场景中的表现，重点关注精度、计算成本和现实性之间的权衡。

---

## Field 3 — Summary of Existing Literature (200 words)

**Main version:**

> Multi-agent trajectory prediction is a critical component of autonomous driving systems, requiring accurate forecasting of the future states of vehicles, pedestrians, and cyclists in shared environments. Early approaches relied on physics-based models such as constant velocity extrapolation and the Intelligent Driver Model (Treiber et al., 2000), which assume deterministic, independent agent motion. Social Force models (Helbing and Molnár, 1995) introduced inter-agent interaction but remain limited in complex traffic.
>
> Recent advances have shifted toward deep learning. Recurrent architectures such as Social LSTM (Alahi et al., 2016) and convolutional approaches like Social GAN (Gupta et al., 2018) model social interactions and multimodal futures. Transformer-based methods, notably Wayformer (Noh et al., 2022) and MTR (Shi et al., 2022), leverage attention mechanisms for scene-level context encoding and have demonstrated state-of-the-art performance on large-scale benchmarks. Conditional Variational Autoencoders, as used in PRECOG (Rhinehart et al., 2019) and Trajectron++ (Salzmann et al., 2020), offer principled stochastic prediction by modelling latent intent variables.
>
> The Waymo Open Motion Dataset (Ettinger et al., 2021) provides over 480,000 real-world driving scenarios with high-fidelity agent tracks and HD map data, establishing a rigorous evaluation benchmark. Montali et al. (2023) formalised distributional realism metrics — spanning kinematic, interactive, and map-adherence features — offering a comprehensive evaluation framework beyond traditional displacement-based metrics.

(~195 words)

> 中文说明：文献综述从物理模型（匀速、IDM）讲到深度学习（Social LSTM/GAN、Transformer、CVAE），最后引出Waymo数据集和WOSAC评估框架，形成从简单到复杂的逻辑链条，与项目方法论一致。

---

## Field 4 — Proposed Methodologies

**Main version:**

> This project adopts a progressive, comparative methodology, implementing and evaluating trajectory prediction methods of increasing complexity:
>
> **1. Rule-Based Baselines:**
> - *Constant Velocity (CV) Model:* Extrapolates each agent's last observed heading and speed over the prediction horizon, serving as a zero-learning baseline.
> - *Constant Velocity with Lane Following:* Augments the CV model with HD map information, constraining predicted trajectories to follow lane centrelines, thereby improving map compliance.
>
> **2. Probabilistic Generative Models:**
> - *Conditional Variational Autoencoder (CVAE):* A latent-variable model conditioned on observed trajectories and scene context, capable of generating diverse, multimodal future trajectories by sampling from the learned latent distribution.
>
> **3. Attention-Based Architecture (stretch goal):**
> - *Simplified Transformer-based forecaster:* A lightweight attention-based encoder-decoder that processes agent history and map features to produce multi-modal trajectory predictions, inspired by Wayformer and MTR architectures.
>
> **Evaluation Framework:** All methods are evaluated using the WOSAC realism metrics (Montali et al., 2023): kinematic features (speed, acceleration), interaction features (collision rate, distance-to-nearest-object, time-to-collision), and map-adherence features (offroad rate, distance-to-road-edge). A composite metric aggregates these via weighted negative log-likelihood to enable principled cross-method comparison.

**Stronger alternative (adds closed-loop framing):**

> Additionally, models will be evaluated in both open-loop (single-pass prediction) and closed-loop (autoregressive rollout at 10 Hz) settings where feasible, enabling assessment of error accumulation and robustness to distribution shift — a key distinction highlighted in the WOSAC evaluation framework.

> 中文说明：方法论分三个层次递进：(1) 基于规则的简单基线；(2) 概率生成模型CVAE；(3) Transformer（作为延伸目标）。所有方法使用统一的WOSAC指标评估，确保公平对比。这种渐进式设计既保证了最低可交付成果，也留有上升空间。

---

## Field 5 — Proposed Data

**Main version:**

> The primary dataset is the **Waymo Open Motion Dataset (WOMD) v1.2** (Ettinger et al., 2021), a large-scale, publicly available dataset for motion prediction research in autonomous driving. It is freely accessible via the Waymo Open Dataset website (https://waymo.com/open/) under a non-commercial research licence.
>
> **Dataset characteristics:**
> - **Scale:** 486,995 training scenarios, 44,097 validation scenarios, and 44,920 test scenarios, mined from 103,354 driving segments of 20 seconds each.
> - **Format:** Each scenario comprises 9.1 seconds at 10 Hz (1.1s history + 8.0s future), with up to 128 agents per scene.
> - **Agent types:** Vehicles, pedestrians, and cyclists, with bounding box dimensions and per-timestep state (position, heading, velocity).
> - **Map data:** High-definition road graph including lane boundaries, lane types, traffic signal states, stop signs, and crosswalks.
>
> The training and validation splits will be used for model development and hyperparameter tuning. The validation set will serve as the primary evaluation benchmark for all reported results. No proprietary or personal data is required.

> 中文说明：数据来自Waymo公开数据集，免费用于非商业研究。包含约48万训练场景，含高精地图和多类交通参与者数据。仅使用训练集和验证集，不涉及个人隐私数据。

---

## Field 6 — Summary of Planned Analysis (200 words)

**Main version:**

> The analysis proceeds in four stages. First, **data exploration and preprocessing**: parsing WOMD scenario protobuf files, extracting agent trajectories, map features, and traffic signals, and computing descriptive statistics on agent distributions, trajectory lengths, and scene complexity. Visualisations of representative scenarios will contextualise model behaviour.
>
> Second, **baseline implementation and evaluation**: the constant velocity and lane-following models will be implemented and evaluated on the full validation set using the WOSAC realism metrics. These results establish performance floors against which learned models are compared.
>
> Third, **generative model development**: a CVAE-based trajectory predictor will be trained, conditioned on observed agent states and local map context. Ablation studies will examine the impact of conditioning features (map, agent interactions) and latent dimension on prediction diversity and accuracy. If time permits, a simplified Transformer-based model will be implemented as a further comparison point.
>
> Fourth, **comparative analysis and interpretation**: all methods will be benchmarked using the nine WOSAC component metrics and the composite realism score. Statistical analysis will quantify performance differences across agent types (vehicles, pedestrians, cyclists) and scenario complexity (intersections, highway merges, unprotected turns). Failure case analysis will identify systematic weaknesses of each approach, informing recommendations for future work.

(~195 words)

> 中文说明：分析分四阶段：数据探索 → 基线评估 → 生成模型训练与消融实验 → 跨方法对比分析。重点不仅是数值指标，还包括按场景类型和智能体类型的细分分析以及失败案例研究。

---

## Field 7 — Project Partner

*(Leave blank — no external project partner)*

> 中文说明：无外部合作方，留空即可。

---

## Field 8 — Field Work?

**Answer: No**

> 中文说明：本项目纯为计算/数据分析类研究，无需实地调研。选"No"。

---

## Field 9 — UCL Forms (conditional)

*(Not applicable — no field work planned)*

> 中文说明：因选了"No"，此项留空。

---

## Field 10 — Ethical Considerations (100–200 words)

**Main version:**

> This project uses the Waymo Open Motion Dataset, which is a publicly released, de-identified dataset collected and published by Waymo LLC under a research licence. All trajectory data represents anonymised object tracks derived from perception system outputs (bounding boxes and centroids), not raw sensor imagery, and contains no personally identifiable information such as faces, licence plates, or GPS coordinates linkable to individuals.
>
> No human participants are involved in this research; all experiments are conducted computationally on pre-existing secondary data. The dataset's terms of use will be strictly observed, and it will be used exclusively for non-commercial academic research purposes.
>
> From a broader ethical perspective, this research contributes to improving the safety and reliability of autonomous vehicle simulation systems. However, it is acknowledged that trajectory prediction technologies could, in principle, be applied to surveillance contexts. This project will not develop or endorse any such applications. All code and results will be presented transparently, with clear documentation of limitations and failure modes, consistent with responsible AI research practices.

(~155 words)

> 中文说明：伦理部分强调三点：(1) 数据已脱敏，不含个人信息；(2) 无人类参与者，纯计算研究；(3) 承认轨迹预测技术的潜在双重用途，但本项目仅限于学术安全研究。

---

## Field 11 — Ethical Approval?

**Answer: No**

> 中文说明：使用公开脱敏数据、无人类参与者，不需要伦理审批。选"No"。

---

## Project Timeline

| Week | Dates (approx.) | Activities |
|------|-----------------|------------|
| 1–2 | Late June | Literature review; dataset download & environment setup; familiarise with WOMD protobuf format and Waymax toolkit |
| 3–4 | Early July | Data exploration & preprocessing; implement constant velocity baseline; set up evaluation pipeline (WOSAC metrics) |
| 5–6 | Mid July | Implement lane-following baseline; baseline evaluation & analysis; begin CVAE architecture design |
| 7–8 | Late July | CVAE training & hyperparameter tuning; ablation studies on conditioning features and latent dimensions |
| 9–10 | Early August | (Stretch) Implement simplified Transformer forecaster; comparative evaluation across all methods |
| 11–12 | Mid August | Per-scenario and per-agent-type analysis; failure case study; visualisation of results |
| 13–14 | Late August | Dissertation writing: introduction, literature review, methodology |
| 15–16 | Early September | Dissertation writing: results, discussion, conclusion; proofreading and submission |

---

## Risk Management Plan

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dataset too large for local storage/compute | Medium | High | Use WOMD's pre-sharded structure; process scenarios in batches; leverage UCL HPC or cloud GPU resources (A100 available) |
| CVAE model fails to converge or produces low-diversity outputs | Medium | Medium | Implement KL-annealing schedule; test multiple latent dimensions; fall back to Gaussian Mixture output heads |
| Transformer stretch goal infeasible within timeline | High | Low | Explicitly scoped as stretch goal; core contributions (baselines + CVAE + comparative analysis) are self-contained without it |
| Evaluation metric implementation errors | Low | High | Cross-validate against published baseline scores in Montali et al. (2023) Table 3; use official WOSAC evaluation code where available |
| Protobuf parsing/data pipeline issues | Medium | Medium | Waymo provides official tutorials and Waymax library; allocate dedicated setup time in Weeks 1–2 |
| Time overrun on writing | Medium | High | Begin writing methodology and literature review in parallel with experiments from Week 8; maintain running experiment log |

---

## Suggested References

1. Ettinger, S., Cheng, S., Caine, B., et al. (2021). "Large Scale Interactive Motion Forecasting for Autonomous Driving: The Waymo Open Motion Dataset." *ICCV 2021*.

2. Montali, N., Lambert, J., Mougin, P., et al. (2023). "The Waymo Open Sim Agents Challenge." *NeurIPS 2023 Datasets and Benchmarks Track*. arXiv:2305.12032.

3. Alahi, A., Goel, K., Raber, V., et al. (2016). "Social LSTM: Human Trajectory Prediction in Crowded Spaces." *CVPR 2016*.

4. Gupta, A., Johnson, J., Fei-Fei, L., et al. (2018). "Social GAN: Socially Acceptable Trajectories with Generative Adversarial Networks." *CVPR 2018*.

5. Salzmann, T., Ivanovic, B., Chakravarty, P., and Pavone, M. (2020). "Trajectron++: Dynamically-Feasible Trajectory Forecasting with Heterogeneous Data." *ECCV 2020*.

6. Rhinehart, N., McAllister, R., Kitani, K., and Levine, S. (2019). "PRECOG: Prediction Conditioned on Goals in Visual Multi-Agent Settings." *ICCV 2019*.

7. Noh, J., et al. (2022). "Wayformer: Motion Forecasting via Simple & Efficient Attention Networks." *ICRA 2023*.

8. Shi, S., Jiang, L., Dai, D., and Schiele, B. (2022). "MTR: Motion Transformer with Global Intention Localization and Local Movement Refinement." *NeurIPS 2022*.

9. Treiber, M., Hennecke, A., and Helbing, D. (2000). "Congested Traffic States in Empirical Observations and Microscopic Simulations." *Physical Review E*, 62(2), 1805–1824.

10. Helbing, D. and Molnár, P. (1995). "Social Force Model for Pedestrian Dynamics." *Physical Review E*, 51(5), 4282–4286.

11. Sohn, K., Lee, H., and Yan, X. (2015). "Learning Structured Output Representation using Deep Conditional Generative Models." *NeurIPS 2015*. (CVAE foundation)

12. Vaswani, A., et al. (2017). "Attention Is All You Need." *NeurIPS 2017*. (Transformer foundation)

13. Gulino, C., et al. (2024). "Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research." *NeurIPS 2023*.
