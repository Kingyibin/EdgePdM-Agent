# EdgePdM-Agent 文档总索引（从这里开始）

> 如果你是新人：按「推荐阅读顺序」走。  
> 如果你要审查交付：看「定稿审查」。  
> 如果你要复现实验：看 README + experiments。

---

## 推荐阅读顺序（约 45–60 分钟）

| 顺序 | 文件 | 目的 |
|------|------|------|
| 1 | `docs/04_roles_and_governance.md` | 主管/负责人怎么协作 |
| 2 | `docs/05_full_process_timeline.md` | 全过程时间线与痕迹地图 |
| 3 | `docs/00_project_brief.md` | 项目是什么 / 非目标 |
| 4 | `notes/mindset_journal.md` | 为什么做、心路 |
| 5 | `notes/trial_error_log.md` | 错了什么、怎么改 |
| 6 | `docs/tutorials/00_project_walkthrough_for_beginners.md` | 技术主线白话版 |
| 6b | `docs/tutorials/01_mastery_from_zero.md` | 从零基础到能被追问（RUL/泄漏/ONNX/LLM） |
| 6c | `docs/tutorials/02_timeline_steps.md` | 选题→G0–G6→定稿→马拉松：一步一课 |
| 7 | `docs/benchmark_summary.md` | 关键数字 |
| 8 | `docs/gates/review_log.md` | 审核链 |
| 9 | `docs/06_final_delivery_audit.md` | 定稿审查结论 |
| 9b | `docs/07_seal_review.md` | 封盖复盘：误差分布、两种 RMSE、qps 口径 |
| 10 | 根目录 `README.md` | 动手复现 |
| 11 | `experiments/marathon_sweep_notes.md` | （可选）结项后超参旁证故事 |

---

## 按类型查找

### 治理与决策

- 角色：`04_roles_and_governance.md`
- 计划：`01_delivery_plan.md`
- ADR：`02_decision_record.md`
- 会议：`docs/meetings/`
- Subagents：`.cursor/agents/project-manager.md`、`project-lead.md`

### 学习笔记（负责人）

- C-MAPSS / Baseline / LSTM / ONNX-C++ / llama.cpp → `notes/learning_*.md`
- 每日日志：`notes/work_log.md`

### 实验与代码

- `experiments/exp_*/notes.md` + `metrics.json`（正式交付）
- `experiments/marathon_sweep_notes.md` + `experiments/rNN_*/metrics.json`（结项后超参旁证）
- Python：`src/`、`scripts/`；马拉松脚本：`training_marathon.py`
- C++：`cpp_inference/`
- LLM：`agent/`

### Gate

- 当前状态：`docs/gates/CURRENT_GATE.md`
- 验收单：`G0.md`～`G6.md`
- 审核日志：`review_log.md`

---

## 一句话项目状态

**G0–G6 技术结项 COMPLETE（2026-07-23）；定稿审查 PASS（2026-08-06）；2026-10-08 封盖（ADR-010）。** 正式模型仍是 RMSE 14.27 的 LSTM。封盖只增加对已有预测的复盘，见 `docs/07_seal_review.md`。
