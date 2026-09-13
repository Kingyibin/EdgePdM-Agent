# 01 整体交付计划

状态图例：`TODO` | `IN_PROGRESS` | `PASS` | `FAIL` | `BLOCKED`

主管：`.cursor/agents/project-manager.md`  
当前关卡：见 `docs/gates/CURRENT_GATE.md`

| Gate | 阶段 | 状态 | 主要产出 | 验收摘要 |
|------|------|------|----------|----------|
| G0 | 立项与骨架 | PASS | 目录、README、AGENTS、计划、决策、学习计划、笔记骨架、subagent | 2026-07-23 主管 PASS |
| G1 | 数据与任务理解 | PASS | 数据落盘、`notes/learning_cmapss.md`、字段/RUL/划分讲清 | 2026-07-23 主管 PASS；五问自测 + raw 校验通过 |
| G2 | Baseline 复现 | PASS | `scripts/run_baseline_fd001.py` + `experiments/exp_20260722_baseline_xgb_ridge/` | 2026-07-23 主管 PASS；XGBoost RMSE≈17.48 / Score≈929（capped125） |
| G3 | 序列模型 | PASS | LSTM + 对比表（`exp_20260722_lstm_fd001`） | 2026-07-23 主管 PASS；LSTM RMSE≈14.27 / Score≈324.6，优于 XGBoost |
| G4 | C++ ONNX 推理 | PASS | `cpp_inference/` 可跑、延迟记录 | 2026-07-23 主管 PASS；C++/Python≈118.47，latency≈0.167ms |
| G5 | llama.cpp 解释 | PASS | `agent/` + 示例对话 | 2026-07-23 主管 PASS；llama-server + 5 case 解释；非手册 RAG |
| G6 | 结项包装 | PASS | README 复现、架构图、简历条目、总复盘 | 2026-07-23 主管终审 PASS；项目 COMPLETE |

**定稿状态（2026-08-06）**：定稿审查 **PASS**（痕迹完整性 / 双角色治理 / 错误改正链 / 可读索引）。技术结项 COMPLETE 维持；扩展须新开 G7+。详见 `docs/06_final_delivery_audit.md` 第 5 节与 `docs/gates/review_log.md`。

## 执行原则

1. **一次只做一个 Gate**
2. Gate 完成 → 调用 project-manager → 只有 PASS 才改 CURRENT_GATE
3. 每 Gate 至少更新：`notes/work_log.md` + 对应实验/学习文档
4. 卡壳超过一天：写 `notes/trial_error_log.md` 并标 BLOCKED

## 建议日历（弹性，时间不是硬约束）

| 阶段 | 建议精力 |
|------|----------|
| G0–G1 | 2–4 天 |
| G2–G3 | 1–2 周 |
| G4 | 1–2 周 |
| G5 | 3–7 天 |
| G6 | 2–4 天 |

## 依赖

- Python 3.10+、PyTorch / sklearn / XGBoost（G2+）
- CMake、C++17、ONNX Runtime（G4）
- llama.cpp 与小模型 GGUF（G5）
- C-MAPSS 原始 txt（G1）
