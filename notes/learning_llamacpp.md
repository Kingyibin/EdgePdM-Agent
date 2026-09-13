# G5：llama.cpp 本地解释层学习笔记

## 它在系统里干什么

```text
C++/ONNX 给出：
  { predicted_rul, risk_level, abnormal_sensors, trend }
        ↓
llama-server（本地 GGUF）
        ↓
自然语言维护建议
```

**禁止**：让 LLM 重新算 RUL；禁止做成手册检索 RAG。

## 本机组件

| 组件 | 路径 |
|------|------|
| llama-server | `third_party/llama-cpp/llama-server.exe`（b10091 win-cpu-x64） |
| 模型 | `models/gguf/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` |
| 客户端 | `agent/explain_client.py` |

## 为什么选小模型

- 本机 CPU 可跑、下载可控
- 足够演示链路；生产换 1.5B/3B Instruct 即可
- 小模型会偶发胡编，正好用来强调「结构化约束 + 人工审核」的重要性

## 复现

```powershell
.\scripts\start_llama_server.ps1
# wait health ok
python agent\explain_client.py --json agent\examples\case01_warning.json
```

示例输出：`agent/examples/case0*_explanation.md`（5 条）。
