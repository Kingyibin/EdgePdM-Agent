# G2 Baseline 学习笔记（给初学者）

> 配合代码：`scripts/run_baseline_fd001.py`、`src/data.py`、`src/features.py`、`src/metrics.py`  
> 实验结果：`experiments/exp_20260722_baseline_xgb_ridge/`

---

## 1. 这一关要达成什么

不是「把 XGBoost 调到论文 SOTA」，而是：

1. 自己跑通一条**可复现**的 RUL 预测链路；
2. 得到真实数字（RMSE / NASA Score）；
3. 能向别人讲清每一步为什么这样做。

---

## 2. Pipeline 步骤图

```text
train_FD001.txt
  → 读入 DataFrame
  → 每台发动机算 RUL = max_cycle - cycle
  → RUL = min(RUL, 125)          # capped
  → 丢掉几乎不变的传感器
  → 对每个 unit 做 rolling mean   # 只用过去+当前
  → StandardScaler.fit(train)
  → 训练 Ridge / XGBoost
test_FD001.txt
  → 同样 rolling（不重新 fit scaler）
  → 每台取最后一帧特征
  → predict
  → 与 RUL_FD001.txt 比 RMSE/Score
```

---

## 3. 为什么测试用「最后一帧」

官方测试任务是：给定一段截断轨迹，预测**该轨迹结束时刻**还能跑多久。  
取最后一帧（或最后窗口）是最直观的表格模型做法。G3 的 LSTM 会改用序列窗口。

---

## 4. 为什么用 GroupKFold（按 unit）

如果随机按行划分 train/val，同一台发动机的相邻 cycle 可能一边训练一边验证 → **泄漏**，分数虚高。  
按 `unit` 分组交叉验证更诚实。

---

## 5. 指标怎么读

- **RMSE**：平均平方误差的根，越小越好。本实验 XGBoost ≈ 17.5（capped125）。
- **NASA Score**：预测偏晚惩罚更大（维护上更危险）。越小越好。
- 报告时写明是否对 true RUL 做了 125 cap，避免和别人论文口径对不上。

---

## 6. 如何复现

```powershell
cd E:\EdgePdM-Agent
.\.venv\Scripts\Activate.ps1
python scripts\run_baseline_fd001.py
```

依赖见 `requirements.txt`。

---

## 7. 和 eastani 仓库的关系

我读了公开 PdM/C-MAPSS 工程的「数据→特征→评估→产物」组织方式，但本仓库代码是自写的，便于：

- 控制路径与配置（`configs/default.yaml`）；
- 后续接 ONNX / C++；
- 面试时能讲每一行逻辑。

---

## 8. 下一关预告（G3）

用 sliding window + LSTM/GRU 之一，和本 baseline 的 RMSE 对比。  
若深度模型更差，也要写清楚「为什么」，这是正常科研/工程过程。
