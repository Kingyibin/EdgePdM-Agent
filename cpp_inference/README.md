# cpp_inference/

C++ + ONNX Runtime 端侧推理（G4）。

## 依赖

1. **CMake + g++**（本机：WinLibs via winget）
2. **ONNX Runtime** 预编译包：解压到  
   `../third_party/onnxruntime-win-x64-1.20.1/`  
   下载：https://github.com/microsoft/onnxruntime/releases
3. MinGW 需在 `lib/` 下生成导入库：

```powershell
cd ..\third_party\onnxruntime-win-x64-1.20.1\lib
gendef onnxruntime.dll
dlltool -d onnxruntime.def -l libonnxruntime.a -D onnxruntime.dll
```

## 构建与运行

```powershell
# 先从项目根导出模型
..\..\.venv\Scripts\python.exe ..\..\scripts\export_lstm_onnx.py

cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4

.\build\edgepdm_infer.exe ..\models\onnx\rul_lstm.onnx ..\models\onnx\sample_window_unit1_scaled.csv 5 50
```

（若当前目录是 `cpp_inference`，ONNX 路径用 `..\models\onnx\...`。）

## 设计说明

- 输入为**已缩放**的 window CSV，降低第一版 C++ 特征工程复杂度
- sidecar：`models/onnx/rul_lstm_sidecar.json` 含 mean/scale，便于后续把标准化搬进 C++
