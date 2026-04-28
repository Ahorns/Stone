# Phase 1A · Step 2 — 跑通官方 tutorial → 第一份合法 submission
# Run the official tutorial → first valid submission

## 这一步要做什么 / Goal

按 Waymax 官方教程把整个 WOSAC 提交流程从头到尾走一遍。**这一步只关心 pipeline 通不通、文件格式对不对，不关心分数。** 分数是 Step 3 的事。
>这个tutorial就是基于这个模拟器waymo为了竞赛,教我们怎么把 Waymo 的场景数据读出来，生成合法的 sim-agents 预测结果，并用官方流程进行检查和评分。waymax 是waymo题目自己搞的向量模拟器,是更高级的做题平台 / 训练平台; tutorial 和 Waymax 不是替代关系，而更像是：tutorial 让你先学会规则,Waymax 让你以后大规模高效地做

Reproduce the official WOSAC submission pipeline end-to-end with a baseline policy. Score doesn't matter; correctness of the pipeline does.

---

## 这个文件夹里有什么 / Folder contents

```
run_tutorial.py                      ← 入口脚本 / entry-point
outputs/
├── viz/                             ← 可视化 PNG（共 6 张）
│   ├── scenario_map.png             场景地图 + 当前帧所有 agent 的位置
│   ├── sim_agents_tracks.png        高亮哪些 agent 需要被模拟
│   ├── simulated_trajectories.png   线性外推得到的 32 条 rollout 叠加在地图上
│   ├── kinematic_features.png       每个 agent 的速度/加速度分布
│   ├── interactive_features.png     碰撞 / TTC（time-to-collision）分布
│   └── map_features.png             越界 / 距路沿的分布
└── submissions/
    ├── submission.binproto-00000-of-00150     这个 shard 对应的 binary proto
    └── submission.tar.gz                       打包后的 WOSAC 提交格式
```

---

## `run_tutorial.py` 做了什么 / What the script does

跟着 [Waymax 官方 sim-agents tutorial](https://github.com/waymo-research/waymo-open-dataset/blob/master/docs/sim_agents_tutorial.md) 一步一步走：

1. **加载 shard**（这里是 `../1_understand_data/data/validation.tfrecord-00000-of-00150`）
2. **对每个 scenario：**
   - 解析 protobuf
   - 用 `submission_specs.get_sim_agent_ids` 找出哪些 agent 需要模拟
   - 用 **linear extrapolation（线性外推 / 等同于 constant velocity）** 当 baseline policy
     —— 每个 agent 按当前速度直线走 80 步
   - 生成 32 个 rollout（这里是 32 份完全相同的外推，**没有加噪声**，所以多样性为零）
   - 用 `submission_specs.validate_scenario_rollouts` 验证格式合法
   - 调 WOSAC 官方 `compute_scenario_metrics_for_bundle` 算 SimAgentMetrics
3. **打包**：所有 32-rollout × 286-scenario 结果合并成 `submission.tar.gz`

Following the [official Waymax sim-agents tutorial](https://github.com/waymo-research/waymo-open-dataset/blob/master/docs/sim_agents_tutorial.md): load shard → parse → linear-extrapolation rollouts → validate → score → package.

---

## 关键数字 / Headline numbers

| 指标 | 数值 |
|---|---|
| 处理的 scenario 数 | 286（一个 shard） |
| 每个 scenario 的 rollout 数 | 32 |
| 每个 rollout 的步数 | 80（8 秒 × 10 Hz） |
| 这个 baseline 的 metametric | 约 0.29，**和论文里 Constant Velocity 的 0.287 基本一致** |
| 提交文件大小 | `submission.tar.gz` ≈ 660 KB |

> **重要说明**：这只是 **150 个 shard 中的 1 个**，所以这个 `submission.tar.gz` 还不是一个完整的 WOSAC 提交。但格式正确，跑全 150 个 shard 再合并就可以提交。Phase 1 只验证 pipeline，正式提交是 Phase 2/3 的事。

---

## 这一步为什么重要（给老师汇报时用）/ Why this matters

它**同时验证了两件事**：

1. **数据 pipeline 是通的。** 我们能打开 WOMD scenario、解析它、模拟 agent、生成合法的提交 proto。后面 Step 3、Step 4 的不同策略可以直接套到同一个 harness 上。

2. **Metric 实现和官方对得上。** 线性外推在我们这边算出来 metametric ≈ 0.29，论文里 Constant Velocity 的参考分是 0.287。两边几乎一致，说明我们用的 metric 计算流程是正确的。后面 Step 3、Step 4 报出来的分数可以放心相信。

This step validates two things at once: (1) the data pipeline works end-to-end and produces a legal submission proto, and (2) our metric implementation matches Waymo's published reference (0.29 vs 0.287 for constant velocity).

---

## 这一步用到的源代码 / Source files used

| 文件 | 用途 |
|---|---|
| `run_tutorial.py` | 入口脚本（用到了 `code/darwin_waymo/features/` 和 `code/darwin_waymo/submission/`） |

---

## 接下来 / What goes next

**Step 3** 把 linear-extrapolation 换成 **三个有结构的 baseline**（log replay / constant velocity / rule-based），用同一个 metric harness 在 15 个 scenario 上打分，看每种 baseline 在哪个轴上失败得最厉害 —— 这是 diagnostic（诊断）的核心。

Step 3 swaps linear extrapolation for **three structured baselines** and scores them on the same harness across 15 scenarios — to diagnose which capabilities each baseline fails on.
