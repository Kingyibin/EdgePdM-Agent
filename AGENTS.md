# AGENTS.md — EdgePdM-Agent

署名：金毅彬（项目负责人 / Lead） · project-manager（主管审核） · project-lead（执行提审）

## 项目定位

端侧预测性维护与本地 LLM 诊断解释系统。

- 数据：NASA C-MAPSS（公开 benchmark，非企业保密手册）
- 算法：RUL 回归 / 风险等级 / 异常传感器分析
- 工程：Python 训练 → ONNX → C++ 端侧推理
- 大模型：`llama.cpp` 只做结构化结果的自然语言解释

## 双角色治理（必读）

详见 `docs/04_roles_and_governance.md`。

| 角色 | Subagent | 职责 |
|------|----------|------|
| 项目主管 | `.cursor/agents/project-manager.md` | 拆阶段、验收、PASS/FAIL、放行 |
| 项目负责人 | `.cursor/agents/project-lead.md` | 执行、留痕、提审、返工 |

**负责人不得自行宣布 Gate PASS。**

## 目录规则

| 路径 | 用途 |
|------|------|
| `docs/` | PRD、计划、决策、Gate、会议、定稿、索引 |
| `docs/meetings/` | 各阶段同步/评审纪要 |
| `notes/` | 工作日志、心路、试错、学习笔记 |
| `experiments/` | 单次实验记录与指标 |
| `src/` / `scripts/` | Python 代码与入口 |
| `cpp_inference/` | C++ ONNX 推理 |
| `agent/` | llama.cpp 解释层 |
| `data/` | 数据说明与 raw（大文件可 gitignore） |
| `assets/` | 架构图等 |
| `.cursor/agents/` | 主管 / 负责人 subagent |

## 开发规则

1. **一步一 Gate**：完成后由 **project-manager** 审核，PASS 才能下一步。
2. 执行侧优先用 **project-lead** 组织提审包与留痕。
3. 正式结论写 `docs/`；探索与情绪写 `notes/`。
4. 每次实验写 `experiments/` 并更新 `docs/iteration_log.md`。
5. 关键取舍写 `docs/02_decision_record.md`。
6. 错误必须进 `notes/trial_error_log.md`（现象→原因→处理→预防）。
7. 禁止伪造实验数字；禁止手册 RAG 主线；LLM 不预测 RUL。
8. 库代码不写死本机绝对路径。

## 全过程从哪读起

1. `docs/INDEX.md`
2. `docs/05_full_process_timeline.md`
3. `docs/06_final_delivery_audit.md`

## 主参考（复现 + 扩展）

1. https://github.com/eastani/predictive-maintenance-cmapss
2. https://github.com/salarsadek/turbofan-rul-time-series-ml
3. https://github.com/ggml-org/llama.cpp
4. https://github.com/microsoft/onnxruntime

## 开始顺序（新人）

1. 读 `docs/INDEX.md`
2. 读 `README.md` 与 `docs/00_project_brief.md`
3. 读 `docs/gates/CURRENT_GATE.md`
4. 用 project-lead 推进 / 用 project-manager 审核
