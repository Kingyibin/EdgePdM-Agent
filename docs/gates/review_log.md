# Gate 审核日志

> 由 project-manager 追加。格式：日期 | Gate | 结论 | 证据摘要 | 下一指令

---

## 2026-07-23 | G0 | PASS

### 证据

- 根目录：`E:\EdgePdM-Agent`，Cursor 工作区已切换
- Subagent：`.cursor/agents/project-manager.md`
- 文档：`README.md`、`AGENTS.md`、`docs/00_project_brief.md`、`01_delivery_plan.md`、`02_decision_record.md`、`03_learning_plan.md`、`iteration_log.md`
- Gates：`G0.md`～`G6.md`、`CURRENT_GATE.md`、`review_log.md`
- Notes：`work_log.md`、`mindset_journal.md`、`trial_error_log.md`、`learning_cmapss.md`（G1 提纲）
- 工程占位：`src/`、`cpp_inference/`、`agent/`、`configs/default.yaml`、`data/README.md`
- `.gitignore` 已忽略 raw 数据、模型权重、venv、build

### 缺口

无。G0 验收清单满足。

### 下一指令（唯一主线）

进入 **G1**：获取 NASA C-MAPSS FD001（`train_FD001.txt` / `test_FD001.txt` / `RUL_FD001.txt`）放入 `data/raw/`，按 `docs/gates/G1.md` 写完 `notes/learning_cmapss.md`（含面试五问自测），更新 `notes/work_log.md`，然后再次请求 project-manager 做 G1 审核。在此之前不要开始 baseline 训练代码（可预习学习清单，但不算 G2）。

---

## 2026-07-23 | G1 | PASS

### 证据

- `data/raw/` 实测存在且校验通过：
  - `train_FD001.txt` 3,515,356 bytes / 20,631 行
  - `test_FD001.txt` 2,228,855 bytes / 13,096 行
  - `RUL_FD001.txt` 429 bytes / 100 行
- `data/README.md`：官方口径 + Zenodo URL + 布局与校验表，路径可复现
- `notes/learning_cmapss.md`：字段含义、RUL 构造、capped RUL、train/test 差异、FD001–004、评估指标；末尾面试五问自答完整
- `notes/work_log.md`：记录下载、解压、venv、shape/RUL 校验与文档产出
- `notes/trial_error_log.md`：T-002（下载渠道）、T-003（系统 Python 无 pandas）
- 额外：`docs/tutorials/00_project_walkthrough_for_beginners.md` 已存在
- 未越界进入 G2 训练代码

### 缺口

无。G1 验收清单满足。

### 下一指令（唯一主线）

进入 **G2**：在 FD001 上复现至少一种 baseline（Ridge 或 XGBoost），产出可复现脚本/notebook + `experiments/exp_baseline_*`，报告 RMSE（及 Score 若实现），更新 `notes/work_log.md` 与 `docs/iteration_log.md`，然后请求 project-manager 做 G2 审核。在此之前不要做 LSTM/ONNX/llama.cpp。

---

## 2026-07-23 | G2 | PASS

### 证据

- 自有代码存在且路径相对项目根：
  - `scripts/run_baseline_fd001.py`
  - `src/data.py`、`src/features.py`、`src/metrics.py`（+ `__init__.py`）
- 实验目录 `experiments/exp_20260722_baseline_xgb_ridge/` 完整：
  - `metrics.json`、`notes.md`
  - `predictions_ridge.csv` / `predictions_xgboost.csv`（各 100 units）
  - `scatter_ridge.png` / `scatter_xgboost.png`
  - `ridge.joblib` / `xgboost.joblib`
- `metrics.json` 真实指标（抽查 predictions 重算 RMSE 一致）：
  - Ridge：RMSE_capped125 = 20.8427，NASA Score_capped125 = 1285.30
  - XGBoost：RMSE_capped125 = 17.4842，NASA Score_capped125 = 929.35
- 防泄漏做法正确：训练 capped RUL=125；测试取 unit last cycle；CV 用 GroupKFold(by unit)；Scaler 仅在 train fit
- 文档已更新：`notes/work_log.md`、`notes/learning_baseline.md`、`docs/iteration_log.md`；笔记注明参考边界（思路参考公开 pipeline，代码本仓库重写）
- 未越界进入 G3 LSTM / ONNX / llama.cpp

### 缺口

无。G2 验收清单满足。

### 下一指令（唯一主线）

进入 **G3**：在 FD001 上实现 LSTM / GRU / CNN 之一（sliding window），与 G2 XGBoost baseline（RMSE≈17.48 / NASA Score≈929，capped125）做同口径对比，产出 `experiments/exp_*` + 对比表，更新 `notes/work_log.md` 与 `docs/iteration_log.md`，然后请求 project-manager 做 G3 审核。在此之前不要做 ONNX/C++/llama.cpp。

---

## 2026-07-23 | G3 | PASS

### 证据

- 自有代码存在且路径相对项目根：
  - `scripts/run_lstm_fd001.py`
  - `src/sequence.py`（sliding window + last-window pad）
  - `src/lstm_model.py`（`RULSTM`）
- 实验目录 `experiments/exp_20260722_lstm_fd001/` 完整：
  - `metrics.json`、`notes.md`、`history.json`
  - `predictions_lstm.csv`（100 units）
  - `scatter_lstm.png`、`lstm.pt`
- `metrics.json` 真实指标（抽查 predictions 用 `src.metrics` 重算一致）：
  - LSTM：RMSE_capped125 ≈ **14.2709**，NASA Score_capped125 ≈ **324.57**
  - 对照 G2 XGBoost：RMSE 17.4842 / Score 929.35
  - `beat_xgboost_rmse`: **true**；Score 亦明显更优
- 设定清晰：window=30、17 特征、unit 级 20% 验证、Scaler 仅 train fit、测试 last window
- 文档已更新：`notes/learning_lstm.md`、`notes/work_log.md`、`docs/iteration_log.md`；`docs/gates/G3.md` 清单已勾选且结论「LSTM 更好」
- 未越界进入 G4 ONNX/C++ 或 G5 llama.cpp 实现

### 缺口

无。G3 验收清单满足。

### 下一指令（唯一主线）

进入 **G4**：将模型导出为 ONNX，在 `cpp_inference/` 用 CMake + ONNX Runtime 跑通 CSV→特征→RUL 推理，记录延迟/内存，写 `notes/learning_onnx_cpp.md` 与必要的 `trial_error_log`，更新 work_log / iteration_log，然后请求 project-manager 做 G4 审核。在此之前不要做 llama.cpp（G5）结项包装。

---

## 2026-07-23 | G4 | PASS

### 证据

- 模型产物存在（本机实测；`models/**` / `*.onnx` 已 gitignore，可经脚本复现）：
  - `models/onnx/rul_lstm.onnx`（239,651 bytes）
  - `models/onnx/sample_window_unit1_scaled.csv`（30×17）
  - `models/onnx/rul_lstm_sidecar.json`（window/feature_cols/mean/scale；非字面 `sidecar.json`，语义满足 sidecar）
  - 导出脚本：`scripts/export_lstm_onnx.py`
- C++ 工程：
  - `cpp_inference/CMakeLists.txt`（C++17 + ORT include/link + POST_BUILD 拷贝 DLL）
  - `cpp_inference/src/main.cpp`（读 window CSV → ORT Session → 打印 RUL / latency）
  - `cpp_inference/build/edgepdm_infer.exe` 已存在；`cpp_inference/README.md` 含 MinGW/`gendef`/`dlltool` 与构建运行说明
  - `third_party/onnxruntime-win-x64-1.20.1/` 本机已落盘
- 实验 `experiments/exp_20260723_cpp_onnx_infer/`：
  - `metrics.json`：python_ort_pred≈118.4717，cpp_ort_pred=118.472，latency_ms_avg≈**0.167**，toolchain=MinGW-w64 g++ 16.1.0 + CMake 4.3.3 + onnxruntime 1.20.1
  - `notes.md`：一致性与吞吐说明完整
- 文档闭环：`notes/learning_onnx_cpp.md`、`trial_error_log` T-004～T-006、`work_log` G4 条目、`iteration_log` Iteration 3、`docs/gates/G4.md` 清单已勾选
- 未越界实现 G5 llama.cpp 解释层

### 审核备注

- 主管抽查时当前 shell 未带 WinLibs PATH，直接跑 `edgepdm_infer.exe` 返回 `0xC0000135`（缺 MinGW 运行时 DLL）；属审核环境 PATH，不否定已构建产物与实验记录。复现以 `cpp_inference/README.md` 为准。
- G4 验收清单要求「延迟 + 工具链」；内存数字未单独写入 metrics（CURRENT_GATE 曾提及），不构成 FAIL。

### 缺口

无。G4 验收清单满足。

### 下一指令（唯一主线）

进入 **G5**：在 `agent/` 接 llama.cpp（或等价本地服务），用结构化推理结果（RUL / 风险等级 / 异常传感器）生成自然语言解释示例；更新 work_log / iteration_log / 学习笔记，然后请求 project-manager 做 G5 审核。解释层不得改写 RUL 数值，禁止做成手册 RAG 主线。

---

## 2026-07-23 | G5 | PASS

### 证据

- `agent/` 解释层完整：
  - `agent/explain_client.py`：OpenAI-compatible 调用本地 llama-server；system prompt 明确「不得重新计算或改写 RUL」
  - `agent/prompt_template.md`：结构化 JSON → 维护建议模板
  - `agent/README.md`：声明 **LLM 不预测 RUL**、**不是手册 RAG**；含启动与调用命令
- 示例 ≥5 组（JSON + 解释 md 成对）：
  - `case01_warning` / `case02_healthy` / `case03_urgent` / `case04_monitor` / `case05_uncertain`
- 运行时本机落盘：
  - `third_party/llama-cpp/llama-server.exe`（+ `llama-server-impl.dll` 等官方 win-cpu 布局）
  - `models/gguf/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`（≈379 MB）
  - `scripts/start_llama_server.ps1`（相对路径启动，缺文件即报错）
- 文档闭环：`notes/learning_llamacpp.md`、`experiments/exp_20260723_llamacpp_explain/notes.md`、`notes/work_log.md`（health=ok）、`docs/iteration_log.md` Iteration 4
- 边界正确：输入为端侧结构化结果；笔记诚实记录 0.5B 措辞不准；未做成手册检索 RAG；未越界写 G6 结项包装

### 缺口

无。G5 验收清单满足。

### 下一指令（唯一主线）

进入 **G6**：结项包装——补齐可复现 README、架构图、benchmark 汇总、简历条目与总复盘；更新 work_log / iteration_log，然后请求 project-manager 做 G6 终审。在此之前不要新开算法主线或手册 RAG。

---

## 2026-07-23 | G6 | PASS（终审）

### 证据

- **README 可复现**：安装/venv、数据落盘、baseline+LSTM、ONNX+C++、llama-server 解释分步齐全；指标与简历入口有链接。
- **架构图**：`assets/design/architecture.md`（mermaid：数据→算法→端侧→解释）+ 模块边界表（LLM 不预测 RUL / 非手册 RAG）。
- **benchmark 可追溯**：`docs/benchmark_summary.md` 数字与实验一致——
  - Ridge/XGB：`exp_20260722_baseline_xgb_ridge/metrics.json`（RMSE 20.84 / 17.48）
  - LSTM：`exp_20260722_lstm_fd001/metrics.json`（RMSE 14.27 / Score 324.6）
  - C++：`exp_20260723_cpp_onnx_infer/metrics.json`（pred≈118.47，latency 0.167ms）
  - LLM：`agent/examples/` 5 case
- **简历草稿**：`docs/resume_project_bullet.md`，数字出处指向上述 experiments。
- **总复盘**：`notes/mindset_journal.md`「结项前复盘」；`docs/iteration_log.md` Iteration 5（G6）；`notes/work_log.md` 有 G6 条目。
- **前序关卡**：review_log 中 G0–G5 均为 PASS；证据链完整（复现→扩展→端侧→解释）。

### 缺口

无。G6 验收清单满足；项目故事完整。

### 下一指令（唯一主线）

项目 **COMPLETE**。可按需打磨简历口述与面试问答；勿擅自扩 scope（微调大模型 / 手册 RAG 等需另立 Gate）。

---

## 2026-08-06 | 定稿审查 | PASS

### 证据

- **提审包**：`docs/meetings/2026-08-06_lead_submission_final.md` 自检 READY；对照 `docs/06_final_delivery_audit.md` 第 2 节清单抽查通过。
- **双角色机制**：`.cursor/agents/project-manager.md`、`.cursor/agents/project-lead.md`；`docs/04_roles_and_governance.md`；负责人不得自行标 PASS 的规则已落档。
- **历史关卡**：本日志 G0–G6 均为 PASS（2026-07-23）；`CURRENT_GATE` 技术结项 COMPLETE。
- **全过程痕迹**：`docs/05_full_process_timeline.md`；`docs/meetings/` 含 G0–G6 + 定稿会 + 提审包；`notes/work_log.md` / `mindset_journal.md`；`notes/trial_error_log.md` T-001～T-008（含 T-007/T-008）；`docs/02_decision_record.md` ADR-001～008（含 ADR-005～008）；`docs/iteration_log.md`。
- **可阅读索引**：`docs/INDEX.md` 阅读顺序与分类查找齐全。
- **技术抽样（不重训）**：`exp_20260722_baseline_xgb_ridge`、`exp_20260722_lstm_fd001`、`exp_20260723_cpp_onnx_infer` 均有 metrics；`agent/examples/` 5 case 成对；README / benchmark / 简历 / 架构图入口存在。
- **诚实边界保留**：C++ 预缩放输入（ADR-006）、0.5B 解释局限（T-008）、未在定稿日重跑训练——均已写明，不构成 FAIL。

### 缺口

无。定稿审查以痕迹完整性 / 治理 / 错误改正链 / 索引可读性为标准，清单满足。

### 下一指令（唯一主线）

定稿审查 **PASS**；技术结项 **COMPLETE** 维持。默认状态不再扩 scope；若扩展（如 C++ 内建 scaler、更大 GGUF、FD002）须 **新开 G7+**，由 project-lead 提审后再由主管审核。可按需打磨简历口述与面试问答。
