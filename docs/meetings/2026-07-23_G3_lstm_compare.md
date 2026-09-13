# 会议纪要 — G3 LSTM 对比

- 日期：2026-07-23
- 出席：负责人、主管

## 汇报

- LSTM window=30，test RMSE≈14.27，优于 XGB 17.48；Score 大幅下降  
- 验证按 unit 划分；best checkpoint 用于测试

## 决策讨论

- **负责人倾向**：部署也上 LSTM（效果更好）  
- **主管提醒**：C++ 第一版要可交付；允许先 ONNX 化 LSTM，但特征工程可分期  
- **决议**：ADR-005 — 主模型候选 LSTM；G4 以打通推理为先

## 审核结果

G3 **PASS**
