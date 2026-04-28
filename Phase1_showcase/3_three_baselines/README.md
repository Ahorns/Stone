# Phase 1B · Step 3 — 三个 baseline 用官方 metric 打分
# Three baselines, scored on official WOSAC metrics

## 这一步要做什么 / Goal

建立 baseline 的"参考线"：用 WOSAC 官方 metric 给三种简单策略打分，看每种 baseline 在哪个能力上失败得最厉害。这是 Phase 1B 的**诊断（diagnostic）核心** —— Step 4 学习模型的目标就是要在这些 baseline 之上有所改进。

Establish a baseline picture under WOSAC scoring, so we know which capabilities a learned model has to beat.

---

## 这个文件夹里有什么 / Folder contents

```
run_baselines.py                     ← 评测脚本
results/
├── baseline_comparison.csv          每个 (scenario, baseline) 一行 — 共 45 行
├── baseline_summary.md              聚合后的 Markdown 表格（15 scenario 平均）
└── run.log                          每个 baseline 的进度日志（耗时、metametric）
```

---

## 三个 baseline / The three baselines

三种 baseline 都产出同样形状的输出：`(32, n_agents, 80, 4)` 的 numpy 数组 —— 32 个未来 × 80 步 × 所有 agent × `(x, y, z, heading)`。**用同一个 packaging 和 scoring harness**，所以差异只在策略本身。

| Baseline | 中文说明 | 32 条 rollout 之间的多样性 |
|---|---|---|
| **`log_replay`** | **日志回放**：直接把 ground-truth future 当作 simulated future（只能在 validation 上用，test 上无未来） | 无 —— 32 条完全一样。作为分布匹配的"上界"诊断 |
| **`constant_velocity`** | **匀速直线**：每个 agent 按最后一帧的 (vx, vy) 直线走 80 步 | 无 —— 32 条完全一样 |
| **`rule_based`** | **规则策略**：lane-keeping（保持车道）+ IDM（智能驾驶员模型，跟车）+ traffic-light 反应 + collision avoidance（避碰）。32 个 rollout 用 32 组不同参数（speed_factor、follow_gap、steer_gain 等） | 有真正的多样性（参数扰动） |

实现都在 [`../code/darwin_waymo/policies/baselines.py`](../code/darwin_waymo/policies/baselines.py)。

---

## 关键数字（15 个 scenario 平均）/ Headline numbers (15 scenarios)

| Baseline | metametric | 越界率 (offroad) | 碰撞率 (collision) | 距路沿 likelihood | 平均耗时 (秒) |
|---|---|---|---|---|---|
| `log_replay` | **0.786** | 7.6% | 8.7% | 0.756 | 65 |
| `constant_velocity` | 0.475 | 28.5% | 24.0% | 0.546 | 65 |
| **`rule_based`** | **0.403** | **90.2%** | 28.4% | **0.230** | 299 |

**WOSAC 论文里发表的参考分（整体 metametric）：**

| 系统 | metametric |
|---|---|
| Random Gaussian | 0.155 |
| Constant Velocity | 0.287 |
| CV + Gaussian Noise | 0.324 |
| Wayformer (Diverse) | 0.531 |

---

## Step 3 的核心 finding（给老师汇报）/ Key finding

> **rule-based baseline 在 80 步 closed-loop rollout 中有 90.2% 的概率开出马路。**
>
> 2 个 scenario 的 smoke test 是 97.9%，跨 15 个 scenario 平均下来是 90.2% —— 不是偶然，是**系统性失败**。
>
> 最有指向性的 sub-metric 是 `angular_speed_likelihood = 0.048` —— 规则引擎的角速度（转向）分布和真实驾驶差太多了，所以 8 秒闭环 rollout 里 agent 慢慢侧滑出了车道。

The rule-based baseline drives off-road on 90.2% of rollouts across 15 scenarios — confirmed across the shard, not a fluke. `angular_speed_likelihood = 0.048` is the smoking gun: the rule engine's rotational dynamics are very different from real driving.

**这是一个非常具体、可优化的失败模式（failure mode）。** **Map adherence（沿路行驶能力）就是最值得 learned model 优化的目标** —— Step 4 接住了这个线索。

---

## 工程实现要点 / Implementation notes

- **Metric 评测用 TF（CPU 模式）**：TF 2.12 在这台机器上找不到 CUDA libs，加上 PyTorch 也用 CUDA 会 segfault，所以 TF 锁在 CPU。PyTorch 跑 GPU。
- **Runner 每个 (scenario, baseline) 写一行 CSV 立刻 flush** —— 这是从 Step 3 一次 1h47min 的长跑教训学到的。中途挂掉的话，已完成的部分都在 CSV 里，不会丢。
- **rule_based 慢**（299 秒/scenario），因为 32 rollout × 80 step × N agents 都要跑物理步进 + 决策逻辑。这个慢正好提醒我们：rule_based 不能 scale 到全验证集。Phase 2 用 GPU + neural network 时这个开销会消失。

---

## 这一步用到的源代码 / Source files used

| 文件 | 用途 |
|---|---|
| `run_baselines.py` | 评测主脚本 |
| `code/darwin_waymo/policies/baselines.py` | 三个 baseline rollout function 的实现 + 注册表 |
| `code/darwin_waymo/policies/rule_engine.py` + `kinematic_model.py` | rule_based 的实现 |
| `code/darwin_waymo/submission/rollout_engine.py` | `package_submission()` —— 三个 baseline 共用的打包函数 |

---

## 接下来 / What goes next

**Step 4** 训练**第一个 PyTorch learned model**（一个 MLP），用同样的 harness 评测。目标：在至少一个 sub-metric 上击败 constant velocity。

Step 4 trains the first PyTorch learned model and scores it against the same harness. Goal: beat constant velocity on at least one sub-metric.
