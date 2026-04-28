# Phase 1 Showcase — Waymo Open Sim Agents Challenge
# 第一阶段成果集 — Waymo 开放仿真智能体挑战赛

这是 WOSAC 项目 **Phase 1（第一阶段）** 的完整成果包，按 slide-guide 里定义的 step 顺序整理，方便逐步阅读和展示。整个文件夹大小 **305 MB**，已经把数据、代码、训练好的模型、评测结果全部装进来。第一次最多就和她讲一下你在做Phase 1A · Step 2就可以了.

This folder is a self-contained snapshot of all Phase 1 work for the WOSAC research project, organized by step to mirror the slide-guide structure. **305 MB total**, includes raw data, code, trained checkpoint, and evaluation results.

---

## Phase 1 → Step 文件夹对照表 / Step folder mapping

| Slide-guide 阶段 | 文件夹 | 这一步做了什么 |
|---|---|---|
| **Phase 1A · Step 1** — 理解数据和任务格式 | [`1_understand_data/`](1_understand_data/) | 读懂 WOMD 一个 shard 的数据格式（车、人、地图、红绿灯都长什么样） |
| **Phase 1A · Step 2** — 跑通官方 tutorial → 第一份合法 submission | [`2_official_tutorial/`](2_official_tutorial/) | 用 constant-velocity 当 baseline，把 32 个 rollout 打包成 `.tar.gz`，验证 pipeline 通了 |
| **Phase 1B · Step 3** — 三个 baseline 用官方 metric 打分 | [`3_three_baselines/`](3_three_baselines/) | log_replay / constant_velocity / rule_based 三种基线在 15 个 scenario 上的 WOSAC 分数 |
| **Phase 1B · Step 4** — 训练第一个 learned model | [`4_learned_model/`](4_learned_model/) | 一个 78,854 参数的 PyTorch MLP，预测下一步 (Δfwd, Δlat, Δh) 的高斯分布 |

---

## 文件夹和文件总览 / File & folder reference

| 路径 / Path | 类型 | 内容说明（中文） | What it is (English) |
|---|---|---|---|
| `README.md` | 文档 | 本文件，整个 showcase 的入口 + 文件目录表 | This file — entry point + index |
| `code/darwin_waymo/` | 代码包 | 所有 step 共享的 Python 包，包含 features / policies / submission / learned 四个子模块 | Python package shared across all steps |
| `code/darwin_waymo/features/` | 代码模块 | scenario_parser、agent_features、map_features — 把原始 protobuf 转成可用的 numpy 数据 | Scenario parser + 44-d feature extractor |
| `code/darwin_waymo/policies/` | 代码模块 | rule_engine（规则策略）、kinematic_model（自行车模型）、baselines（4 种 baseline 的注册表） | Rule-based policy + baselines registry |
| `code/darwin_waymo/submission/` | 代码模块 | rollout_engine — 闭环 rollout + WOSAC 提交格式打包 | Closed-loop rollout + WOSAC submission packaging |
| `code/darwin_waymo/learned/` | 代码模块 | **Step 4 新建** — PyTorch 学习模型：dataset、model、train、policy 四个文件 | **Step 4 new** — PyTorch learned model |
| `code/darwin_waymo/paths.py` | 代码 | 整个项目的路径常量定义 | Path constants for all scripts |
| **`docs/`** | 文档 | 所有相关文档和论文（详见下面 docs 表格） | All reference documents |
| `1_understand_data/` | step 文件夹 | Step 1 的产物 + 一个 README 解释做了什么 | Step 1 artefacts |
| `2_official_tutorial/` | step 文件夹 | Step 2：tutorial 脚本 + 6 张可视化 PNG + 提交文件 | Step 2 artefacts |
| `3_three_baselines/` | step 文件夹 | Step 3：3 种 baseline 的运行脚本 + 评分结果 | Step 3 artefacts |
| `4_learned_model/` | step 文件夹 | Step 4：训练数据、模型、训练日志、评测、完整报告 | Step 4 artefacts |

### `docs/` 文件夹详细说明 / Inside `docs/`

| 文件 | 类型 | 用途 / 内容 |
|---|---|---|
| `step4-plan.md` | Markdown | **Step 4 设计文档** — 在写 Step 4 代码之前先写的规划：架构选 MLP 不选 Transformer、5 个阶段、退出标准、时间估算。从 Step 3 教训出发的工程性计划。 |
| `proposal.md` | Markdown | **毕业论文 proposal 草稿** — CASA dissertation 的 draft，研究问题、方法、参考文献都在里面(参考一下就行了,暂时不重要) |
| `wosac-paper.pdf` | PDF | **必读论文** — Montali et al., "The Waymo Open Sim Agents Challenge"。任务定义 / metric / factorisation 规则的官方来源 |
| `design.md` | Markdown | **darwin_waymo 架构设计(这是我设计的一个算法,先试试,你之后可以不用)** — 早期的 Darwin v2 进化方法的设计文档（演化策略 + 闭环 fitness + 多样性奖励）。这部分是 darwin_waymo/evolution/ 的设计依据，**Step 4 的 learned model 没用到** |
| `overview.md` | Markdown | **中文路线图(是我设计的一个算法,也可以不用管)** — 早期写的 Darwin 模型升级路线（不要反向传播 / 闭环评估 / 潜变量 z / HMM）。是项目背景资料，**和 Step 1-4 的 learned model 走的不是一条路** |

> 提醒：`design.md` 和 `overview.md` 描述的是 **进化算法（evolutionary strategy）路线**，是 darwin_waymo 包早期工作的设计文档。**Phase 1B Step 4 改用 PyTorch + 梯度下降**，没有用进化算法。把这两份文档放进来是为了背景完整，但读 step 4 的时候请直接看 [`4_learned_model/report.md`](4_learned_model/report.md) 和 [`docs/step4-plan.md`](docs/step4-plan.md)，不要被 design.md / overview.md 误导。

---

## 下次给老师汇报的两个核心(不是这次汇报,应该是下次汇报的时候说,因为这个已经是phase1b的内容了) finding / Headline findings for the supervisor

1. **Step 3 — rule-based baseline 在 80 步 closed-loop rollout 中有 90.2% 的概率开出马路。** 跨 15 个 scenario 平均（不是个案）。最关键的 sub-metric 是 `angular_speed_likelihood = 0.048` — 规则引擎的转向动力学和真实驾驶差太多了，所以 8 秒 rollout 里 agent 慢慢侧滑出了车道。这是一个非常具体、可优化的失败模式。

2. **Step 4 — learned MLP 在 `linear_speed_likelihood` 上击败了 constant velocity** （0.038 vs 0.011）。这是 slide-guide 设定的成功标准（"beat const-vel on at least one sub-metric"）。但因为 closed-loop drift（一步训练 / 80 步评测的分布偏移），整体 metametric 输给了 const-vel。这个失败模式正是 Phase 2 要解决的（DAGGER 风格的 closed-loop training + agent-agent attention/GNN）。

Step 3 finds a concrete failure mode (map adherence, 90% off-road rate). Step 4 trains the first learned model end-to-end and beats const-vel on the linear-speed metric, while exposing the closed-loop drift problem that motivates Phase 2 directly.

---


## 这次工作的工程教训 / Engineering lessons captured

| 教训 | 解决方式 | 出现在哪一步 |
|---|---|---|
| 长跑脚本只在最后写结果 → kill 掉就全丢 | 改成每个 scenario 都立刻 append CSV row + 写 `status.json` | Step 3、Step 4 prepare_dataset / eval |
| TF 2.12 找不到 CUDA libs，而且和 PyTorch CUDA 直接冲突会 segfault | 显式 `tf.config.set_visible_devices([], "GPU")`，TF 跑 CPU，PyTorch 跑 GPU | Step 4 learned 评测 |
| 一开始时间预估偏低（57 min 实际 1h47m） | 先 smoke-test 2 个 scenario 测真实速度，再决定要不要跑 15 个 | Step 3 |
| 模型一直 overfit | 减小 epoch + dropout 0.2 + weight decay 1e-2，always save best_val checkpoint | Step 4 训练 |
