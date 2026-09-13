"""C-MAPSS data loading and RUL label construction.

给初学者：先读 notes/learning_cmapss.md，再读本文件。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

COLUMN_NAMES = (
    ["unit", "cycle", "setting_1", "setting_2", "setting_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_fd_file(path: Path) -> pd.DataFrame:
    """Load a space-separated C-MAPSS txt into a named DataFrame (26 cols)."""
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df = df.iloc[:, :26].copy()
    df.columns = COLUMN_NAMES
    return df


def load_subset(raw_dir: Path | str, subset: str = "FD001") -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    raw_dir = Path(raw_dir)
    train = load_fd_file(raw_dir / f"train_{subset}.txt")
    test = load_fd_file(raw_dir / f"test_{subset}.txt")
    rul = pd.read_csv(raw_dir / f"RUL_{subset}.txt", sep=r"\s+", header=None, names=["RUL"])["RUL"]
    return train, test, rul


def add_rul_labels(train: pd.DataFrame, rul_cap: int | None = 125) -> pd.DataFrame:
    """For each unit: RUL = max_cycle - cycle, optionally capped."""
    out = train.copy()
    max_cycle = out.groupby("unit")["cycle"].transform("max")
    out["RUL"] = max_cycle - out["cycle"]
    if rul_cap is not None:
        out["RUL"] = out["RUL"].clip(upper=rul_cap)
    return out


def last_cycle_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the last observed cycle per unit (typical test evaluation rows)."""
    idx = df.groupby("unit")["cycle"].idxmax()
    return df.loc[idx].sort_values("unit").reset_index(drop=True)
