"""Feature selection and scaling for tabular baseline.

Baseline 思路（故意简单、可讲清）：
- 输入：当前 cycle 的 setting + sensor（去掉几乎恒定的传感器）
- 可选：同 unit 上的 rolling mean（仅用过去，含当前）
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


FEATURE_BASE = [f"setting_{i}" for i in range(1, 4)] + [f"sensor_{i}" for i in range(1, 22)]


def drop_constant_features(df: pd.DataFrame, cols: list[str], eps: float = 1e-6) -> list[str]:
    keep = []
    for c in cols:
        if df[c].std(ddof=0) > eps:
            keep.append(c)
    return keep


def add_rolling_means(df: pd.DataFrame, cols: list[str], window: int = 5) -> pd.DataFrame:
    """Per-unit rolling mean; min_periods=1 so early cycles仍有值。"""
    out = df.copy()
    for c in cols:
        out[f"{c}_roll{window}"] = (
            out.groupby("unit", group_keys=False)[c]
            .apply(lambda s: s.rolling(window=window, min_periods=1).mean())
            .reset_index(level=0, drop=True)
        )
    return out


def build_feature_matrix(
    df: pd.DataFrame,
    feature_cols: list[str],
    scaler: StandardScaler | None = None,
    fit: bool = False,
) -> tuple[np.ndarray, StandardScaler]:
    x = df[feature_cols].to_numpy(dtype=np.float64)
    if scaler is None:
        scaler = StandardScaler()
    if fit:
        x = scaler.fit_transform(x)
    else:
        x = scaler.transform(x)
    return x, scaler
