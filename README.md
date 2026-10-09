# EdgePdM-Agent

用 NASA C-MAPSS FD001 预测发动机剩余寿命，把 LSTM 导出为 ONNX，在 C++ 里用 ONNX Runtime 推理，再用本地小模型把结构化结果写成维护说明。

作者：金毅彬

```text
C-MAPSS FD001 → Python 训练 → ONNX → C++ 推理 → JSON → llama.cpp 解释
```

## 结果

FD001，100 台测试发动机，标签上限 125 个周期。

| 项 | 结果 | 出处 |
|----|------|------|
| Ridge RMSE | 20.84 | `experiments/exp_20260722_baseline_xgb_ridge/metrics.json` |
| XGBoost RMSE | 17.48 | 同上 |
| LSTM RMSE / MAE / NASA Score | **14.27 / 10.48 / 324.6** | `experiments/exp_20260722_lstm_fd001/metrics.json` |
| 同一窗口 Python ORT | 118.4717 | `experiments/exp_20260723_cpp_onnx_infer/metrics.json` |
| 同一窗口 C++ ORT | 118.472 | 同上 |
| C++ 平均延迟 | **0.167 ms** | warmup 5 次后，再测 50 次，单线程 |

C++ 程序读取已经缩放过的 30×17 窗口。本地模型只解释 JSON，不重新计算 RUL。延迟是这一台 CPU 上的单窗口耗时。

更细的口径在 `docs/benchmark_summary.md`。

## 仓库里有什么

| 路径 | 内容 |
|------|------|
| `src/`、`scripts/` | 数据、特征、LSTM、指标、ONNX 导出 |
| `cpp_inference/` | C++ / ONNX Runtime 推理 |
| `agent/` | llama.cpp 解释客户端与示例 |
| `experiments/` | 每次实验的 `metrics.json` |
| `docs/` | 决策、教程、指标说明 |

原始数据、`.pt`、`.onnx` 和 GGUF 不进版本库。按下面的步骤在本机生成。

## 运行

在仓库根目录执行。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

数据使用 NASA C-MAPSS FD001，放到：

```text
data/raw/train_FD001.txt
data/raw/test_FD001.txt
data/raw/RUL_FD001.txt
```

下载说明见 `data/README.md`。

```powershell
python scripts\run_baseline_fd001.py
python scripts\run_lstm_fd001.py
python scripts\export_lstm_onnx.py
```

C++ 需要 CMake、g++ 和 ONNX Runtime，步骤在 `cpp_inference/README.md`。

```powershell
cd cpp_inference
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
.\build\edgepdm_infer.exe ..\models\onnx\rul_lstm.onnx ..\models\onnx\sample_window_unit1_scaled.csv 5 50
```

本地解释需要 llama.cpp 的 `llama-server` 和 Qwen2.5-0.5B GGUF，见 `agent/README.md`。

```powershell
.\scripts\start_llama_server.ps1
python agent\explain_client.py --json agent\examples\case01_warning.json
```

`agent/examples/case0*.json` 是手写提示词样例，用来看解释层怎么说话。某台发动机的预测数字以 `experiments/exp_20260722_lstm_fd001/predictions_lstm.csv` 和 C++ 实验记录为准。

## 参考

- https://github.com/eastani/predictive-maintenance-cmapss
- https://github.com/salarsadek/turbofan-rul-time-series-ml
- https://github.com/ggml-org/llama.cpp
- https://github.com/microsoft/onnxruntime
