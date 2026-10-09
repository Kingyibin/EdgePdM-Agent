# agent/ — 本地 LLM 解释层（G5）

## 原则

- **LLM 不预测 RUL**，只解释结构化 JSON（RUL/风险/异常传感器/趋势）
- **不是**工业手册 RAG

## 依赖

1. `third_party/llama-cpp/llama-server.exe`（官方 win-cpu-x64 release）
2. `models/gguf/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`

## 启动服务

```powershell
cd E:\EdgePdM-Agent
.\scripts\start_llama_server.ps1
```

健康检查：`http://127.0.0.1:8080/health`

## 生成解释

```powershell
.\.venv\Scripts\python.exe agent\explain_client.py `
  --json agent\examples\case01_warning.json `
  --out agent\examples\case01_warning_explanation.md
```

批量示例见 `agent/examples/case0*_explanation.md`（至少 5 条）。

## 说明

0.5B 小模型可能出现措辞不严谨；项目价值在于**链路与边界**（结构化结果 → 本地解释）。示例 JSON 是手写夹具，见 `examples/README.md`，不要当成某台发动机的模型输出。
