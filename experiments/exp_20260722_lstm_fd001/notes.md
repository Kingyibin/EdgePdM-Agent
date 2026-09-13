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
- 测试：每台 last window（不足则前端 pad）

## 同口径对比（test，capped125）

| 模型 | RMSE | MAE | NASA Score |
|------|------|-----|------------|
| G2 XGBoost | 17.48 | 12.29 | 929.3 |
| **G3 LSTM** | **14.27** | **10.48** | **324.6** |

结论：**LSTM 优于表格 XGBoost baseline**（RMSE 与 Score 均更好）。  
部署候选：优先导出/对照 LSTM；若 C++ 端优先简单，仍可先部署 XGBoost ONNX，再迭代 LSTM ONNX。

## 误差观察

- 验证集 best RMSE ≈ 13.70；测试 14.27，泛化尚可，未见严重崩坏。
- Score 大幅下降说明「偏晚预测」的大错误更少（对维护更友好）。

## 产物

`metrics.json`、`lstm.pt`、`predictions_lstm.csv`、`scatter_lstm.png`、`history.json`
