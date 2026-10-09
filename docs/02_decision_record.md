# 02 决策记录（ADR）

## ADR-001：项目方向定为「C-MAPSS PdM + C++ 推理 + 本地 LLM 解释」

- 日期：2026-07-23
- 状态：已采纳

### 背景

投递方向含 C++、大模型、Agent、嵌入式；简历缺强 C++ AI 工程项目。曾考虑手册型工业诊断 RAG / 纯微调，资料与差异化均不足。

### 决策

以 NASA C-MAPSS 为公开数据主线，做 RUL 预测；Python 训练；C++/ONNX 部署；llama.cpp 仅做解释。

### 替代方案与放弃原因

| 方案 | 放弃原因 |
|------|----------|
| 手册 RAG 诊断 | 手册/案例难获取、质量低、与旧项目重复且难聊深 |
| 纯 LoRA 微调 | 与 C++/端侧短板不匹配，同质化高 |
| 从零手写推理引擎 | 周期长，一周级上手不现实，学习曲线过陡 |

### 后果

必须先吃透数据与 baseline，再谈部署与 LLM；LLM 不得抢预测主线。

---

## ADR-002：允许「因开源项目成熟而启动」，但对外叙事必须是「复现 + 扩展」

- 日期：2026-07-23
- 状态：已采纳

### 决策

真实动机可包含：选资料充足的 GitHub 工程复刻学习。对外强调：复现 eastani pipeline → 扩展 C++ 与 llama.cpp。

### 后果

禁止只交「和别人仓库几乎一样」的代码；扩展点必须可演示。

---

## ADR-003：项目根目录放在 `E:\EdgePdM-Agent`

- 日期：2026-07-23
- 状态：已采纳

### 决策

独立工程盘路径，与港铁/RAG 旧工程隔离；文档/代码按 Gate 生长。

---

## ADR-004：用 project-manager subagent 做 Gate 审核

- 日期：2026-07-23
- 状态：已采纳

### 决策

每阶段结束必须审核；FAIL 不得进入下一阶段。审核记录写入 `docs/gates/review_log.md`。

---

## ADR-005：主模型候选定为 LSTM；表格 XGBoost 保留为对照

- 日期：2026-07-23
- 状态：已采纳
- 依据：G3 对比实验；会议 `docs/meetings/2026-07-23_G3_lstm_compare.md`

### 决策

部署与后续解释层以 LSTM（window=30）为主候选；XGBoost 保留在实验与简历对比表中。

---

## ADR-006：G4 第一版 C++ 输入采用预缩放 window CSV

- 日期：2026-07-23
- 状态：已采纳
- 依据：会议 `docs/meetings/2026-07-23_G4_cpp_onnx.md`

### 决策

先打通 ONNX Runtime 推理与延迟测量；标准化参数写入 sidecar JSON，完整特征工程进 C++ 列为增强项，不阻塞结项。

### 后果

简历/面试必须诚实说明边界，不能声称「全量特征工程已在 C++ 完成」。

---

## ADR-007：llama.cpp 只做结构化解释，不预测 RUL，不做手册 RAG

- 日期：2026-07-23
- 状态：已采纳
- 依据：会议 `docs/meetings/2026-07-23_G5_llm_boundary.md`

### 决策

解释层输入必须是模型产出的 JSON；示例保留小模型真实输出（含瑕疵）以体现诚实；生产可换更大 GGUF。

---

## ADR-008：定稿采用「主管 + 负责人」双角色治理

- 日期：2026-08-06
- 状态：已采纳
- 依据：会议 `docs/meetings/2026-08-06_final_delivery_audit.md`

### 决策

新增 `project-lead` subagent；全过程时间线、会议纪要、定稿审查报告纳入交付物；任何扩 scope 必须重新走 Gate。

---

## ADR-009：马拉松超参扫描只作结项后旁证，不替换正式 LSTM/ONNX

- 日期：2026-08-20
- 状态：已采纳
- 依据：`docs/meetings/2026-08-20_marathon_sweep_story.md`；`experiments/marathon_sweep_notes.md`

### 决策

结项后 `training_marathon.py` 扫描（`experiments/rNN_*`）写入项目故事与消融记录；简历与端侧主数字仍锚定七月 `exp_20260722_lstm_fd001`（RMSE≈14.27 + `lstm.pt` + C++ 对齐）。扫描最优（约 RMSE 13.10）不得静默改写 G3–G6 口径。

### 后果

- 面试可讲：超参/种子敏感、MC Dropout 覆盖率、多数配置仍打赢 XGBoost。
- 若要把扫描最优固化为正式模型，必须另开 **G7**：重训存权 → 导出 ONNX → C++ 复验 → 主管审核。

---

## ADR-010：封盖，正式数字与范围冻结

- 日期：2026-10-08
- 状态：已采纳
- 依据：负责人按现有实验复盘 `predictions_lstm.csv` 后请求封盖；`docs/07_seal_review.md`

### 决策

G0–G6 与 2026-08-06 定稿审查的正式口径保持不变。不新开 G7，不用马拉松最优替换 `lstm.pt` / ONNX。封盖复盘只允许解释已有预测文件，不改写 `metrics.json`。

### 后果

面试新增可讲的分布结论（近失效段更准、Score 由少数乐观误差主导、验证 RMSE 与测试 RMSE 不是同一聚合）以 `docs/07_seal_review.md` 为准。`benchmark_summary` 中的 qps 只作为单线程延迟的倒数，不作为并发能力。
