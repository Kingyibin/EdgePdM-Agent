# 04 角色与治理（定稿）

## 双角色模型

本项目刻意用「主管 + 负责人」双角色，模拟真实小团队推进，而不是一个人闷头写代码。

| 角色 | 谁 | Subagent | 核心权力 |
|------|-----|----------|----------|
| 项目主管（PM / Gate Keeper） | 审核方 | `project-manager` | 拆阶段、定验收、PASS/FAIL/BLOCKED、是否放行下一关 |
| 项目负责人（Lead） | 金毅彬（执行） | `project-lead` | 选型落地、编码实验、试错留痕、提审、按审核返工 |

## 决策流（固定）

```text
负责人提出方案 / 执行当前 Gate
    ↓
写入 work_log / trial_error / experiments / ADR（必要时）
    ↓
负责人自检 → 提审包
    ↓
主管对照 Gx.md 审核
    ├─ PASS → 更新 CURRENT_GATE → 下一关
    ├─ FAIL → 返工清单（禁止跳关）
    └─ BLOCKED → 外部阻塞解除步骤
```

## 文件即权力痕迹

| 动作 | 必须留下的文件 |
|------|----------------|
| 阶段计划 | `docs/01_delivery_plan.md` |
| 关卡状态 | `docs/gates/CURRENT_GATE.md` |
| 审核结论 | `docs/gates/review_log.md` |
| 关键取舍 | `docs/02_decision_record.md` |
| 每日执行 | `notes/work_log.md` |
| 错误与改正 | `notes/trial_error_log.md` |
| 思考动机 | `notes/mindset_journal.md` |
| 实验数字 | `experiments/exp_*/` |
| 会议/同步 | `docs/meetings/` |

## 禁止事项

1. 负责人自行把 Gate 标 PASS  
2. 跳过 FAIL 直接做下一关  
3. 伪造指标或隐瞒失败实验  
4. 把 LLM 解释层说成「预测 RUL」或手册 RAG  

## 如何调用

对 Cursor：

- 「用 **project-lead** 推进当前 Gate / 准备提审」
- 「用 **project-manager** 审核当前 Gate」
