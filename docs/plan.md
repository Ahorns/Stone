# 写在前面
## 1. 这个训练题目到底要求做什么？

>(这部分可以是你给老师讲述你毕设背景的第一个部分,简单又清晰地介绍一下这个)

通俗讲，它要你训练一个“交通世界模拟器”。

给你一个真实道路场景，例如：

```text
过去 1 秒：
车 A 在这里，速度这样
车 B 在旁边
行人在路口
骑行者在右侧
地图上有车道线、路口、红绿灯等
```

你的模型要生成未来 8 秒：

```text
未来 8 秒：
车 A 怎么开
车 B 怎么让/怎么跟车
行人怎么走
骑行者怎么移动
自动驾驶车 ADV 怎么走
```

而且不是只生成一个答案，而是生成 **32 种可能未来**。因为真实世界不是 deterministic(确定的) 的，同样的过去 1 秒，未来可能有多种合理发展。例如前车可能加速、减速、变道，行人可能继续走或停下。Waymo 把这个问题定义成 **distribution matching(分布匹配)**：你的模拟结果分布越接近真实驾驶数据分布，分数越高。([Waymo][1])

你提交的不是模型代码，而是生成好的轨迹文件。每个场景需要提交 32 个 8 秒 rollout，每个 rollout 里面包含 agent 的 bounding boxes，也就是 x/y/z 位置和 heading。网页说提交格式是 serialized `SimAgentsChallengeSubmission` proto，每个 `ScenarioRollouts` 包含 32 个 8 秒 rollout；最后需要把 150 个 shard 压缩成一个 `.tar.gz` 上传。([Waymo][1])
>(这一段在说目标,暂时不用太管具体是什么)

它评分看三大类：

| 评分类别               | 它在看什么                     | 通俗解释                  |
| ------------------ | ------------------------- | --------------------- |
| Agent motion       | 速度、角速度、加速度、角加速度           | 车/人/骑行者动得像不像真实世界      |
| Agent interactions | 碰撞、最近距离、time-to-collision | agent 之间会不会合理避让、跟车、交互 |
| Map adherence      | 是否 off-road、离道路边界距离、是否闯红灯 | 有没有开出路外、是否遵守地图和红绿灯    |

这些指标最后会被聚合成 meta-metric，分数越高越好。([Waymo][1])

最关键的一点：它不是普通 motion prediction。普通预测可能是 open-loop：看过去，直接预测未来完整轨迹。但这个 challenge 要求 **autoregressive simulation**，也就是一步一步模拟，每一步都要基于之前模拟出来的新状态继续生成下一步。网页还要求模型分成两个部分：一个是 ADV 模型，一个是 world agents 模型，并且二者要满足特定的 factorization。([Waymo][1])

所以一句话总结：

> 这个题目要求你做一个能在 Waymo 场景中生成多 agent、交互式、随机但真实的未来交通行为模拟器，而不是单纯预测一条轨迹。

## 2. 页面里要求/推荐你读什么论文？

页面中明确提到两篇核心论文。

第一篇必须读：

**Montali et al., “The Waymo Open Sim Agents Challenge”, NeurIPS 2023 / 2024 proceedings version.**

这是最重要的题目定义论文。它解释了为什么不能只 replay log，为什么要做 sim agents，为什么评价方式是分布匹配，以及 autoregressive、closed-loop、多 agent simulation 和普通 trajectory forecasting 的区别。论文摘要里说，WOSAC 目标是推动 realistic simulators，用于 autonomous driving behavior model 的评估和训练。([ar5iv][3])
>(这段专有名词多,看[appendix1]有解释)

你读这篇时重点看：

```text
1. Introduction：为什么 sim agents 重要
2. Traffic Simulation as Conditional Generative Modeling：题目数学定义
3. Benchmark Overview：数据集、输入输出、提交格式
4. Evaluation：为什么用 NLL / distribution matching
5. Baselines：别人怎么做 baseline
```

第二篇强烈建议读：

**Gulino et al., “Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research”, NeurIPS 2023 / 2024 proceedings version.**

Waymo 页面推荐用 Waymax 来生成 submission。Waymax 是一个基于 Waymo Open Motion Dataset 的 accelerated simulator，支持 GPU/TPU 上的大规模 multi-agent simulation，也包含 learned 和 hard-coded behavior models。([ar5iv][4])

你读这篇时重点看：

```text
1. Waymax 的数据结构
2. simulator state 怎么表示
3. agent model 怎么接入
4. rollout 怎么做
5. 为什么它适合大规模仿真
```

第三个不是论文，但你必须看：

**Waymo / Waymax 官方 submission tutorial。**

这个教程直接教你如何用 Waymax 创建 WOSAC submission，并且代码里明确设置了 `CURRENT_TIME_INDEX = 10`、`N_SIMULATION_STEPS = 80`、`N_ROLLOUTS = 32`，这正好对应“过去约 1 秒历史 + 未来 8 秒 + 32 个 rollout”。([Waymo Research][5])

所以阅读优先级应该是：
>(**在你开会之前都可以暂时不看**)

```text
第一优先级：
The Waymo Open Sim Agents Challenge

第二优先级：
Waymax paper

第三优先级：
Waymax WOSAC submission tutorial / GitHub notebook

第四优先级：
Waymo Open Motion Dataset 文档和 proto 格式
```

## 3. 如果你开始做，步骤应该是什么？

我建议不要一上来就训练复杂模型。你应该按“能提交 → 能跑 baseline → 能训练模型 → 提升指标”的路线走。

### Step 1：先理解数据和任务格式

先下载 Waymo Open Motion Dataset，重点理解每个 scenario 里面有什么：
>(这个文件实在是太大了建议先从step2开始)
```text
agent past trajectory
agent current state
map features
traffic lights
object type: vehicle / pedestrian / cyclist
SDC / ADV 信息
```

WOSAC 使用的是 WOMD v1.2.0 数据，论文里说每个 scenario 是 9.1 秒、10 Hz：大约 1.1 秒 history 加 8 秒 future，未来 8 秒对应 80 个 simulation steps。每个场景最多要模拟 128 个 agents，其中一个是 AV/ADV。([ar5iv][3])

你第一步的目标不是训练，而是能把一个 scenario 读出来并可视化：

```text
读取一个场景
画出过去轨迹
画出地图
标出车辆、行人、骑行者
确认当前时刻是哪一帧
```

### Step 2：跑通官方 tutorial，生成一个合法 submission

这一步非常重要。先别管分数，先确保你能生成合法文件。

用 Waymax tutorial 的 baseline agent，例如 constant speed / replay / simple rule-based agent，生成：

```text
每个 scenario：32 个 rollout
每个 rollout：80 steps
每个 step：所有 valid agents 的 x/y/z/heading
```

官方教程就是为了教你如何生成 WOSAC submission。它会处理 scenario id、Waymax dataloader、proto 格式等细节。([Waymo Research][5])

这一步完成后，你应该能得到：

```text
SimAgentsChallengeSubmission proto
多个 binary shard
最终 .tar.gz
```

### Step 3：建立最简单 baseline

你可以先做三个 baseline：

```text
Baseline 1: log replay
直接复制真实未来，验证 pipeline，但 test set 不能这么做

Baseline 2: constant velocity
每个 agent 按当前速度直线走

Baseline 3: simple interaction rule
车辆保持车道，前车太近就减速，行人/骑行者用简单速度模型
```

这些 baseline 的意义不是赢比赛，而是帮你理解评分系统。比如 constant velocity 可能 motion 看起来还行，但容易 off-road、collision、红灯违规。

### Step 4：训练第一个 learned model

第一个可行 learned model 可以不用太复杂。建议从 trajectory prediction model 改造：

输入：

```text
过去 1 秒 agent states
地图 vector features
agent type
agent relative positions
traffic light state
```

输出：

```text
下一步或者未来短 horizon 的 delta x, delta y, delta heading
```

但注意 WOSAC 要 autoregressive，所以最好训练成：

```text
当前 scene state -> 下一步 state distribution
```

然后在 rollout 时循环 80 次：

```text
for t in 1..80:
    observe current simulated scene
    predict next state for ADV
    predict next state for world agents
    update scene
```

网页明确说，合法 submission 应该由两个 autoregressive components 产生：World 和 ADV，并且在给定所有 objects 状态时二者 conditionally independent。([Waymo][1])

### Step 5：从“单 agent prediction”升级到“joint multi-agent simulation”

这个 challenge 的难点不是预测某一辆车，而是所有 agent 要共同合理。

你需要考虑：

```text
agent-agent interaction
车和行人之间避让
车辆跟车
车道保持
红绿灯约束
多 modal future
```

如果只独立预测每个 agent，很容易出现两个车撞在一起。论文也指出，sim agents 需要 realistic, interactive behavior，不能只是 log playback 或简单 rule-based。([ar5iv][3])

所以比较合理的模型路线是：

```text
Vectorized map encoder
Agent history encoder
Agent-agent attention / graph neural network
Stochastic latent variable / diffusion / autoregressive decoder
Map constraint / collision-aware post-processing
```
>要去学习这些模型,这些模型更重要!!!!!这下面的都是实习工作要求的重点能力
```
Adversarial Agents 
多智能体博弈
Latent Variable Modeling
潜在变量建模
Hidden Markov Models (隐马尔可夫模型) 和 Probabilistic Modelling (概率建模)
```

### Step 6：针对评价指标优化

评分不是只看 ADE/FDE，所以你不能只优化轨迹误差。你要针对三类指标改模型：

```text
Motion:
速度、加速度要平滑，不能 sudden jump

Interaction:
减少 collision，保持合理距离，TTC 不要异常

Map:
不要 off-road，不要穿越不可行驶区域，不要闯红灯
```

2025 版本还加入了 traffic light violation metric，并且 time-to-collision metric 对 vehicle 有新的 filter。([Waymo][1])

所以你的训练 loss 可以包括：

```text
trajectory imitation loss
velocity / acceleration smoothness loss
off-road penalty
collision penalty
red-light violation penalty
diversity loss
```

### Step 7：生成 32 个多样但合理的 rollout

不要让 32 个 rollout 都一样。因为评分会用你的 32 个样本估计 simulated distribution，然后看真实 logged future 在这个分布下的 likelihood。网页说它会用 histogram 或 KDE 近似 32 个 simulation samples 的分布，再评估 logged sample 的 likelihood。([Waymo][1])

所以模型需要 stochasticity，例如：

```text
latent variable z
diffusion sampling
mixture decoder
temperature sampling
goal sampling
behavior mode sampling
```

但是 diversity 不能乱来。32 个未来要“有变化”，但都要合理。

## 最小可执行路线

如果你现在要开工，我建议按这个顺序：

```text
第 1 周：
读 WOSAC paper + 跑通 Waymax tutorial
目标：能读取数据、可视化 scenario、生成合法 submission

第 2 周：
实现 constant velocity / rule-based baseline
目标：理解 proto、rollout、evaluation 逻辑

第 3-4 周：
训练 next-step autoregressive imitation model
目标：能 rollout 80 steps，不崩，不大规模 off-road/collision

第 5-6 周：
加入 map encoder + agent-agent attention
目标：提升 interaction 和 map adherence

第 7 周之后：
加入 stochastic sampling / diffusion / multimodal decoder
目标：让 32 个 rollout 覆盖真实未来分布，提高 likelihood-based score
```

最核心的一句话是：

> 你要做的不是“预测未来轨迹”，而是“做一个能反复采样的真实交通世界模型”。它必须多 agent、交互式、autoregressive、stochastic，并且输出 32 个未来 8 秒场景。

[1]: https://waymo.com/open/challenges/2025/sim-agents/ "Sim Agents – 2025 – Waymo Open Dataset"
[2]: https://waymo.com/open/ "About – Waymo Open Dataset"
[3]: https://ar5iv.org/abs/2305.12032 "[2305.12032] The Waymo Open Sim Agents Challenge"
[4]: https://ar5iv.org/abs/2310.08710 "[2310.08710] Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research"
[5]: https://waymo-research.github.io/waymax/docs/notebooks/wosac_submission_via_waymax.html "Waymo Open Sim Agents Challenge Submission - Waymax documentation"
