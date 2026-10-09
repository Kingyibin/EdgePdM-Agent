# Experiment: C++ ONNX Runtime inference

- Gate：G4
- 模型：`models/onnx/rul_lstm.onnx`（由 G3 LSTM 导出）
- 程序：`cpp_inference/build/edgepdm_infer.exe`

## 一致性

| 运行时 | predicted_rul (unit1 scaled window) |
|--------|-------------------------------------|
| Python onnxruntime | 118.4717 |
| C++ onnxruntime | 118.472 |

## 性能（CPU，IntraOpThreads=1）

- warmup=5, iters=50
- latency_ms_avg ≈ **0.167**
- 单线程延迟的倒数 ≈ **5988** 次/秒（`1000/0.167`）。没有并发压测，不能写成系统吞吐。

## 结论

端侧推理链路打通；数字与 Python ORT 对齐。下一步（G5）用结构化结果接 llama.cpp 解释，不改变 RUL 计算。
