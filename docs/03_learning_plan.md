# 03 基础知识学习计划（搜什么）

原则：先业务与数据，再 baseline，再深度模型，再 C++/LLM。不先死磕 Transformer 细节。

## A. 必须先懂（G1 前）

| 主题 | 你要能说清 | 去搜什么 |
|------|------------|----------|
| 预测性维护 | 坏了再修 vs 预测再修 | B站：`预测性维护 入门`；Google：`predictive maintenance tutorial` |
| RUL | 剩余寿命定义与标签构造 | B站：`RUL 剩余寿命预测`；`Remaining Useful Life C-MAPSS` |
| C-MAPSS | 字段、FD001–004、train/test | B站：`C-MAPSS 数据集`；GitHub：`C-MAPSS RUL prediction` |
| capped RUL | 为何截断到 ~125 | Google：`capped RUL C-MAPSS 125` |
| RMSE / NASA score | 怎么评估 | Google：`C-MAPSS scoring function` |

## B. Baseline（G2）

| 主题 | 去搜什么 |
|------|----------|
| XGBoost 回归 | B站：`XGBoost 回归 入门` |
| 时序特征 | B站：`rolling mean rolling std 时间序列`；`时间序列 特征工程` |
| 数据泄漏 | B站：`时间序列 数据泄漏`；`group split by unit id` |

## C. 序列模型（G3）

| 主题 | 去搜什么 |
|------|----------|
| 滑动窗口 | B站：`sliding window 时间序列`；`滑动窗口 LSTM` |
| LSTM/GRU | B站：`PyTorch LSTM 时间序列预测`；`GRU 原理` |
| Transformer（了解即可） | B站：`李宏毅 Transformer`；不必第一阶段手写 |

## D. C++ 部署（G4）

| 主题 | 去搜什么 |
|------|----------|
| CMake | B站：`CMake 入门` |
| ONNX | B站：`PyTorch 导出 ONNX`；`ONNX Runtime C++ 推理` |
| CSV/JSON | B站：`C++ 读取 CSV`；`nlohmann json` |

## E. 本地 LLM（G5）

| 主题 | 去搜什么 |
|------|----------|
| llama.cpp | B站：`llama.cpp 本地部署`；GitHub：`ggml-org/llama.cpp` |
| GGUF / 量化 | B站：`GGUF`；`大模型量化 INT4` |
| 结构化解释 | 自写：JSON 结果 → prompt → 建议（勿做成手册 RAG） |

## 学习笔记落点

- C-MAPSS：`notes/learning_cmapss.md`
- ONNX/C++：`notes/learning_onnx_cpp.md`
- llama.cpp：`notes/learning_llamacpp.md`
- 每日执行：`notes/work_log.md`
