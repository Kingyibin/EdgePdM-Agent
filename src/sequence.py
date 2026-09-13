"""Sliding-window sequence builders for RUL models."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_windows(
    df: pd.DataFrame,
    feature_cols: list[str],
    window: int,
    label_col: str | None = "RUL",
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray]:
    """Return X (n, window, f), y (n,) or None, unit_ids (n,).

    For each unit, only emit windows that end at cycle positions with full history.
    """
    xs: list[np.ndarray] = []
    ys: list[float] = []
    units: list[int] = []

    for unit, g in df.groupby("unit"):
        g = g.sort_values("cycle")
        feats = g[feature_cols].to_numpy(dtype=np.float32)
        labels = g[label_col].to_numpy(dtype=np.float32) if label_col and label_col in g.columns else None
        if len(g) < window:
            continue
        for end in range(window, len(g) + 1):
            xs.append(feats[end - window : end])
            units.append(int(unit))
            if labels is not None:
                ys.append(float(labels[end - 1]))

    x = np.stack(xs, axis=0)
    y = np.asarray(ys, dtype=np.float32) if labels is not None else None
    u = np.asarray(units, dtype=np.int32)
    return x, y, u


def last_window_per_unit(
    df: pd.DataFrame,
    feature_cols: list[str],
    window: int,
) -> tuple[np.ndarray, np.ndarray]:
    """One window ending at each unit's last cycle (pad at front if needed)."""
    xs: list[np.ndarray] = []
    units: list[int] = []
    for unit, g in df.groupby("unit"):
        g = g.sort_values("cycle")
        feats = g[feature_cols].to_numpy(dtype=np.float32)
        if len(feats) >= window:
            w = feats[-window:]
        else:
            pad = np.repeat(feats[:1], window - len(feats), axis=0)
            w = np.concatenate([pad, feats], axis=0)
        xs.append(w)
        units.append(int(unit))
    return np.stack(xs, axis=0), np.asarray(units, dtype=np.int32)
