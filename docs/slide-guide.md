下面是一个**完整可直接做 PPT 的版本**。这版的核心定位是：

> 我不是为了冲竞赛 leaderboard，而是把 Waymo Open Sim Agents Challenge 当作一个标准化研究平台，用来学习自动驾驶仿真，并在其中找到一个值得优化的 sim-agent 模型设计问题。

Waymo 对 WOSAC 的定位本身也是推动 realistic simulators，用于自动驾驶 behaviour model 的评估和训练；Waymax 则是基于 Waymo Open Motion Dataset 的自动驾驶多智能体仿真与评估框架。([Waymo][1])

---

# 配图与素材清单 (Asset & Format Notes)

`slides/assets/` 目录下当前可用的素材：

| 文件 | 内容 | PPT 兼容性 | 建议位置 |
|------|------|-----------|----------|
| `demonstrate.gif` | 多智能体 rollout 的动画（黄/蓝色框车辆在路口移动） | GIF 在 PowerPoint 中原生支持，放映时自动循环 | **Slide 3 (Task Definition)** 主图 |
| `home-anim-transparent.webm` | Waymo 主页风格的透明背景动画 | WebM 在 Windows PowerPoint 上兼容性差，建议转码 | **Slide 2 (Background)** 配图 |
| `The factorization.webp` | ego/world state 联合 rollout 的条件独立结构图 | WebP 仅 Office 2021+/365 支持 | **Slide 5 (Benchmark Platform)** 中的 "Required factorization" 子区 |
| `WaymoOpenDatasetLogo.svg` | Waymo Open Dataset 文字 logo | SVG 在 Office 2016+ 原生支持 | **Slide 0 / Slide 5 / Slide 14** 角标 |

## 格式建议

- **GIF** 直接拖入 PPT 即可，放映时自动播放并循环。
- **视频 vs GIF**：PowerPoint 支持插入视频（MP4 最稳），但 GIF 更省心（无需点击播放、跨平台一致）。如果不需要声音、长度 ≤ 10s，转 GIF 通常更方便。
- **WebM → MP4 或 GIF**：PowerPoint 对 WebM 的支持不稳定。推荐用 ffmpeg 转码：
  ```bash
  # 转 MP4（保留较高画质，可在 PPT 内点击播放）
  ffmpeg -i slides/assets/home-anim-transparent.webm -c:v libx264 -pix_fmt yuv420p slides/assets/processed/home-anim.mp4

  # 转 GIF（自动循环，体积更小，建议降帧 + 缩放）
  ffmpeg -i slides/assets/home-anim-transparent.webm -vf "fps=15,scale=720:-1:flags=lanczos" slides/assets/processed/home-anim.gif
  ```
- **WebP → PNG**（如果导师/学校用的是较老版本的 PowerPoint）：
  ```bash
  ffmpeg -i "slides/assets/factorization.webp" "slides/assets/processed/factorization.png"
  ```
- **SVG**：直接拖进 PPT 即可，可无损缩放，颜色可在 PPT 内修改。

---

# Slide 0 — Title / Meeting Objective

## Title

```text
Waymo Open Sim Agents Challenge:
Task Understanding and Research-Oriented Initial Plan
```

## Subtitle

```text
Using WOSAC as a benchmark to study realistic sim-agent design for autonomous driving
```

## Goal of this meeting

```text
1. Introduce the Waymo Sim Agents task and its role in autonomous-driving simulation.

2. Frame the challenge as a research benchmark, not only a leaderboard competition.

3. Discuss whether it is a suitable training/research task for building autonomous-driving foundations.

4. Propose an initial roadmap for finding and optimizing one sim-agent design problem.

5. Identify key risks, decisions, and a realistic first milestone.
```

## Bottom sentence

```text
This project uses the challenge as a benchmark platform to design better sim agents, not merely as a competition submission.
```

## 配图建议 / Visual

- 右上角小尺寸放 `slides/assets/waymo-logo.svg`（白色文字 logo，建议在深色封面上使用）。
- 不放主视觉图，避免分散对"研究定位"这一核心信息的注意力。

## 口头讲法

> 今天我想讨论的是 Waymo Open Sim Agents Challenge。但我的目标不是单纯完成竞赛或者冲 leaderboard，而是把它作为一个标准化 benchmark，用来学习自动驾驶中的 simulation、behaviour modelling 和 multi-agent interaction，并尝试找到一个值得优化的 sim-agent 模型设计问题。

---

# Slide 1 — Motivation: Why I Choose This Challenge

## Title

```text
Motivation: Building Research Foundations for Autonomous Driving
```

## Slide content

```text
Why this task?

- I want to build practical foundations for autonomous driving research and engineering.

- Sim agents are closely related to:
  - behaviour modelling
  - motion prediction
  - multi-agent interaction
  - planning evaluation
  - safety-critical simulation

- My goal is not simply to compete, but to use this benchmark to identify and optimize a meaningful sim-agent design problem.
```

## Key message

```text
I treat this challenge as a research platform, not only as a competition.
```

## 口头讲法

> 我选择这个题不是因为它只是一个比赛，而是因为它能系统训练自动驾驶行业中非常核心的能力：预测、仿真、多智能体交互、行为建模和 planning evaluation。我的目标不是追求一个很高的比赛排名，而是在这个 benchmark 里找到一个明确的建模问题并尝试优化。

---

# Slide 2 — Background: Why Realistic Simulation Matters

## Title

```text
Background: Why Realistic Simulation Matters
```

## Slide content

```text
Autonomous driving systems are difficult to evaluate only through real-world driving.

Simulation provides a scalable way to:
- test rare or risky scenarios
- evaluate planning and behaviour models
- study multi-agent interactions
- reduce real-world testing cost

However, simulation is useful only if the surrounding agents behave realistically.
```

## Bottom sentence

```text
The key problem is not replaying logs, but generating realistic interactive traffic behaviour.
```

## 配图建议 / Visual

- 右半页放 `slides/assets/home-anim-transparent.webm`（或转码后的 `home-anim.mp4` / `home-anim.gif`），作为"真实自动驾驶在复杂交通中行驶"的氛围图。
- 该视频是透明背景，建议放在浅色或纯色 slide 背景上效果最佳。
- ⚠️ 如果要在 Windows 版 PowerPoint 上放映，先用上面的 ffmpeg 命令转成 mp4 或 gif，否则可能黑屏。
- 备用方案：截取该视频的一帧静态图作为 PNG 配图也可以。

## 口头讲法

> 自动驾驶系统很难完全依靠真实道路测试来评估，因为真实测试成本高、风险高，而且很多极端场景很少出现。因此 simulation 非常重要。但 simulation 有价值的前提是：周围的车辆、行人、骑行者必须表现得足够真实。如果 surrounding agents 的行为不真实，那么对 planning 或 behaviour model 的评估也不可靠。

## 来源依据

WOSAC 论文明确指出，realistic, interactive agents 是自动驾驶软件开发中的关键任务，WOSAC 的目标是推动 realistic simulators 的设计，用于评估和训练自动驾驶 behaviour model。([Waymo][1])

---

# Slide 3 — Task Definition: Simulating the Future Traffic World

https://waymo.com/open/challenges/2025/sim-agents/

## Title

```text
Task Definition: Simulating the Future Traffic World
```

## Recommended layout

左右两栏，中间一个箭头流程图。

### Left side — Input

```text
Input: Past driving scene

Past 1 second:
- vehicle states
- pedestrian / cyclist states
- autonomous driving vehicle state
- road map
- lane structure
- traffic lights
```

### Center

```text
Past 1s scene + map
        ↓
Sim-agent model
        ↓
32 rollouts × 8s future
```

### Right side — Output

```text
Output: Future traffic evolution

Future 8 seconds:
- all vehicles
- pedestrians
- cyclists
- autonomous driving vehicle

Generate 32 possible futures per scenario.
```

## Bottom sentence

```text
The model acts as a traffic world simulator: it generates how the whole scene evolves, not only one predicted trajectory.
```

## 配图建议 / Visual ⭐ 主视觉

- **核心配图**：在右半页或下方放 `slides/assets/demonstrate.gif`。
  - 这张 GIF 直接展示了 sim agent 输出的样子：每辆车（黄/蓝色 box）有 heading + position，在路口逐帧演化。
  - 它能让导师"一眼看懂"任务，比文字描述效率高得多。
- 推荐布局：左侧放 Input → Sim-agent → Output 流程文字；右侧放 GIF。
- GIF 在 PowerPoint 放映时会自动循环，无需额外配置。
- 可在 GIF 下方加一行 caption："Example rollout: each box is a simulated agent (position + heading) over 8 seconds."

## 口头讲法

> 通俗地讲，这个任务就是训练一个交通世界模拟器。给它一个真实道路场景的过去约 1 秒历史，比如车在哪里、速度是多少，行人在哪里，骑行者在哪里，地图上有什么车道线、路口和红绿灯。然后模型要生成未来 8 秒整个交通世界如何发展。重点是，它不是只生成一个未来，而是生成 32 个可能未来，因为真实世界本身不是 deterministic 的。
> （指着 GIF）右边这个就是一个 rollout 的可视化效果，你可以看到所有 agent 的 box 在每个 step 都在更新位置和朝向。

---

# Slide 4 — Research Framing: From Competition Task to Sim-Agent Design Problem

## Title

```text
Research Framing: From Competition Task to Sim-Agent Design Problem
```

## Slide content

```text
This project is not primarily about winning the leaderboard.

Instead, I want to use the challenge as a controlled benchmark to study:

- What makes a sim agent realistic?
- Which failure mode is most important to improve?
- How can we design a better agent model for closed-loop traffic simulation?
- Can we improve one specific capability clearly and convincingly?
```

## Comparison box

```text
Competition objective:
submit 32 future rollouts per scenario

My research objective:
identify one key modelling weakness and optimize it into a strong sim-agent design
```

## Bottom sentence

```text
The challenge provides the dataset, simulator, metrics, and evaluation protocol; my contribution should be a focused sim-agent model improvement.
```

## 口头讲法

> 这一点是我想和老师明确讨论的：我不是把这个项目定义为“我要完成一个比赛”或者“我要做一个排名很高的模型”。我更想把它作为一个研究平台。它已经提供了数据、simulator、submission format 和评价方式，所以我可以在这个平台上寻找一个具体问题，比如 closed-loop stability、interaction realism 或 map adherence，然后围绕这个点设计一个更好的 sim agent。

---

# Slide 5 — Benchmark Platform: Data, Simulator, and Rollout Format

## Title

```text
Benchmark Platform: Data, Simulator, and Rollout Format
```

## Slide content

### Dataset

```text
Waymo Open Motion Dataset

Provides real-world driving scenarios:
- agent trajectories
- object types
- map features
- traffic light states
```

### Simulator / Framework

```text
Waymax simulator

Provides:
- scenario loading
- simulation state representation
- multi-agent rollout interface
- baseline agents
- submission generation
```

### Rollout format

```text
Each scenario requires:
- 32 simulated rollouts
- 8 seconds per rollout (80 steps @ 10 Hz)
- agent bounding boxes:
  x, y, z position + heading
- packaged as 150 serialized
  SimAgentsChallengeSubmission protos
- max 3 test-set attempts per 30 days
```

### Required factorization (2025 rule)

```text
The submission must follow a specific factorization:
- ADV (ego) model and world model are conditionally independent
  given the previous joint state.
- Object dimensions are fixed from the final history frame.
```

## 配图建议 / Visual

- **左上角**：放 `slides/assets/waymo-logo.svg`（小尺寸）作为 "数据来源" 标识。
- **下半部分 / 右栏**：放 `slides/assets/factorization.webp` —— 这张图正好对应上面的 "Required factorization" 子区，展示 S^ego_t 与 S^world_t 之间的条件独立结构。
  - 蓝色节点 = ego/ADV 状态序列；橙色节点 = world (其他 agent) 状态序列；左侧 c = 共享上下文（地图 + 历史）。
  - 图中的箭头说明：在 t+1 时刻，ego 的 next state 与 world 的 next state 都只依赖于 t 时刻的联合状态，但它们彼此**条件独立**。
- ⚠️ 如果导师电脑不是 Office 2021+，先把 webp 转 png（见顶部 ffmpeg 命令）。

## Bottom sentence

```text
This gives a standardized environment for testing whether a sim-agent design improves realism.
```

## 口头讲法

> 这个 benchmark 的好处是它不是一个完全开放、没有边界的问题。数据来自 Waymo Open Motion Dataset，仿真和评估可以基于 Waymax，最后输出的是生成好的 trajectory rollouts，而不是提交模型代码。也就是说，我可以把它看成一个标准化实验环境：输入场景、运行 sim agent、生成未来 rollouts，然后用统一指标评估 realism。
> （指着右图）这里有一个 2025 版本特别强调的要求：你的 ADV model 和 world model 在给定上一步联合状态后必须是**条件独立**的——也就是不能让 ego 的预测在同一步内"偷看" world 的预测结果。这张图就是 Waymo 官方对这个 factorization 的可视化。

## 来源依据

Waymax 官方介绍说明，它是一个用于 simulating and evaluating agents 的库，场景来自 Waymo Open Motion Dataset，并使用 WOMD 的 object / bounding-box 表示；Waymax GitHub 也说明它支持 closed-loop simulation、planning、sim-agent research 和 open-loop behavior prediction。([Waymo][2])
2025 challenge 页面明确要求 submission 遵循 ADV/world 的条件独立 factorization，且提交格式为 150 个 serialized proto 的 .tar.gz，每 30 天最多 3 次 test-set 提交。

---

# Slide 6 — Evaluation: Distribution Matching as Research Feedback

## Title

```text
Evaluation: Distribution Matching as Research Feedback
```

## Slide content

```text
The evaluation does not only check trajectory error.

It asks whether generated rollouts match the distribution of real driving behaviour.
```

## Concept diagram

```text
32 generated futures
        ↓
simulated behaviour distribution
        ↓
compare with real driving data distribution
```

## Evaluation dimensions

```text
1. Motion realism (kinematic)
   - linear speed / acceleration
   - angular speed / acceleration
   - 2025: smoother estimation for higher precision

2. Interaction realism
   - collision  (2025: capsule shapes, not square boxes)
   - distance to nearest object
   - time-to-collision (vehicles only;
                        2025: new filter applied)

3. Map adherence
   - off-road behaviour
   - distance to road edges
   - traffic-light violation (2025: NEW metric, vehicles only)
```

## Aggregation

```text
Per-feature negative log-likelihood
        ↓
weighted-mean meta-metric
        ↓
higher = more realistic
```

## 配图建议 / Visual

- 这张 slide 信息量已经很大，建议**不放图**，保持留白和可读性。
- 如果一定要配图，可以在左下角放小尺寸 `slides/assets/waymo-logo.svg` 作为来源标识。
- 替代方案：自己用 matplotlib 画一张"32 rollouts → distribution → compare"的示意图（不在现有素材里，按需绘制）。

## Bottom sentence

```text
These metrics can guide the research focus: interaction, map adherence, closed-loop stability, or multimodal behaviour.
```

## 口头讲法

> 这里最重要的是：它不是普通 trajectory prediction，不只是看预测点和真实点之间的误差。它更像是 distribution matching。模型生成 32 个未来，形成一个模拟出来的未来行为分布，然后评价这个分布和真实驾驶数据分布有多接近。所以这些指标不仅是比赛评分，也可以帮助我诊断模型到底哪里不真实。
> 顺便提一下 2025 版本相对于早期版本有几处更新：碰撞检测从方框改为 capsule、新增了 traffic-light violation 指标、time-to-collision 加了 filter，kinematic 估计也更平滑。所以引用早期 paper 的 baseline 数字时需要注意分数不可直接对比。

## 来源依据

WOSAC 论文提出了对应的 metrics，用于评估 realistic sim agents；相关工作也把 WOSAC 的 realism 评价概括为对 kinematic、interactive 和 map-based features 的 distribution matching。([arXiv][3])
2025 challenge 页面记录了上述 metric 更新，且说明旧 leaderboard 的分数为"更新前"的版本，新旧不可直接对比。

---

# Slide 7 — Candidate Optimization Points for This Project

## Title

```text
Candidate Optimization Points for This Project
```

## Slide content

### Direction A — Closed-loop stability

```text
Problem:
small one-step errors accumulate over 80 steps

Possible focus:
train a model that remains stable during long autoregressive rollout
```

### Direction B — Interaction realism

```text
Problem:
independent agent prediction can cause collisions or unrealistic yielding

Possible focus:
agent-agent attention or graph-based interaction modelling
```

### Direction C — Map adherence

```text
Problem:
agents may drift off-road or violate lane / traffic constraints

Possible focus:
map-conditioned decoding or constraint-aware rollout
```

### Direction D — Multimodal generation

```text
Problem:
one deterministic future cannot represent real-world uncertainty

Possible focus:
latent-variable / mixture / token-based sampling for diverse rollouts
```

## Bottom sentence

```text
The project should select one of these directions as the main contribution, rather than trying to solve the whole challenge.
```

## 口头讲法

> 我现在不想一开始就说我要做一个完整、很大的模型。更合理的方式是先把 benchmark 跑通，然后诊断 baseline 到底失败在哪里。之后选择一个最值得优化的点，比如 closed-loop stability、interaction realism、map adherence 或 multimodal generation。这样最后的项目贡献会更清楚。

---

# Slide 8 — Proposed Initial Focus: Stable and Interaction-Aware Sim Agents

## Title

```text
Proposed Initial Focus: Stable and Interaction-Aware Sim Agents
```

## Slide content

```text
Initial hypothesis:

A good sim agent should not only predict the next position accurately.
It should remain stable and socially plausible during closed-loop rollout.
```

## Possible research focus

```text
- autoregressive sim-agent model
- agent-agent interaction encoding
- map-conditioned state update
- loss terms targeting collision / off-road / smoothness
```

## Bottom sentence

```text
The first research goal is to design a sim agent that improves closed-loop realism, not simply open-loop prediction accuracy.
```

## 口头讲法

> 我目前倾向于把初始重点放在 closed-loop stability 和 interaction realism 上。因为 sim agent 的本质不是只在 open-loop 下预测下一步准不准，而是在 80 个 step 的 rollout 中，整个场景是否还能保持稳定、合理、不撞、不漂移，并且 agent 之间的交互是否像真实交通。

---

# Slide 9 — Proposed Roadmap

## Title

```text
Proposed Roadmap
```

## Slide content

```text
Stage 1: Understand data, metrics, and rollout format

Stage 2: Reproduce Waymax baseline pipeline

Stage 3: Diagnose baseline failure modes

Stage 4: Select one research focus

Stage 5: Design improved sim-agent model

Stage 6: Compare against simple baselines

Stage 7: Analyse improvements and limitations
```

## Bottom sentence

```text
The roadmap is diagnosis-driven: first understand failures, then design a focused improvement.
```

## 口头讲法

> 我不想直接跳到复杂模型。更稳妥的路线是：先理解数据和指标，跑通 Waymax pipeline，然后用简单 baseline 暴露问题。比如它是 off-road 严重，还是 collision 多，还是 rollout 不稳定。找到问题以后，再选择一个明确方向进行模型设计。

---

# Slide 10 — Phase 1A: Understand the Data and Run the Official Tutorial (Steps 1–2)

## Title

```text
Phase 1 · Steps 1–2: understand the data, run the official tutorial
```

## Slide content

### Step 1 — Understand the data and task format

```text
Dataset: Waymo Open Motion Dataset v1.2.0
Per scenario:
  - 9.1 s @ 10 Hz  →  ~1.1 s history + 8 s future = 80 simulation steps
  - up to 128 agents, one is the AV / ADV
  - object types: vehicle, pedestrian, cyclist
  - past trajectories, current state, map features, traffic lights

First-week target — read one scenario and visualise it:
  - past trajectories per agent
  - lane / road / crosswalk geometry
  - traffic-light states
  - current frame marker
```

> Note: WOMD is large. Skip downloading the full dataset for now and start with Step 2 — Waymax handles loading.

### Step 2 — Run the official Waymax tutorial → first valid submission

```text
Use a baseline agent (constant speed / replay / simple rule-based)
and follow the official WOSAC submission tutorial.

The tutorial handles:
  - scenario id, Waymax dataloader
  - proto format, sharding
  - SimAgentsChallengeSubmission packaging

Output per scenario:
  - 32 rollouts × 80 steps × all valid agents
  - x, y, z, heading per (agent, step)

Final artefact:
  - SimAgentsChallengeSubmission proto
  - binary shards
  - .tar.gz with 150 protos
```

## Bottom sentence

```text
Goal of this step is not score — it is a working pipeline that produces a legal submission.
```

## 配图建议 / Visual

- 左侧：Step 1 数据描述 + 一张小的"scenario 9.1s 时间轴"图（手绘 ASCII 也行）。
- 右侧：Step 2 流程图 — `WOMD scenario → Waymax loader → baseline agent → SimAgentsChallengeSubmission.tar.gz`
- 不放大图，重点是双 step 的清晰排版。

## 口头讲法

> 第一阶段的第一步是搞清楚 data 和任务格式。WOMD v1.2.0 每个 scenario 是 9.1 秒 10 Hz，大约 1.1 秒历史加 8 秒未来，对应 80 个 simulation step，每个 scenario 最多 128 个 agent，其中一个是 AV/ADV。我的目标不是马上训练，而是能把一个场景读出来、画出来。
> 但这个数据集体量很大，更稳的方式是从 Step 2 开始。直接跟 Waymax 的 tutorial 跑通一遍——用 constant speed 这种 baseline agent 生成 32 个 rollout、每个 80 步，按官方格式打包成 .tar.gz。这一步只关心 pipeline 走通和 submission 合法。

## 来源依据

WOSAC 论文说明每个 scenario 9.1 秒、10 Hz、最多 128 agents、ADV 1 个；Waymax tutorial 是官方教学如何生成 WOSAC submission。([ar5iv][3], [Waymo Research][2])

---

# Slide 11 — Phase 1B: Three Baselines + First Learned Model (Steps 3–4)

## Title

```text
Phase 1 · Steps 3–4: three baselines and the first learned model
```

## Slide content

### Step 3 — Three simple baselines

```text
Baseline 1 — Log replay
  Copies the recorded future as the simulated future.
  Sanity-checks the pipeline. Invalid for the test set
  (no future is given there).

Baseline 2 — Constant velocity
  Each agent extrapolates its current speed in a straight line.

Baseline 3 — Simple interaction rules
  Vehicles keep lane, brake on lead car proximity.
  Pedestrians / cyclists use simple speed models.
```

```text
Purpose: not to win — to read the metric.
e.g. Constant velocity often looks fine on motion realism
     but fails on off-road / collision / red-light violation.
```

### Step 4 — First learned model

```text
Adapt a trajectory-prediction model.

Input:
  - past 1 s agent states
  - vector map features
  - agent type
  - relative agent positions
  - traffic-light state

Output:
  - next-step Δx, Δy, Δheading  (or short-horizon distribution)

Training: scene state → next-state distribution
Rollout: loop 80 times
  observe simulated scene
  predict ADV next state
  predict world agents next state
  update scene
```

> WOSAC requires that the ADV and world predictors be conditionally independent given the previous joint state — see Slide 5.

## Bottom sentence

```text
By the end of Phase 1: working pipeline, three baselines scored, one learned model trained.
```

## 配图建议 / Visual

- 左侧：三种 baseline 的小图标 + 一行简介（log replay / const-vel / rule-based）。
- 右侧：learned model 的 training-vs-rollout 双列伪代码。
- 底部 callout：autoregressive factorization 受 WOSAC 规则约束。

## 口头讲法

> 第三步是建立三个 baseline。第一个是 log replay，把真实 future 当作生成 future——它不能用于 test set，但是验证 pipeline 很好用。第二个是 constant velocity——每辆车按当前速度直线走。第三个是简单的 interaction rule——保持车道、跟车减速、行人匀速。这三个 baseline 的意义不是赢比赛，而是帮助我读懂评分系统：constant velocity 在 motion 上可能还行，但容易 off-road、collision、闯红灯。
> 第四步是第一个 learned model。可以从 trajectory prediction model 改造：输入过去 1 秒 agent state、vector map、agent type、相对位置、红绿灯；输出下一步 Δx Δy Δheading。训练目标是 scene → next-state distribution，rollout 时循环 80 次，每一步分别预测 ADV 和 world agent 的下一状态——并且要遵守 WOSAC 的条件独立 factorization。

---

# Slide 12 — Phase 2: From Single-Agent Prediction to Joint Multi-Agent Simulation

## Title

```text
Phase 2: design a focused sim-agent model — single-agent prediction → joint multi-agent simulation
```

## Slide content

### From Step 5 — the real difficulty

```text
The hard part is not predicting one car.
It is making all agents jointly plausible:
  - agent–agent interaction
  - vehicle vs pedestrian yielding
  - car following
  - lane keeping
  - traffic-light compliance
  - multimodal future (multiple plausible outcomes)

If each agent is predicted independently,
two cars frequently collide.

WOSAC requires realistic interactive behaviour,
not log playback or simple rules.
```

### Reasonable model recipe

```text
Vectorized map encoder
Agent history encoder
Agent–agent attention / GNN
Stochastic latent / diffusion / autoregressive decoder
Map constraint / collision-aware post-processing
```

## Model diagram

```text
Scene state (agent history + map + lights)
        ↓
Map encoder + history encoder
        ↓
Agent–agent interaction module (attention / GNN)
        ↓
Stochastic decoder
        ↓
Next simulated scene state
        ↓ (repeat × 80)
```

## Bottom sentence

```text
Success = a clear design improvement on one capability — not a top leaderboard score.
```

## 配图建议 / Visual

- 顶部：单 agent 预测 vs 多 agent 联合预测对比示意（两辆车撞在一起 vs 互相避让）。
- 中间：模型 5 段流水线 (encoder → interaction → decoder → constraint → loop)。
- 不引入新图像；用形状构造即可。

## 口头讲法

> Phase 2 的核心难点不是某辆车的预测，而是所有 agent 必须 *联合* 合理。如果独立预测每个 agent，常常会出现两个车撞在一起、车辆压到行人、或者无人让车。论文也明确说，sim agents 需要 realistic 和 interactive behavior，不能只是 log replay 或简单规则。
> 我倾向的模型路线是：vectorized map encoder + agent history encoder → 一个 agent–agent interaction module（attention 或 GNN） → stochastic decoder（latent variable / diffusion / autoregressive） → map constraint 或 collision-aware 的 post-processing。这一阶段成功的标准不是 leaderboard 第一，而是能在某一个能力上看到明确改进。

---

# Slide 13 — Phase 3: Evaluate the Design, Not Only the Score

## Title

```text
Phase 3: Evaluate the Design, Not Only the Score
```

## Slide content

```text
Compare against:
- constant-velocity baseline
- simple rule-based baseline
- initial learned baseline
```

## Analyse improvements in

```text
- motion realism
- interaction realism
- map adherence
- closed-loop stability
- diversity across 32 rollouts
```

## Key question

```text
Which failure mode does the proposed design reduce most clearly?
```

## Bottom sentence

```text
The final result should explain why the model works, where it improves, and where it still fails.
```

## 口头讲法

> 评价不应该只报告一个总分。更重要的是分析：我的设计到底改善了什么？比如它是否减少了 collision？是否减少了 off-road？是否让 80-step rollout 更稳定？是否生成了更多合理但不同的未来？这才更像一个研究项目，而不是单纯参赛。

---

# Slide 14 — Discussion Questions

## Title

```text
Discussion Questions
```

## Slide content

```text
1. Is this a suitable benchmark for building autonomous-driving research foundations?

2. Which research focus is most valuable?
   - closed-loop stability
   - interaction realism
   - map adherence
   - multimodal generation

3. Should I start with rule-based diagnosis or a learned baseline?

4. What would be a convincing 4–6 week milestone?

5. What kind of final output would be most useful?
   - working simulator pipeline
   - improved sim-agent model
   - failure-mode analysis
   - short technical report
```

## Bottom sentence

```text
The goal of this meeting is to align on scope, focus, and first milestone.
```

## 口头讲法

> 我希望这次 meeting 的结果不是决定我要不要“参加比赛”，而是帮我确定这个 benchmark 是否适合作为训练/研究任务，以及我应该优先优化哪个具体方向。比如是先做 closed-loop stability，还是 interaction realism，还是 map adherence。

---

# Slide 15 — References

## Title

```text
References
```

## Slide content

```text
[1] Montali et al., The Waymo Open Sim Agents Challenge.

[2] Gulino et al., Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research.

[3] Waymo Open Dataset 2025 Sim Agents Challenge webpage.
    https://waymo.com/open/challenges/2025/sim-agents/

[4] Waymax WOSAC submission tutorial.

[5] Waymo Open Dataset Sim Agents tutorial.

[6] Recent WOSAC 2025 technical reports.
```

## 配图建议 / Visual

- 顶部或角落放 `slides/assets/waymo-logo.svg`，作为参考资料的视觉锚点。
- 不需要其他配图。

## 口头讲法

> 这些是我接下来会重点阅读和复现的资料。中间 slides 不单独讲论文，而是把论文里的任务定义、benchmark 设计和 simulator 框架融入到了前面的介绍中。

---

# 最终 PPT 目录

```text
0. Title / Meeting Objective

1. Motivation: Why I Choose This Challenge

2. Background: Why Realistic Simulation Matters

3. Task Definition: Simulating the Future Traffic World

4. Research Framing: From Competition Task to Sim-Agent Design Problem

5. Benchmark Platform: Data, Simulator, and Rollout Format

6. Evaluation: Distribution Matching as Research Feedback

7. Candidate Optimization Points for This Project

8. Proposed Initial Focus: Stable and Interaction-Aware Sim Agents

9. Proposed Roadmap

10. Phase 1A — Steps 1–2: Understand the data, run the official tutorial

11. Phase 1B — Steps 3–4: Three baselines + first learned model

12. Phase 2: From single-agent prediction to joint multi-agent simulation

13. Phase 3: Evaluate the design, not only the score

14. Discussion Questions

15. References
```

---

# 你这套 PPT 的核心叙事

你整场 meeting 应该围绕这条线讲：

```text
我想进入自动驾驶方向
        ↓
sim agents 是自动驾驶仿真和评估中的重要基础能力
        ↓
Waymo WOSAC 提供了标准数据、simulator、rollout format 和评价指标
        ↓
但我的目标不是冲榜，而是把它作为研究平台
        ↓
先复现和诊断 baseline
        ↓
再选择一个优化点：
closed-loop stability / interaction realism / map adherence / multimodal generation
        ↓
设计一个 focused sim-agent model
        ↓
用指标和 failure analysis 证明它确实改善了某个能力
```

这一版比“介绍竞赛 + 做步骤”更高级，因为它明确告诉导师：你不是在做一个零散比赛，而是在把竞赛题转化成一个有边界、有评价、有研究切入点的项目。

[1]: https://waymo.com/research/the-waymo-open-sim-agents-challenge/?utm_source=chatgpt.com "The Waymo Open Sim Agents Challenge"
[2]: https://waymo.com/research/waymax/?utm_source=chatgpt.com "Waymax: An Accelerated, Data-Driven Simulator forLarge- ..."
[3]: https://arxiv.org/abs/2305.12032?utm_source=chatgpt.com "[2305.12032] The Waymo Open Sim Agents Challenge"
