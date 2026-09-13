# EdgePdM-Agent 全过程学习模板（给零基础接手的人）

> 本文用「讲课」口吻说明：这个项目是什么、为什么做、分几步、每步学什么、怎么验收。  
> 执行者会按 Gate 推进；每关结束必须让 **project-manager** 审核通过才能下一步。

---

## 1. 项目一句话

我们要做一个**端侧预测性维护小系统**：

1. 用公开传感器数据预测设备**还剩多久可能失效**（RUL）；
2. 把模型推理放到 **C++** 里跑（像工控机/边缘设备）；
3. 用本地大模型（**llama.cpp**）把数字结果说成人话维修建议。

它**不是**又一个「查手册的 RAG 聊天机器人」。

---

## 2. 你需要先搞懂的 8 个词

| 词 | 白话 |
|----|------|
| Predictive Maintenance | 坏之前预测，提前修 |
| RUL | 还剩多少个运行周期 |
| C-MAPSS | NASA 公开的发动机退化数据集（我们的练习场） |
| Baseline | 先用简单模型做出可对比分数 |
| Sliding window | 用过去 N 个周期预测当前 |
| ONNX | 把 Python 模型导出成通用格式给 C++ 用 |
| llama.cpp | 本地跑小大模型的 C++ 引擎 |
| Gate | 本项目的关卡；过关才能进下一阶段 |

更全的「去 B 站搜什么」见：`docs/03_learning_plan.md`。

---

## 3. 为什么选这个方向（动机模板）

真实学习动机可以是：GitHub 上有成熟工程，方便复现。

对外请这样说：

> 我想把时间序列建模、传感器/嵌入式经验和 C++ 工程串起来。C-MAPSS 提供公开可复现的 benchmark；我复现基线后，扩展到 ONNX C++ 推理和本地 LLM 解释。

详细心路：`notes/mindset_journal.md`。

---

## 4. 系统怎么串起来（架构）

```text
[数据] NASA C-MAPSS 多传感器时间序列
          ↓
[算法] 特征工程 + RUL 回归（XGBoost / LSTM…）
          ↓
[导出] .onnx 模型文件
          ↓
[端侧] C++ + ONNX Runtime：读 CSV → 推理 → RUL/风险/异常传感器
          ↓
[解释] llama.cpp：吃结构化 JSON，输出自然语言建议
```

分角色：

- **算法模型**：负责算 RUL；
- **C++**：负责部署与性能；
- **LLM**：只负责解释，**不算 RUL**。

---

## 5. 全过程 Gate 地图

| Gate | 你在学什么 | 完成长什么样 | 审核文件 |
|------|------------|--------------|----------|
| G0 | 立项、目录、规则 | 仓库骨架 + 主管 subagent | `docs/gates/G0.md` |
| G1 | 数据与 RUL 任务 | 数据落盘 + 能讲清五问 | `G1.md` |
| G2 | 机器学习 baseline | 有 RMSE 等真实指标 | `G2.md` |
| G3 | 深度学习序列模型 | 与 baseline 对比表 | `G3.md` |
| G4 | C++ ONNX 推理 | 可执行程序 + 延迟 | `G4.md` |
| G5 | 本地 LLM 解释 | 示例对话可复现 | `G5.md` |
| G6 | 包装成作品 | README/架构图/简历条目 | `G6.md` |

**当前关卡永远看**：`docs/gates/CURRENT_GATE.md`  
**审核历史**：`docs/gates/review_log.md`

### 工作节奏（固定）

```text
做当前 Gate → 写 notes/work_log.md →（实验则写 experiments/）
→ 请 project-manager 审核
→ PASS 才改 CURRENT_GATE 并进入下一关
→ FAIL 则按缺口返工，禁止跳关
```

对 Cursor 说：

> 用 project-manager 审核当前 Gate

---

## 6. 每一关「不会也能跟着做」的说明

### G0 立项（已完成）

产出：README、AGENTS、计划、决策、学习清单、笔记、Gate。  
意义：先约定「做什么 / 不做什么」，避免做成手册 RAG。

### G1 数据（本阶段）

你要会：

1. 下载并校验 FD001 三文件；
2. 解释字段；
3. 手算/代码验证 RUL 构造；
4. 回答面试五问。

详细笔记：`notes/learning_cmapss.md`（必读）。

### G2 Baseline

你要会：

1. 读 eastani 仓库的 pipeline 思路（参考，不是只交 clone）；
2. 自己在 `src/` / `notebooks/` 实现：读数据 → 标签 → 特征 → 训练 → 评估；
3. 把指标写入 `experiments/`。

初学者建议顺序：

```text
B站：XGBoost 回归
B站：时间序列 特征工程 / rolling
再写代码
```

### G3 序列模型

在 baseline 之上加 LSTM/GRU/1D-CNN 之一，**必须对比**。  
重点学：sliding window、按 unit 划分、避免泄漏。

### G4 C++ 部署

```text
Python 导出 ONNX → CMake 工程 → ONNX Runtime C++ → 打印 RUL 与耗时
```

搜：`ONNX Runtime C++ 推理`、`CMake 入门`。

### G5 本地 LLM

先跑通 `llama-server`，再把：

```json
{"predicted_rul": 38, "risk_level": "warning", "abnormal_sensors": ["sensor_11"]}
```

喂给模型，生成建议。记住：LLM 不替代 RUL 模型。

### G6 结项

把故事写完整：复现 → 扩展 → 数字可追溯 → 简历四条亮点。

---

## 7. 推荐参考仓库（各学什么）

| 仓库 | 你学什么 |
|------|----------|
| [eastani/predictive-maintenance-cmapss](https://github.com/eastani/predictive-maintenance-cmapss) | 工程化 PdM pipeline、评估、serving 思路 |
| [salarsadek/turbofan-rul-time-series-ml](https://github.com/salarsadek/turbofan-rul-time-series-ml) | 报告级实验与图 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 本地推理与 server |
| [microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) | C++ 推理 API |

原则：**复现思想 + 自己重写关键路径 + 明确扩展点**。

---

## 8. 目录导航（迷路时看这里）

| 路径 | 用途 |
|------|------|
| `docs/00_project_brief.md` | 立项简报 |
| `docs/01_delivery_plan.md` | 总计划与状态 |
| `docs/02_decision_record.md` | 为什么这样选 |
| `docs/03_learning_plan.md` | 搜什么学什么 |
| `notes/work_log.md` | 每天做了啥 |
| `notes/mindset_journal.md` | 心路 |
| `notes/trial_error_log.md` | 踩坑 |
| `experiments/` | 每次实验指标 |
| `src/` | Python 代码 |
| `cpp_inference/` | C++ 推理 |
| `agent/` | LLM 解释 |
| `configs/default.yaml` | 配置 |

---

## 9. 环境（本机已做 / 后来者照做）

```powershell
cd E:\EdgePdM-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

数据：

- 已提供下载说明见 `data/README.md`
- 原始大文件默认不进 git

---

## 10. 完成标准（你怎么知道「真的做完了」）

当 G6 PASS 时，你应能对任意新人讲 15 分钟：

1. 业务问题是什么；
2. 数据与标签怎么来；
3. baseline 与深度模型差在哪；
4. C++ 如何跑通推理；
5. LLM 边界是什么；
6. 每个关键数字出自哪次实验目录。

做不到其中任一条 = 还没结项。
