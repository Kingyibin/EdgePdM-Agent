# EdgePdM-Agent

端侧预测性维护与本地 LLM 诊断解释系统。

> NASA C-MAPSS 多传感器时间序列 → RUL 预测 → C++/ONNX 端侧推理 → llama.cpp 本地解释。

**当前状态**：G0–G6 均已 PASS，项目 COMPLETE（见 `docs/gates/CURRENT_GATE.md`）。

---

## 为什么做

补齐 C++ AI 工程 / 端侧部署 / Agent 解释能力；用公开 benchmark 避免「手册资料不足」。  
动机与叙事：`notes/mindset_journal.md`、`docs/02_decision_record.md`。

**全过程入口（推荐先读）**：`docs/INDEX.md`  
**时间线与痕迹地图**：`docs/05_full_process_timeline.md`  
**定稿审查**：`docs/06_final_delivery_audit.md`  
**角色治理**：`docs/04_roles_and_governance.md`

初学者技术主线：

1. `docs/tutorials/00_project_walkthrough_for_beginners.md`
2. `notes/learning_cmapss.md`
3. 本文「快速复现」

---

## 架构

见 `assets/design/architecture.md`。指标见 `docs/benchmark_summary.md`。

```text
C-MAPSS → Python 训练(XGBoost/LSTM) → ONNX → C++ ORT → JSON → llama-server 解释
```

---

## 环境

```powershell
cd E:\EdgePdM-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

额外工具链（G4）：WinLibs（cmake/g++），ONNX Runtime 见 `cpp_inference/README.md`。  
额外资源（G5）：llama.cpp release + GGUF，见 `agent/README.md`。

---

## 数据

按 `data/README.md` 下载 Zenodo `CMAPSSData.zip`，放置：

```text
data/raw/train_FD001.txt
data/raw/test_FD001.txt
data/raw/RUL_FD001.txt
```

---

## 快速复现

### 1) Baseline + LSTM

```powershell
python scripts\run_baseline_fd001.py
python scripts\run_lstm_fd001.py
```

### 2) ONNX + C++

```powershell
python scripts\export_lstm_onnx.py
cd cpp_inference
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
.\build\edgepdm_infer.exe ..\models\onnx\rul_lstm.onnx ..\models\onnx\sample_window_unit1_scaled.csv 5 50
```

### 3) 本地 LLM 解释

```powershell
.\scripts\start_llama_server.ps1
python agent\explain_client.py --json agent\examples\case01_warning.json
```

---

## 关键结果（摘要）

| 项 | 结果 |
|----|------|
| XGBoost RMSE (capped125) | 17.48 |
| LSTM RMSE (capped125) | **14.27** |
| C++ ORT 延迟 | **≈0.17 ms** |
| LLM | 5 条结构化解释示例 |

简历条目草稿：`docs/resume_project_bullet.md`。

---

## 目录

| 路径 | 用途 |
|------|------|
| `docs/` | 计划、决策、Gate、教程、benchmark |
| `notes/` | 日志、心路、试错、学习笔记 |
| `experiments/` | 实验指标与结论 |
| `src/` / `scripts/` | Python 训练与导出 |
| `cpp_inference/` | C++ 推理 |
| `agent/` | llama.cpp 解释客户端 |
| `.cursor/agents/project-manager.md` | 关卡审核主管 |

## 工作方式

每完成一个 Gate → 调用 **project-manager** 审核 → 仅 PASS 进入下一关。

## 参考

- https://github.com/eastani/predictive-maintenance-cmapss
- https://github.com/salarsadek/turbofan-rul-time-series-ml
- https://github.com/ggml-org/llama.cpp
- https://github.com/microsoft/onnxruntime
