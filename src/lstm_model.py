"""Small LSTM regressor for RUL."""

from __future__ import annotations

import numpy as np
import torch
from torch import nn


class RULSTM(nn.Module):
    def __init__(self, n_features: int, hidden: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F)
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(last).squeeze(-1)


@torch.no_grad()
def mc_dropout_predict(model: nn.Module, x: torch.Tensor, n_samples: int = 30, device=None):
    """MC Dropout 不确定性估计：保持 dropout 激活，多次随机前向取均值与标准差。

    返回 (mean, std)，shape 均为 (N,)。这是项目此前缺失的能力：
    原模型只输出 RUL 点估计，本函数为每个测试单元给出均值与 95% 置信区间，
    为"何时安排维护"提供量化风险依据。
    """
    model.train()  # 关键：保持 dropout 开启，使前向具有随机性
    if device is not None:
        x = x.to(device)
    samples = []
    for _ in range(n_samples):
        p = model(x)
        samples.append(p.detach().cpu().numpy() if device is not None else p.numpy())
    model.eval()
    arr = np.stack(samples, axis=0).reshape(n_samples, -1)
    return arr.mean(axis=0), arr.std(axis=0)
