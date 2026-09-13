# 简历项目条目草稿（G6 终审 PASS）

**基于 C-MAPSS 的端侧预测性维护与本地 LLM 解释系统（EdgePdM-Agent）**

- 基于 NASA C-MAPSS FD001 构建 RUL 预测流水线：capped RUL=125、防泄漏划分与评估；XGBoost baseline 测试 RMSE≈17.48，LSTM（window=30）提升至 RMSE≈14.27、NASA Score≈324.6
- 结项后对 LSTM 做真实超参扫描（窗口/隐层/层数/学习率/种子）与 MC Dropout 不确定性记录；扫描最优约 RMSE≈13.1（旁证，未替换端侧导出模型）
- 将 LSTM 导出 ONNX，使用 C++/ONNX Runtime 完成端侧推理，与 Python ORT 结果对齐（pred≈118.47），CPU 单线程平均延迟约 0.17ms
- 接入 llama.cpp（llama-server + Qwen2.5-0.5B GGUF）对结构化诊断 JSON 生成维护解释，明确 LLM 不重新计算 RUL
- 工程可复现：Gate 审核、实验目录、`configs/default.yaml`、初学者全过程教程与试错记录

数字出处：

- `experiments/exp_20260722_baseline_xgb_ridge/metrics.json`
- `experiments/exp_20260722_lstm_fd001/metrics.json`
- `experiments/exp_20260723_cpp_onnx_infer/metrics.json`
- 扫描旁证：`experiments/marathon_sweep_notes.md` / `experiments/r01_w30_h64_lr5e4/metrics.json`
