# 05 全过程时间线与痕迹索引（定稿）

> 本文是「从头到尾怎么走过这个项目」的主索引。  
> 每一行都能点到具体文件：计划 → 执行 → 出错 → 改正 → 审核 → 放行。

项目根：`E:\EdgePdM-Agent`  
结项日：2026-07-23（G6 PASS） / 定稿审查：2026-08-06

---

## 总览图

```text
动机与选题争议
  → G0 立项骨架（主管建制）
  → G1 数据理解（下载踩坑 → 改正）
  → G2 Baseline（可量化标尺）
  → G3 LSTM（打赢 baseline）
  → G4 C++ ONNX（无编译器/链接坑 → 改正）
  → G5 llama.cpp 解释（小模型局限诚实记录）
  → G6 结项包装
  → 定稿审查（角色治理 + 全过程索引）
  → 结项后：马拉松超参扫描（旁证，不替换正式模型）
```

---

## 阶段 0：选题与动机（立项前）

| 痕迹类型 | 路径 | 内容 |
|----------|------|------|
| 心路 | `notes/mindset_journal.md` | 投递不顺；手册 RAG/微调为何放弃 |
| 决策 | `docs/02_decision_record.md` ADR-001/002 | C-MAPSS + C++ + 本地 LLM；复现+扩展 |
| 简报 | `docs/00_project_brief.md` | 一句话目标与非目标 |

**关键思考（摘要）**：不是因为「航空发动机」，而是公开数据 + 可补 C++ 短板；承认「有现成 GitHub」是启动理由，但对外必须是复现+扩展。

---

## G0：立项与骨架

| 步骤 | 痕迹 |
|------|------|
| 建目录 / git | `notes/work_log.md`；试错 T-001 |
| 主管制度 | `.cursor/agents/project-manager.md`；ADR-004 |
| 计划与 Gate | `docs/01_delivery_plan.md`；`docs/gates/G0.md`～`G6.md` |
| 审核 | `review_log.md` → G0 PASS |

会议纪要：`docs/meetings/2026-07-23_G0_kickoff.md`

---

## G1：数据与任务理解

| 步骤 | 痕迹 |
|------|------|
| 下载数据 | Zenodo；`data/README.md`；T-002 |
| 环境 | `.venv`；T-003（无 pandas → 建 venv） |
| 学习 | `notes/learning_cmapss.md`（含面试五问） |
| 教程 | `docs/tutorials/00_project_walkthrough_for_beginners.md` |
| 审核 | G1 PASS |

会议纪要：`docs/meetings/2026-07-23_G1_data_sync.md`

---

## G2：Baseline 复现

| 步骤 | 痕迹 |
|------|------|
| 代码 | `src/data.py` `features.py` `metrics.py`；`scripts/run_baseline_fd001.py` |
| 实验 | `experiments/exp_20260722_baseline_xgb_ridge/` |
| 学习 | `notes/learning_baseline.md` |
| 结果 | XGB RMSE≈17.48；Ridge≈20.84 |
| 决策 | 选定 XGBoost 为表格对照（见 iteration_log） |
| 审核 | G2 PASS |

会议纪要：`docs/meetings/2026-07-23_G2_baseline_review.md`

---

## G3：序列模型

| 步骤 | 痕迹 |
|------|------|
| 代码 | `src/sequence.py` `lstm_model.py`；`scripts/run_lstm_fd001.py` |
| 实验 | `experiments/exp_20260722_lstm_fd001/` |
| 对比 | LSTM RMSE≈14.27 优于 XGB 17.48 |
| 学习 | `notes/learning_lstm.md` |
| 决策 | ADR-005：主模型候选 LSTM，部署可先 ONNX |
| 审核 | G3 PASS |

会议纪要：`docs/meetings/2026-07-23_G3_lstm_compare.md`

---

## G4：C++ ONNX 端侧推理

| 步骤 | 痕迹 |
|------|------|
| 导出 | `scripts/export_lstm_onnx.py`；T-005（dynamo/GBK） |
| 工具链 | T-004（装 WinLibs）；T-006（dlltool 导库） |
| 代码 | `cpp_inference/` |
| 实验 | `experiments/exp_20260723_cpp_onnx_infer/`（延迟≈0.17ms） |
| 学习 | `notes/learning_onnx_cpp.md` |
| 决策 | ADR-006：第一版 C++ 吃预缩放窗口，先打通推理 |
| 审核 | G4 PASS |

会议纪要：`docs/meetings/2026-07-23_G4_cpp_onnx.md`

---

## G5：llama.cpp 解释层

| 步骤 | 痕迹 |
|------|------|
| 服务 | `third_party/llama-cpp/`；`scripts/start_llama_server.ps1` |
| 客户端 | `agent/explain_client.py` |
| 示例 | `agent/examples/case0{1-5}_*`（5 条） |
| 诚实局限 | 0.5B 偶发误解字段；实验 notes 已写 |
| 决策 | ADR-007：LLM 只解释，不预测 RUL |
| 审核 | G5 PASS |

会议纪要：`docs/meetings/2026-07-23_G5_llm_boundary.md`

---

## G6：结项包装

| 步骤 | 痕迹 |
|------|------|
| README 复现 | `README.md` |
| 架构 / benchmark / 简历 | `assets/design/architecture.md`；`docs/benchmark_summary.md`；`docs/resume_project_bullet.md` |
| 复盘 | `notes/mindset_journal.md` 结项段；`iteration_log` Iteration 5 |
| 审核 | G6 PASS → COMPLETE |

会议纪要：`docs/meetings/2026-07-23_G6_closeout.md`

---

## 定稿审查（2026-08-06）

| 步骤 | 痕迹 |
|------|------|
| 角色治理 | `docs/04_roles_and_governance.md`；`project-lead` subagent |
| 全过程索引 | 本文 |
| 会议全集 | `docs/meetings/` |
| 定稿报告 | `docs/06_final_delivery_audit.md` |
| 阅读入口 | `docs/INDEX.md` |

---

## 结项后：马拉松超参扫描（2026-08-20 入库）

| 步骤 | 痕迹 |
|------|------|
| 动机 | 闲时验证「正式 14.27 是否单次运气」；补 MC Dropout |
| 脚本 | `training_marathon.py` |
| 产物 | `experiments/r01_*`～`r03_*`（主）；`r05_*`～`r07_*`（崩溃残留） |
| 故事与数字 | `experiments/marathon_sweep_notes.md` |
| 决策 | ADR-009：旁证不替换正式 LSTM/ONNX |
| 迭代 | `docs/iteration_log.md` Iteration 6 |
| 会议 | `docs/meetings/2026-08-20_marathon_sweep_story.md` |

**关键思考（摘要）**：同一任务上的真扫描有价值，但端侧链路与简历主数字仍跟七月正式实验走；扫描最优约 13.10 要进主线必须另开 G7。

---

## 错误 → 改正速查表

| ID | 阶段 | 一句话 |
|----|------|--------|
| T-001 | G0 | create_project 失败 → 手工 git init |
| T-002 | G1 | NASA 门户不便 → Zenodo + 行数校验 |
| T-003 | G1 | 无 pandas → 项目 venv |
| T-004 | G4 | 无编译器 → WinLibs |
| T-005 | G4 | ONNX dynamo/GBK → legacy export |
| T-006 | G4 | MSVC lib 不兼容 MinGW → gendef/dlltool |
| T-007 | G5 | GGUF URL 404 → 换 bartowski 路径（见 trial_error） |
| T-008 | G5 | 0.5B 胡编 RUL 含义 → 文档强调边界+可换大模型 |
| T-009 | 结项后 | 马拉松 rotate 崩溃留下 r05–r07 → 文档标明残留，可择机删 |

---

## 给接手者的 30 分钟阅读路径

1. `docs/INDEX.md`（2 min）  
2. `docs/05_full_process_timeline.md`（本文，8 min）  
3. `notes/mindset_journal.md` + `trial_error_log.md`（8 min）  
4. `docs/benchmark_summary.md` + 任选一个 `experiments/exp_*/notes.md`（7 min）  
5. `docs/gates/review_log.md` 扫一眼审核链（5 min）  
6. （可选）`experiments/marathon_sweep_notes.md`：结项后消融旁证（3 min）  
