# EdgePdM-Agent 架构图

```mermaid
flowchart TB
  subgraph Data["数据层"]
    A[NASA C-MAPSS FD001<br/>传感器时间序列]
  end

  subgraph Train["算法层 Python"]
    B[RUL 标签 / capped 125]
    C[XGBoost Baseline]
    D[LSTM window=30]
    E[评估 RMSE / NASA Score]
  end

  subgraph Edge["端侧推理 C++"]
    F[导出 ONNX]
    G[ONNX Runtime<br/>edgepdm_infer]
    H[C++ 只打印 RUL<br/>风险等级不在端侧计算]
  end

  subgraph Explain["解释层 本地 LLM"]
    I[llama-server + GGUF]
    J[维护建议中文文本]
  end

  A --> B --> C
  B --> D
  C --> E
  D --> E
  D --> F --> G --> H --> I --> J
```

## 模块边界

| 模块 | 负责 | 不负责 |
|------|------|--------|
| LSTM/XGBoost | 预测 RUL | 写维修话术 |
| C++ ORT | 对预缩放窗口做低延迟推理，打印 RUL | 训练、滚动特征、标准化、风险分级、异常传感器 |
| llama.cpp | 解释 JSON | 预测 RUL / 查手册 RAG |
