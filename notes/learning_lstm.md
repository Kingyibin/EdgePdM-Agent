# G3 LSTM 学习笔记（给初学者）

## 滑动窗口是什么

把过去 `window` 个 cycle 的传感器排成一段序列，预测该段**最后一个 cycle** 的 RUL。

```text
cycle 1..30  → 预测 cycle 30 的 RUL
cycle 2..31  → 预测 cycle 31 的 RUL
...
```

## 为什么可能比 XGBoost 好

XGBoost 主要看「当前帧 + 简单 rolling」；LSTM 能学习一段时间内的**退化趋势形状**。

## 防泄漏要点

1. Scaler 只在训练集 fit  
2. 验证集按 **unit** 划分，不要按行随机切  
3. 窗口内不能偷看未来 cycle  

## 怎么复现

```powershell
python scripts\run_lstm_fd001.py
```

## 本实验结论

LSTM test RMSE (capped125) ≈ **14.27**，优于 G2 XGBoost ≈ **17.48**。  
详见 `experiments/exp_20260722_lstm_fd001/notes.md`。
