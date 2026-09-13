# Experiment: llama.cpp structured explanation

- Gate：G5
- Server：llama-server b10091 CPU
- Model：Qwen2.5-0.5B-Instruct-Q4_K_M.gguf
- Client：`agent/explain_client.py`

## 示例

| Case | 输入 | 输出文件 |
|------|------|----------|
| warning | case01_warning.json | case01_warning_explanation.md |
| healthy | case02_healthy.json | case02_healthy_explanation.md |
| urgent | case03_urgent.json | case03_urgent_explanation.md |
| monitor | case04_monitor.json | case04_monitor_explanation.md |
| uncertain | case05_uncertain.json | case05_uncertain_explanation.md |

## 结论

链路打通：结构化 JSON → 本地 LLM 建议。  
0.5B 模型存在措辞不准/偶发误解字段（如把 RUL 说成年），**这在笔记中诚实记录**；价值在工程边界与可替换模型，而非宣称「小模型诊断专家」。
