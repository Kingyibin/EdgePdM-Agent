# C-MAPSS 学习笔记（G1 完成稿）

> 作者视角：金毅彬  
> 日期：2026-07-23  
> 目标：让「完全没接触过这个数据集的人」看完也能讲清楚任务

---

## 0. 先建立直觉（1 分钟版）

想象你有 100 台同型号发动机。每台从「还能正常飞」开始，传感器慢慢变差，直到某天失效。

- **训练集**：每台都记录到「坏掉那一刻」——完整 run-to-failure。
- **测试集**：只给你看到中途某段，然后问你：**再过多少个运行周期会坏？**

这个「还剩多少周期」就叫：

**RUL = Remaining Useful Life（剩余使用寿命）**

本项目第一阶段只用 **FD001**（最简单、资料最多的子集）。

---

## 1. 数据集是什么

**NASA C-MAPSS**（Commercial Modular Aero-Propulsion System Simulation）是 NASA 用仿真器生成的**涡扇发动机退化**公开数据，常用于预测性维护（Predictive Maintenance）与 RUL 回归研究。

它权威的地方不在于「航空发动机本身」，而在于：

1. 公开、可复现；
2. 有标准 train/test 与官方 RUL；
3. 大量论文与 GitHub 项目用同一套口径，方便对比。

**我为什么用它（而不是企业手册）**：

- 手册/故障案例难公开、质量不稳定（我之前 RAG 诊断就卡在这里）；
- C-MAPSS 让我能把「时间序列 + 传感器 + 端侧部署」做成可量化作品；
- 发动机是 benchmark 载体，方法论可迁移到电机、泵、风机、工业仪表等。

### 本机数据来源与校验

| 项 | 内容 |
|----|------|
| 官方口径 | NASA PCoE / data.nasa.gov：C-MAPSS Jet Engine Simulated Data |
| 本机下载 | Zenodo 镜像 `CMAPSSData.zip`（NASA progpy 亦引用该链接） |
| URL | `https://zenodo.org/records/15346912/files/CMAPSSData.zip?download=1` |
| 落盘路径 | `data/raw/train_FD001.txt` 等 |
| 论文参考 | Saxena et al., PHM08, *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation* |

### FD001 文件校验（实测）

| 文件 | 大小(bytes) | 行数 | 说明 |
|------|-------------|------|------|
| `train_FD001.txt` | 3,515,356 | 20,631 | 100 台发动机，完整跑到失效 |
| `test_FD001.txt` | 2,228,855 | 13,096 | 100 台，截断于失效前 |
| `RUL_FD001.txt` | 429 | 100 | 测试集每台「最后观测时刻」的真实 RUL |

补充统计：

- 训练集每台最大 cycle：最小 128，最大 362，平均约 206.31
- 测试集官方 RUL 均值约 **75.52**

---

## 2. 每一行是什么（字段）

官方 readme 写「26 列」。实际含义是：

| 列序号 | 字段名（本项目） | 含义 |
|--------|------------------|------|
| 1 | `unit` | 发动机编号（1..100） |
| 2 | `cycle` | 运行周期（从 1 递增） |
| 3–5 | `setting_1..3` | 工况参数（对性能影响大） |
| 6–26 | `sensor_1..21` | 21 路传感器读数（温度/压力/转速等仿真通道） |

注意：

- 文件是**空格分隔、无表头**；
- 用 pandas 读时建议 `sep=r'\s+'`，并只取前 26 列；
- 传感器具体物理名称在论文/社区文档有对应表，**建模第一阶段不必背全名**，知道「多传感器 + 工况」即可。

读法示例（概念）：

```python
cols = ['unit','cycle','setting_1','setting_2','setting_3'] + [f'sensor_{i}' for i in range(1,22)]
df = pd.read_csv('data/raw/train_FD001.txt', sep=r'\s+', header=None)
df = df.iloc[:, :26]
df.columns = cols
```

---

## 3. RUL 标签怎么构造（最重要）

### 3.1 训练集

训练集每台发动机都跑到失效。对某台发动机，若最大 cycle 为 \(T\)，则第 \(t\) 个 cycle 的 RUL：

\[
RUL(t) = T - t
\]

例：unit=1，最大 cycle=192（本机数据 unit1 首条 RUL=191，即 \(T=192\)）：

| cycle | RUL |
|-------|-----|
| 1 | 191 |
| 2 | 190 |
| … | … |
| 191 | 1 |
| 192 | 0 |

我在本机验证：unit1 末三行 RUL 为 `[2, 1, 0]`，首三行为 `[191, 190, 189]`。

### 3.2 测试集

测试序列在失效前结束。官方另给 `RUL_FD001.txt`：

- 第 \(i\) 行 = 测试集第 \(i\) 台发动机，在**其最后一行观测**时的真实 RUL。

评估时通常：

1. 用该发动机测试轨迹（整段或最后窗口）做特征；
2. 预测一个 RUL；
3. 与 `RUL_FD001.txt` 对应行比较，算 RMSE 等。

### 3.3 capped RUL（常用技巧）

许多论文把 RUL **上限截断**到 125（或 130）：

```text
RUL_capped = min(RUL, 125)
```

原因（面试可讲）：

- 早期健康阶段传感器变化不明显，「还剩 180 vs 200」难区分、也对维护决策不那么关键；
- 模型更应学好**后期退化段**；
- 截断后标签分布更合理，常能提升指标稳定性。

本项目默认 `configs/default.yaml` 中 `rul_cap: 125`。

---

## 4. train / test 差异（防泄漏）

| | 训练集 | 测试集 |
|--|--------|--------|
| 是否跑到失效 | 是 | 否（中途截断） |
| RUL 来源 | 自己用 max(cycle) 算 | 官方 `RUL_*.txt` |
| 评估 | 可做验证划分（按 unit） | 最终报告 RMSE/Score |

**泄漏红线**：

- 不要把同一 `unit` 的时间点随机打乱进 train/val（时序泄漏）；
- 标准化（StandardScaler）应 **fit 在训练发动机上**，再 transform 测试；
- rolling 特征只能用「当前及过去」，不能用未来 cycle。

---

## 5. FD001–FD004 区别（简表）

来自官方 `readme.txt`：

| 子集 | 训练轨迹 | 测试轨迹 | 工况 | 故障模式 |
|------|----------|----------|------|----------|
| FD001 | 100 | 100 | 1（海平面） | 1（HPC 退化） |
| FD002 | 260 | 259 | 6 | 1（HPC） |
| FD003 | 100 | 100 | 1 | 2（HPC + Fan） |
| FD004 | 248 | 249 | 6 | 2（HPC + Fan） |

**本项目主线：FD001**。更难子集留作扩展，不阻塞主线。

---

## 6. 评估指标（先懂这两个）

### RMSE

\[
RMSE = \sqrt{\frac{1}{n}\sum_i (y_i - \hat{y}_i)^2}
\]

越小越好。

### NASA asymmetric scoring function（了解）

对「报得太晚」（实际更早失效）惩罚更重——因为维护决策上，低估风险更危险。G2 实现 baseline 时尽量一并报告；若时间紧可先 RMSE，但笔记里要知道 Score 的存在。

---

## 7. 和本项目后续模块怎么接

```text
C-MAPSS 传感器序列
  → 特征 / 窗口
  → RUL 模型（Python）
  → 导出 ONNX
  → C++ 端侧推理
  → 结构化 JSON（RUL、风险、异常传感器）
  → llama.cpp 本地 LLM 解释（不预测 RUL）
```

G1 只要求把左边「数据与任务」吃透。

---

## 8. 面试五问自测（我的答案）

### Q1. C-MAPSS 是什么？

NASA 公开的涡扇发动机退化仿真数据集，用多工况设置与多传感器时间序列模拟 run-to-failure，是 RUL / 预测性维护的标准 benchmark 之一。

### Q2. RUL 标签怎么来？

训练集：每台发动机完整跑到失效，`RUL = max_cycle - current_cycle`。  
测试集：序列截断，真实 RUL 由官方 `RUL_FD00x.txt` 给出。

### Q3. 为什么常用 capped RUL（如 125）？

早期健康阶段退化信号弱，过大 RUL 难学且对维护决策价值有限；截断后让模型聚焦后期退化，常更稳。

### Q4. 测试集和训练集差在哪？

训练有完整失效过程；测试在失效前结束，需要外推「还能跑多久」。划分与标准化必须按发动机/训练分布处理，避免泄漏。

### Q5. 你为什么用它而不是企业私有数据？

要做可公开、可复现、可量化的作品；企业故障数据难获得且不宜展示。C-MAPSS 保证方法可验证，工程上再通过 C++/ONNX 与本地 LLM 体现落地能力。

---

## 9. 我今天实际做了什么（可复现）

1. 从 Zenodo 下载 `CMAPSSData.zip`（约 12.4 MB）到 `data/raw/`
2. 解压到 `data/raw/_extract/`，复制 FD001 三文件 + `readme.txt` + 论文 PDF 到 `data/raw/`
3. 用项目 `.venv` 安装 pandas/numpy，打印 shape、unit 数、RUL 构造样例
4. 完成本笔记

---

## 10. 给后来者的阅读顺序

1. 本文第 0–3 节（直觉 + 标签）
2. `data/raw/readme.txt`
3. `docs/tutorials/00_project_walkthrough_for_beginners.md`
4. 再进 G2 写代码
