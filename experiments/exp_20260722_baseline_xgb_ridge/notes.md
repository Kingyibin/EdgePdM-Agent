# Experiment: FD001 tabular baseline (Ridge + XGBoost)

- 执行者：金毅彬
- 时间：2026-07-23（UTC 戳记目录为 20260722）
- Gate：G2
- 脚本：`scripts/run_baseline_fd001.py`

## 做了什么（白话）

1. 读取 FD001 train/test/RUL
2. 训练集构造 capped RUL（上限 125）
3. 去掉几乎恒定的传感器列
4. 对保留特征做 per-unit rolling mean（窗口 5）
5. StandardScaler 只在训练集 fit
6. 训练 Ridge 与 XGBoost
7. 测试时取每台发动机**最后一帧**预测 RUL，与官方 RUL 对比

## 主指标（test，100 units）

| 模型 | RMSE (capped125) | MAE (capped125) | NASA Score (capped125) |
|------|------------------|-----------------|------------------------|
| Ridge | 20.84 | 16.34 | 1285.3 |
| **XGBoost** | **17.48** | **12.29** | **929.3** |

辅助：XGBoost 5-fold GroupKFold（按 unit）训练段 CV RMSE 见 `metrics.json` 的 `groupkfold_xgb_rmse_mean`。

## 结论

- XGBoost 明显优于 Ridge，作为后续对比与 ONNX 导出的**首选 baseline**。
- 该 baseline 故意保持「表格特征 + 最后一帧评估」，便于讲清、便于部署；序列模型（G3）再用窗口建模冲击它。

## 产物

- `metrics.json`
- `xgboost.joblib` / `ridge.joblib`
- `predictions_*.csv`
- `scatter_*.png`

## 参考与边界

- 思路参考公开 C-MAPSS PdM pipeline（如 eastani 仓库的工程化评估方式），**代码为本仓库重写**，非直接拷贝。
- 未使用 LSTM；未接 LLM；未做 ONNX（留给后续 Gate）。
