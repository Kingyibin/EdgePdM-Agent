# Benchmark 汇总（可追溯）

## 算法（FD001 test，100 units，capped RUL=125）

| 模型 | RMSE | MAE | NASA Score | 出处 |
|------|------|-----|------------|------|
| Ridge | 20.84 | 16.34 | 1285.3 | `experiments/exp_20260722_baseline_xgb_ridge/metrics.json` |
| XGBoost | 17.48 | 12.29 | 929.3 | 同上 |
| **LSTM（正式交付）** | **14.27** | **10.48** | **324.6** | `experiments/exp_20260722_lstm_fd001/metrics.json` |

### 结项后马拉松旁证（不替换上表）

| 项 | 值 | 出处 |
|----|-----|------|
| 扫描最优 RMSE | ≈13.10 | `experiments/r01_w30_h64_lr5e4/metrics.json` |
| 扫描最优 NASA Score | ≈240.8 | 同上 |
| 同结构不同 seed 示例 | RMSE≈15.29（`r03_w30_h64`） | 敏感性旁证 |
| 打赢 XGBoost 比例 | ≈67/71 | `experiments/r*/metrics.json` |
| 说明 | 仅 metrics、无 `.pt`、未导出 ONNX | `experiments/marathon_sweep_notes.md`；ADR-009 |

## 端侧推理（LSTM ONNX，CPU，1 thread）

| 项 | 值 | 出处 |
|----|-----|------|
| Python ORT pred (unit1) | 118.4717 | `exp_20260723_cpp_onnx_infer/metrics.json` |
| C++ ORT pred (unit1) | 118.472 | 同上 |
| 平均延迟 | **0.167 ms** | 同上 |
| 延迟倒数 | ≈5988 次/秒 | 同上；`1000/0.167`，单线程，不是并发压测 |

## 本地 LLM

| 项 | 值 |
|----|-----|
| 引擎 | llama.cpp llama-server b10091 CPU |
| 模型 | Qwen2.5-0.5B-Instruct-Q4_K_M.gguf |
| 示例数 | 5 | `agent/examples/` |
| 边界 | 不预测 RUL；非手册 RAG |
