# Experiment: FD001 LSTM sequence model

- 执行者：金毅彬
- Gate：G3
- 脚本：`scripts/run_lstm_fd001.py`

## 设置

- window = 30
- features = 去掉恒定传感器后 17 维
- LSTM hidden=64, layers=2, dropout=0.2
- Adam lr=1e-3, MSE, 25 epochs, 按 unit 留 20% 验证，取 best val checkpoint
- Scaler：只在训练窗口上 fit
- 测试：每台 last window。代码里长度不足 30 会重复第一行；FD001 测试最短 31 周期，这次没有触发。

## 同口径对比（test，capped125）

| 模型 | RMSE | MAE | NASA Score |
|------|------|-----|------------|
| G2 XGBoost | 17.48 | 12.29 | 929.3 |
| **G3 LSTM** | **14.27** | **10.48** | **324.6** |

结论：**LSTM 优于表格 XGBoost baseline**（RMSE 与 Score 均更好）。  
结题端侧导出的是这份 LSTM，没有另导 XGBoost ONNX。

## 误差观察

- 验证集 best RMSE ≈ 13.70；测试 14.27。两者聚合方式不同（全部窗口 vs 每台最后一窗），不能直接读成「只掉了 0.6」。
- 相对 XGBoost，NASA Score 从 929 降到 325。封盖复盘里，XGBoost 的 Score 有 87.6% 来自晚报警，LSTM 是 61%。详见 `docs/07_seal_review.md` 第 6 节。

## 产物

`metrics.json`、`lstm.pt`、`predictions_lstm.csv`、`scatter_lstm.png`、`history.json`
