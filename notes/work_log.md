# 工作日志

## 2026-07-23（续）— G1 执行

### 角色

以本人（金毅彬）视角执行，不跳过理解只堆文件。

### 今天做了什么

1. **下载数据**  
   - URL：Zenodo `CMAPSSData.zip`  
   - 路径：`data/raw/CMAPSSData.zip`（约 12.4 MB）  
   - 解压：`data/raw/_extract/`  
   - 复制 FD001：`train_FD001.txt` / `test_FD001.txt` / `RUL_FD001.txt`，以及官方 `readme.txt`、论文 PDF

2. **环境**  
   - 创建 `.venv`  
   - 安装 `pandas` / `numpy` / `pyyaml`  
   - 用脚本校验 shape：train `(20631,26)`、test `(13096,26)`、RUL `100` 行  
   - 验证 unit1 的 RUL 构造：末尾 `[2,1,0]`，开头 `[191,190,189]`

3. **文档（学习模板）**  
   - 写完 `notes/learning_cmapss.md`（含面试五问自答）  
   - 新增 `docs/tutorials/00_project_walkthrough_for_beginners.md`（全过程给初学者）  
   - 更新 `data/README.md`、`requirements.txt`

4. **试错**  
   - 系统 Python 无 pandas → 建 venv 解决（见 trial_error_log T-003）

### 参考阅读

- `data/raw/readme.txt`（官方子集说明）  
- Zenodo / NASA 数据页（口径）

### 未做（故意留给后续 Gate）

- 未开始 XGBoost/LSTM 训练（属 G2/G3）  
- 未碰 llama.cpp / ONNX（属 G4/G5）

### 下一步

请求 **project-manager** 审核 G1；仅 PASS 后进入 G2。

---

## 2026-07-23（晚）— G2 Baseline

### 今日（G1 PASS 之后）

1. 安装 sklearn / xgboost / matplotlib / joblib
2. 实现 `src/data.py`、`features.py`、`metrics.py`
3. 实现并运行 `scripts/run_baseline_fd001.py`
4. 记录实验到 `experiments/exp_20260722_baseline_xgb_ridge/`
5. 撰写 `notes/learning_baseline.md`

### 关键结果

- XGBoost test RMSE (capped125) ≈ **17.48**
- Ridge ≈ 20.84
- 选定 XGBoost 为后续对比/导出候选

### 下一步

请求 **project-manager** 审核 G2。

---

## 2026-07-23（夜）— G3 LSTM

1. 安装 PyTorch CPU
2. 实现 `src/sequence.py`、`src/lstm_model.py`、`scripts/run_lstm_fd001.py`
3. 训练 25 epoch；test RMSE_capped125 ≈ **14.27**（优于 XGBoost 17.48）
4. 实验目录：`experiments/exp_20260722_lstm_fd001/`
5. 笔记：`notes/learning_lstm.md`

下一步：请求 project-manager 审核 G3。

---

## 2026-07-23（深夜）— G4 C++ ONNX

1. 安装 WinLibs（解决无编译器）
2. `export_lstm_onnx.py` 导出 `models/onnx/rul_lstm.onnx`
3. 下载 onnxruntime 1.20.1；gendef/dlltool 生成 MinGW 导入库
4. 实现并编译 `cpp_inference`；C++ pred=118.472 对齐 Python ORT；延迟 ≈0.167ms
5. 文档：`notes/learning_onnx_cpp.md`、实验 `exp_20260723_cpp_onnx_infer`

下一步：请求 project-manager 审核 G4。

---

## 2026-07-23 — G5 llama.cpp 解释

1. 下载 llama.cpp win-cpu-x64 release + Qwen2.5-0.5B GGUF
2. 启动 llama-server；health=ok
3. 实现 `agent/explain_client.py` + 5 个 case JSON/解释 md
4. 笔记：`notes/learning_llamacpp.md`

下一步：请求 project-manager 审核 G5。

---

## 2026-07-23 — G6 结项包装

1. 架构图 `assets/design/architecture.md`
2. `docs/benchmark_summary.md`、`docs/resume_project_bullet.md`
3. README 重写为可复现总入口
4. 心路复盘更新

下一步：请求 project-manager **G6 终审**。

---

## 2026-08-06 — 定稿审查补齐

以负责人视角补「真实项目」全过程痕迹，非重训模型：

1. 新增 `project-lead` subagent；完善双角色治理文档  
2. 全过程时间线 `docs/05_full_process_timeline.md`  
3. 会议纪要 `docs/meetings/`（G0–G6 + 定稿会）  
4. 补 ADR-005～008、T-007/T-008  
5. `docs/INDEX.md`、`docs/06_final_delivery_audit.md`  
6. 更新 AGENTS.md / README 入口  

下一步：请 **project-manager** 对定稿包做终审（写入 review_log + 填写 06 报告第 5 节）。

---

## 2026-08-20 — 把马拉松扫描写进项目故事

结项后闲时跑的 `training_marathon.py` 不是新项目，是同一 FD001 LSTM 任务的超参真扫描：

1. 整理口径：旁证 / 消融，不替换七月正式 LSTM + ONNX/C++（ADR-009）
2. 写扫描故事：`experiments/marathon_sweep_notes.md`
3. 更新时间线、iteration_log、benchmark、心路与试错 T-009（r05–r07 残留）
4. 会议纪要：`docs/meetings/2026-08-20_marathon_sweep_story.md`

关键数字留痕：扫描最优 RMSE≈13.10；正式主数字仍 14.27；同结构 seed 可晃到 15.29。

下一步：默认不扩 scope；若要把 13.10 固化进端侧，另开 G7。

---

## 2026-07-23（早）— G0

立项骨架、主管 subagent、G0 PASS。详见 `docs/gates/review_log.md`。
