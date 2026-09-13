# 迭代记录

## 2026-07-23 — 立项（Iteration 0）

### 触发

简历投递不顺，缺 C++/端侧 AI 工程硬项目；曾犹豫手册 RAG / 微调，资料与差异化不足。

### 选择

启动 EdgePdM-Agent：C-MAPSS PdM + C++ ONNX + llama.cpp 解释；路径 `E:\EdgePdM-Agent`；用 project-manager Gate 制。

### 替代方案

手册诊断 Agent、纯微调、手写推理引擎 — 见 ADR-001。

### 结果

完成仓库骨架与文档体系；当前 Gate = G0，待主管审核后进入 G1。

### 是否进入论文/简历口径

否（立项阶段）。结项 G6 后再提炼简历条目。

---

## 2026-07-23 — G1 数据理解 + G2 Baseline（Iteration 1）

### 触发

G0 PASS 后按交付计划推进；需要可讲清的数据故事与可量化 baseline。

### 选择

- 数据：Zenodo CMAPSSData.zip → FD001
- Baseline：Ridge + XGBoost，capped RUL=125，rolling mean + StandardScaler，测试取 last cycle
- 文档：初学者教程 + learning_cmapss / learning_baseline

### 结果（测试集 100 units，主指标 capped125）

| 模型 | RMSE | NASA Score |
|------|------|------------|
| Ridge | 20.84 | 1285.3 |
| XGBoost | **17.48** | **929.3** |

产物：`experiments/exp_20260722_baseline_xgb_ridge/`

### 下一步

G1 已由主管 PASS；G2 完成后请主管审核，再进 G3 序列模型。

---

## 2026-07-23 — G3 LSTM（Iteration 2）

### 选择

window=30 的 LSTM（64 hidden, 2 layers），与 G2 同口径 capped125 / last-window 评估。

### 结果

| 模型 | RMSE_capped125 | NASA Score |
|------|----------------|------------|
| XGBoost | 17.48 | 929.3 |
| LSTM | **14.27** | **324.6** |

LSTM 胜出，作为后续主模型候选；C++ 部署可先 ONNX 化较简单的模型再迭代。

---

## 2026-07-23 — G4 C++ ONNX（Iteration 3）

### 选择

导出 G3 LSTM → ONNX；C++ ORT 推理预缩放 window；WinLibs 工具链。

### 结果

- C++/Python 预测一致（≈118.47）
- 平均延迟 ≈ **0.167 ms**（CPU 单线程）
- 工具链与链接踩坑记入 trial_error T-004～T-006

---

## 2026-07-23 — G5 llama.cpp（Iteration 4）

本地 llama-server + Qwen2.5-0.5B GGUF，5 条结构化解释示例落地；明确 LLM 不预测 RUL、非手册 RAG。

---

## 2026-07-23 — G6 结项（Iteration 5）

完成可复现 README、架构图、benchmark 汇总、简历草稿与总复盘；主管终审 **PASS**，CURRENT_GATE 标记 **COMPLETE**。

---

## 2026-08-20 — 结项后马拉松超参扫描（Iteration 6，旁证）

### 触发

闲时继续摸 FD001 LSTM；想弄清「正式 14.27 是不是只跑一次的运气」，并补不确定性（MC Dropout）。

### 选择

- 脚本：`training_marathon.py`（每轮 12 组真训：window / hidden / layers / lr / seed）
- 产物：`experiments/rNN_*/metrics.json`（不存权重）
- 口径：旁证与消融，**不**替换 G3 正式模型与 ONNX/C++ 链路（ADR-009）

### 结果（真实训练，非模拟）

- 约 71 个扫描目录；打赢 XGBoost(17.48) 约 67/71
- 抽查 `r03_w30_h64`：RMSE≈15.29，coverage95≈0.67
- 扫描最优 `r01_w30_h64_lr5e4`：RMSE≈**13.10**，NASA Score≈**240.8**（优于正式 14.27，但无 `.pt`、未导出端侧）
- 同结构不同 seed 可从 ~13.4 晃到 ~15.3 → 敏感性可讲

### 是否进入简历主数字

**否**（主数字仍 14.27）。可写一句旁证：后续扫描最优约 13.1。升级正式端侧模型须另开 G7。

详见：`experiments/marathon_sweep_notes.md`；会议：`docs/meetings/2026-08-20_marathon_sweep_story.md`。