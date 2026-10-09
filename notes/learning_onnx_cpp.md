# G4：ONNX + C++ 端侧推理学习笔记

## 这一关在证明什么

Python 里训好的 LSTM，可以导出成 **ONNX**，再用 **C++ / ONNX Runtime** 跑通，并量到真实延迟。

角色分工：

| 组件 | 职责 |
|------|------|
| PyTorch | 训练 |
| ONNX | 模型交换格式 |
| ONNX Runtime C++ | 端侧推理引擎 |
| 预缩放 CSV | 本关把「窗口+标准化」先在 Python 做好，C++ 专注模型推理与性能 |

后续可把 scaler 也搬进 C++（sidecar JSON 已含 mean/scale）。

## 复现步骤

```powershell
# 1) 导出
.\.venv\Scripts\python.exe scripts\export_lstm_onnx.py

# 2) 构建（需 MinGW + CMake；本机用 WinLibs）
cd cpp_inference
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4

# 3) 推理
.\build\edgepdm_infer.exe ..\models\onnx\rul_lstm.onnx ..\models\onnx\sample_window_unit1_scaled.csv 5 50
```

ONNX Runtime 预编译包放在：

`third_party/onnxruntime-win-x64-1.20.1/`  
（MinGW 需用 `gendef`+`dlltool` 生成 `libonnxruntime.a`）

## 实测结果（本机）

| 项 | 值 |
|----|-----|
| Python ORT pred (unit1) | 118.4717 |
| C++ ORT pred (unit1) | 118.472 |
| 平均延迟 | **≈ 0.167 ms** / 次（warmup=5, iters=50, 1 thread） |
| 延迟倒数 | ≈ 5988 次/秒（`1000/0.167`，单线程，不是并发吞吐） |

与 `true_rul_unit1=112` 的误差属于模型误差，不是部署误差（C++/Python 一致）。

## 面试可讲点

1. 为什么 ONNX：解耦训练框架与部署语言  
2. 为什么先导出 scaled window：降低第一版 C++ 复杂度，先打通推理与 benchmark  
3. MinGW 链接官方 MSVC 版 ORT：通过 DLL + import lib（`OrtGetApiBase` C ABI）
