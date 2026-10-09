# 解释层示例是手写夹具

`case0*.json` 用来给 llama-server 看提示词长什么样。`engine_id` 都是 `fixture-*`。里面的 `predicted_rul`、`risk_level`、`abnormal_sensors`、`trend` **不是** `predictions_lstm.csv` 的某一行，也不是 C++ 程序算出来的。

C++ 只打印一个 RUL。风险等级和异常传感器没有对应的模型输出。

不要把 `fixture-warning` 的 38 和端侧对齐样本 unit 1 混在一起。unit 1 的实测是：真值 112，Python ORT / C++ 预测约 118.47（`experiments/exp_20260723_cpp_onnx_infer/metrics.json`）。

`case0*_explanation.md` 是 0.5B 对**当时那份夹具**的真实生成，保留「把 RUL 说成 Revised Useful Life」这类瑕疵。夹具后来补了 `payload_origin`，解释文本没有重跑。
