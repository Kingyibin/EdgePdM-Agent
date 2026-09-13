# 会议纪要 — 结项后马拉松扫描写入项目故事

- 日期：2026-08-20
- 类型：结项后记录补齐（非新 Gate 审核会）
- 角色：负责人整理；不宣称 Gate PASS

## 背景

结项后闲时用 `training_marathon.py` 在 FD001 上继续真训 LSTM 超参扫描，产出约 71 个 `experiments/rNN_*`（仅 `metrics.json`）。

## 结论（写入故事的口径）

1. **同一件事**：仍是 NASA C-MAPSS FD001 RUL + LSTM，不是新算法主线。  
2. **有用处**：超参/种子敏感性 + MC Dropout 不确定性，丰富面试可讲故事。  
3. **不替换正式交付**：端侧 ONNX/C++ 与简历主数字仍锚定七月 `exp_20260722_lstm_fd001`（RMSE≈14.27）。  
4. **扫描最优**（约 RMSE 13.10）仅作旁证；要升级正式模型须另开 G7。  
5. `r05`/`r06`/`r07` 为崩溃残留，保留或清理均可，不影响主叙事。

## 已落档路径

- `experiments/marathon_sweep_notes.md`
- `docs/iteration_log.md` Iteration 6
- `docs/05_full_process_timeline.md` 结项后阶段
- `docs/02_decision_record.md` ADR-009
- `notes/work_log.md` / `notes/mindset_journal.md`
