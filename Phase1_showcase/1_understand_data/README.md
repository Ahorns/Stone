# Phase 1A · Step 1 — 理解数据和任务格式
# Understand the data and task format

## 这一步要做什么 / Goal

搞清楚 Waymo Open Motion Dataset (WOMD) 一个 scenario 里到底有什么、WOSAC 的任务边界在哪儿，并且能用 Python 把数据读出来。

Know what's in a WOMD scenario, how the WOSAC task is framed, and verify we can read the data end-to-end.

---

## 这个文件夹里有什么 / Folder contents

```
data/
└── validation.tfrecord-00000-of-00150     (252 MB)
```

只有一个文件：**WOMD v1.2.0 验证集（validation split）的第一个 shard**。共 286 个 scenario，每个 scenario 9.1 秒、10 Hz 采样。

这是整个 Phase 1 showcase 唯一用的数据来源。完整 validation 一共 150 个 shard（约 38 GB），Phase 2 才需要全量；Phase 1 单机一个 shard 就能跑完。

One file: the **first shard of the WOMD v1.2.0 validation split** — 286 scenarios, 9.1 s each at 10 Hz. The only data source used in this entire showcase.

---

## 一个 scenario 里包含什么 / What's inside a scenario

| 字段 / Field | 中文说明 | English |
|---|---|---|
| `tracks` | 每个 agent 的完整轨迹，91 个时间步 × (x, y, z, heading, vx, vy, length, width, height, valid) | Per-agent trajectories |
| `current_time_index` | 历史和未来的分界点，一般是 10（前 1.1 秒是历史，后 80 步是未来） | Boundary between past and future |
| `dynamic_map_states` | 每个时间步红绿灯的状态（每条 lane 一个 state） | Per-step traffic-light states |
| `map_features` | 车道线、路边、人行横道、停止标志的几何 | Lanes, road edges, crosswalks, stop signs |
| `sdc_track_index` | 自动驾驶车（AV/ADV）在 tracks 里的下标 | Index of the autonomous vehicle |
| `objects_of_interest` / `tracks_to_predict` | WOSAC 要求模拟和评测的 agent 子集 | Agents required for simulation / evaluation |

**每个 scenario 最多 128 个 agent，其中一个是 ADV。Object type 有三种：vehicle (1) / pedestrian (2) / cyclist (3)。**

---

## WOSAC 的任务（口语版） / The task in plain words

> 给你一段真实交通场景的历史（约 1.1 秒）+ 地图，预测 **8 秒未来** 里所有车、人、骑行者会怎么走。每个 scenario 要给出 **32 个不同的可能未来**（distribution，不是单条轨迹）。

输出格式：每个 (rollout, agent, step) 的 `(x, y, z, heading)`。共 32 rollout × 80 step。

The task: given the past ~1.1 s plus the map, generate **32 plausible 8-second futures** for every agent. Output `(x, y, z, heading)` per (agent, step) — 32 rollouts × 80 steps.

---

## 我们这一步实际做了什么 / What we built at this step

1. **打开 tfrecord**：用官方 `waymo_open_dataset` 的 protobuf 接口读 shard。
2. **写了一个 ScenarioParser**：把原始 protobuf 转成 Python 友好的 `ParsedScenario` dataclass —— 所有 agent 轨迹、车道、路沿、红绿灯都变成 numpy 数据，后续步骤直接用。
3. **写了 feature extractor**：给定 `(agent_id, timestep)` 输出一个 **44 维 ego-centric 特征向量**（自身状态 + 车道信息 + 5 个最近邻 + 安全特征 + 红绿灯）。这个 44 维向量是后面 Step 3 rule_engine 和 Step 4 learned model 的共用输入。

Implementations live in [`../code/darwin_waymo/features/`](../code/darwin_waymo/features/) — `scenario_parser.py`, `agent_features.py`, `map_features.py`.

---

## 这个 shard 的数据规模 / Numbers for this shard

| 指标 | 数值 |
|---|---|
| Scenario 总数 | 286 |
| 平均每个 scenario 的 agent 数 | ~50 |
| 提取出的 next-step 训练样本总数 | ~670,000 |
| Vehicle / Pedestrian / Cyclist 占比 | 93% / 5% / 1% |

完整统计在 Step 4 的 [`../4_learned_model/dataset/stats.json`](../4_learned_model/dataset/stats.json)。

---

## 这一步用到的源代码 / Source files used

| 文件 | 用途 |
|---|---|
| `code/darwin_waymo/features/scenario_parser.py` | 原始 protobuf → `ParsedScenario` |
| `code/darwin_waymo/features/agent_features.py` | (agent, timestep) → 44 维特征向量 |
| `code/darwin_waymo/features/map_features.py` | 地图相关辅助函数（最近车道、是否在路口、距路沿距离等） |

---

## 接下来 / What goes next

**Step 2** 用同一个 parser 给 Waymax 官方 tutorial 喂数据，跑一遍 constant-velocity baseline，生成 6 张可视化图 + 一份合法 `SimAgentsChallengeSubmission.tar.gz`。

Step 2 plugs this parser into the official Waymax tutorial pipeline to produce 6 viz PNGs + a legal `SimAgentsChallengeSubmission.tar.gz` with a constant-velocity baseline.
