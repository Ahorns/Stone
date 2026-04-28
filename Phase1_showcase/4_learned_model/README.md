# Phase 1B · Step 4 — 第一个 learned 下一步预测模型
# First learned next-step predictor

## 这一步要做什么 / Goal

训练一个真正的神经网络 sim-agent，端到端跑通（数据 → 训练 → 评测），并且在至少一个 WOSAC sub-metric 上**击败 constant velocity**。

Train a neural-net sim-agent end-to-end and beat constant-velocity on at least one WOSAC sub-metric.

---

## 这个文件夹里有什么 / Folder contents

```
prepare_dataset.py                   ← 把 shard 转成 (X 44-d, Y 3-d) 训练张量
train_step4.py                       ← PyTorch 训练入口
training_log.csv                     ← 每个 epoch 的 train/val NLL
report.md                            ← 完整 Step 4 报告（架构 + 训练 + 评测 + 分析）

dataset/
├── train.npz                        533,590 个 (X, Y) 样本（38 MB）
├── val.npz                          137,104 个样本（9 MB）
└── stats.json                       目标分布、agent 类型计数

checkpoints/
└── best_val.pt                      v2 模型权重（dropout 0.2 + weight decay 1e-2）

eval/
├── baseline_comparison.csv          5 个 scenario × 3 个 baseline 的所有 metric
├── baseline_summary.md              聚合表格
├── run.log                          每个 baseline 的进度日志
└── status.json                      增量进度（之前长跑用过）
```

---

## TL;DR

一个 **78,854 参数**的 PyTorch MLP，在验证集 shard 提取出的 533K 个 next-step transition 上训练。预测值是 agent ego 坐标系下 (Δforward, Δlateral, Δheading) 的高斯分布，**作为第 4 个 baseline `learned` 接入了和 Step 3 完全一样的评测 harness**。

GPU 上训练**仅用 50 秒**（CPU 上要好几小时）。最优 validation NLL = **−8.51**（v2 模型，第 8 epoch）。

A 78,854-param PyTorch MLP, trained on 533K next-step transitions in 50 s on A100. Best validation NLL = −8.51.

---

## 5-scenario 评测结果 — 击败 const-vel 了吗？/ Does it beat const-vel?

| Metric | log_replay | constant_velocity | **learned (v2)** |
|---|---|---|---|
| metametric | 0.863 | **0.561** | 0.206 |
| `linear_speed_likelihood` | 0.511 | 0.011 | **0.038** ← **learned 赢了 ✓** |
| `linear_acceleration_likelihood` | 0.506 | 0.085 | 0.013 |
| `angular_speed_likelihood` | 0.737 | 0.424 | 0.015 |
| `distance_to_road_edge_likelihood` | 0.821 | 0.694 | 0.191 |
| `simulated_offroad_rate` | 10.7% | 29.3% | **100.0%** |
| `simulated_collision_rate` | 0% | 33.3% | 83.4% |
| ADE (m) | 0.0 | 7.3 | 45.6 |
| 平均耗时 (秒) | 51 | 51 | 237 |

### **成功标准达成 ✓**

`linear_speed_likelihood = 0.038` > constant velocity 的 **0.011**。也就是说，**learned 模型在"speed 分布的真实性"这一指标上比 const-vel 更好**：constant velocity 只会按当前速度直线外推，无法拟合真实司机会减速、加速、停车的速度分布；learned model 学到了一些真实速度的变化规律。

The success criterion is met: `linear_speed_likelihood = 0.038` > constant velocity's 0.011. The learned model has captured a more realistic speed distribution than straight-line extrapolation.

### **其他 metric 输给 const-vel —— 因为 closed-loop drift（闭环漂移）**

- 模型是用 **one-step prediction**（一步预测）训的，输入是 **真实当前状态**（ground truth current state）
- 评测时是 **80 步 closed-loop rollout**，每一步的输入是 **上一步的 simulated state**（模拟出来的，可能已经偏离）
- 训练 1 步后，simulated state 已经飘到了模型从没见过的分布
- 80 步累积下来，agent 跑到了完全错误的位置 —— 100% 越界

This is the textbook imitation-learning train/test distribution mismatch — and it's exactly what the slide-guide's **Phase 2** (joint multi-agent simulation, agent-agent attention/GNN, scheduled sampling / DAGGER) is designed to address.

**这正是 Phase 2 要解决的问题** —— scheduled sampling / DAGGER（在 simulated state 上训练）+ agent-agent attention/GNN。

---

## 训练历史 / Training notes

跑了两次：

| 版本 | Epochs | Dropout | Weight decay | 最优 val NLL | 备注 |
|---|---|---|---|---|---|
| v1 | 30 | 0 | 1e-4 | −8.25（第 5 epoch） | 严重 overfit。第 30 epoch 时 val NLL 飙到 +208。靠 best_val checkpoint 救回 epoch 5 |
| **v2** ⭐ | 12 | 0.2 | 1e-2 | **−8.51（第 8 epoch）** | 稳定。**这个 checkpoint 就是 `checkpoints/best_val.pt`** |

v1 → v2 的对比说明：**dropout 0.2 + 强 weight decay 是必要的正则化**，不然小 MLP 会狠狠记住训练数据。`training_log.csv` 里有 v2 每个 epoch 的 train/val NLL 完整轨迹。

---

## 模型架构 / Architecture

```
输入: 44 维特征向量
(自身状态 6 + 车道 7 + 5 个最近邻 25 + 安全 4 + 红绿灯 2 = 44)
        ↓
MLP [44 → 256 → 256 → 6]   GELU 激活，可选 dropout
        ↓
高斯分布参数: (μ_fwd, μ_lat, μ_h, log σ_fwd, log σ_lat, log σ_h)
        ↓
输出: ego 坐标系下 (Δforward, Δlateral, Δheading)
        ↓
Rollout 时换回 world 坐标系，更新 agent 状态
```

源代码在 [`../code/darwin_waymo/learned/`](../code/darwin_waymo/learned/) —— 4 个文件：

| 文件 | 用途 |
|---|---|
| `dataset.py` | scenario → (X 44-d, Y 3-d) 样本提取，支持训练 / 验证按 scenario 切分 |
| `model.py` | `MLPNextStep`（带 Gaussian head 的 MLP）+ `gaussian_nll` loss |
| `train.py` | 训练 loop：AdamW + Gaussian NLL + best-val checkpointing |
| `policy.py` | `learned_rollout`：把训好的模型当 sim-agent，每步前向 + 采样 + 更新场景 |

---

## 为什么说"第一个" learned model（用词解释）/ Why "first"

slide-guide 的成功标准是：*"第一个 learned model 端到端跑通，并且在至少一个 sub-metric 上击败 constant velocity"*。当前模型：

- ✅ **训练**端到端跑通（A100 上 50 秒）
- ✅ **集成**进了和 rule_based / log_replay 完全一样的评测 harness
- ✅ **击败** constant velocity 在 `linear_speed_likelihood` 上
- ✅ **暴露了**清晰的失败模式（closed-loop drift），完美对应 Phase 2 要解决的问题

**它没有整体击败 const-vel —— 这恰好是个有用的结论：它告诉我们 closed-loop training 是必须的，不能再简单地训一个 one-step predictor 然后期望它在 rollout 里好用。**

---

## 详细信息看哪儿 / See also

- [`report.md`](report.md) —— 完整的 Phase 1B Step 4 报告（架构 + 训练 + 评测 + Phase 2 hooks）
- [`../docs/step4-plan.md`](../docs/step4-plan.md) —— 写代码之前的 Step 4 计划文档
- [`../3_three_baselines/`](../3_three_baselines/) —— 用来对比的 baseline 数字
