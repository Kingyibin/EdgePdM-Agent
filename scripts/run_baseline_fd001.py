"""Run FD001 tabular baselines (Ridge + XGBoost) and write experiment artifacts.

Usage (from project root):
  .\\.venv\\Scripts\\python.exe scripts\\run_baseline_fd001.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import add_rul_labels, last_cycle_rows, load_subset, project_root  # noqa: E402
from src.features import (  # noqa: E402
    FEATURE_BASE,
    add_rolling_means,
    build_feature_matrix,
    drop_constant_features,
)
from src.metrics import mae, nasa_score, rmse  # noqa: E402


def load_config() -> dict:
    with open(project_root() / "configs" / "default.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def prepare_frames(cfg: dict):
    raw_dir = project_root() / cfg["data"]["raw_dir"]
    subset = cfg["data"]["subset"]
    rul_cap = cfg["data"].get("rul_cap", 125)
    window = int(cfg.get("features", {}).get("window_size", 5))
    # rolling window for baseline features; keep small for speed
    roll_w = min(window, 5) if window else 5

    train, test, test_rul = load_subset(raw_dir, subset)
    train = add_rul_labels(train, rul_cap=rul_cap)

    keep = drop_constant_features(train, FEATURE_BASE)
    train = add_rolling_means(train, keep, window=roll_w)
    test = add_rolling_means(test, keep, window=roll_w)
    roll_cols = [f"{c}_roll{roll_w}" for c in keep]
    feature_cols = keep + roll_cols

    return train, test, test_rul, feature_cols, keep, roll_w


def cv_rmse_xgb(train, feature_cols, seed: int = 42) -> float:
    """GroupKFold by unit to avoid leaking the same engine across folds."""
    x, scaler = build_feature_matrix(train, feature_cols, fit=True)
    y = train["RUL"].to_numpy()
    groups = train["unit"].to_numpy()
    gkf = GroupKFold(n_splits=5)
    scores = []
    for tr_idx, va_idx in gkf.split(x, y, groups):
        model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=4,
        )
        model.fit(x[tr_idx], y[tr_idx])
        pred = model.predict(x[va_idx])
        scores.append(rmse(y[va_idx], pred))
    return float(np.mean(scores))


def train_and_eval(name: str, model, train, test, test_rul, feature_cols, out_dir: Path, seed: int):
    x_train, scaler = build_feature_matrix(train, feature_cols, fit=True)
    y_train = train["RUL"].to_numpy()
    model.fit(x_train, y_train)

    test_last = last_cycle_rows(test)
    x_test, _ = build_feature_matrix(test_last, feature_cols, scaler=scaler, fit=False)
    y_true = test_rul.to_numpy(dtype=np.float64)
    # Cap true RUL for metric consistency with training labels
    y_true_capped = np.minimum(y_true, 125)
    y_pred = model.predict(x_test)

    metrics = {
        "model": name,
        "n_test_units": int(len(y_true)),
        "rmse_raw_rul": rmse(y_true, y_pred),
        "rmse_capped125": rmse(y_true_capped, y_pred),
        "mae_capped125": mae(y_true_capped, y_pred),
        "nasa_score_capped125": nasa_score(y_true_capped, y_pred),
        "nasa_score_raw": nasa_score(y_true, y_pred),
    }

    joblib.dump({"model": model, "scaler": scaler, "feature_cols": feature_cols}, out_dir / f"{name}.joblib")
    pred_df = test_last[["unit", "cycle"]].copy()
    pred_df["y_true"] = y_true
    pred_df["y_true_capped125"] = y_true_capped
    pred_df["y_pred"] = y_pred
    pred_df.to_csv(out_dir / f"predictions_{name}.csv", index=False)

    plt.figure(figsize=(6, 6))
    plt.scatter(y_true_capped, y_pred, alpha=0.7, edgecolors="none")
    lim = [0, max(y_true_capped.max(), y_pred.max()) * 1.05]
    plt.plot(lim, lim, "r--", label="ideal")
    plt.xlabel("True RUL (capped 125)")
    plt.ylabel("Predicted RUL")
    plt.title(f"{name}: pred vs true")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"scatter_{name}.png", dpi=150)
    plt.close()

    return metrics


def main() -> None:
    cfg = load_config()
    seed = int(cfg.get("project", {}).get("seed", 42))
    train, test, test_rul, feature_cols, keep, roll_w = prepare_frames(cfg)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_dir = project_root() / "experiments" / f"exp_{stamp}_baseline_xgb_ridge"
    out_dir.mkdir(parents=True, exist_ok=True)

    cv = cv_rmse_xgb(train, feature_cols, seed=seed)

    ridge = Ridge(alpha=1.0)
    xgb = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=seed,
        n_jobs=4,
    )

    metrics_ridge = train_and_eval("ridge", ridge, train, test, test_rul, feature_cols, out_dir, seed)
    metrics_xgb = train_and_eval("xgboost", xgb, train, test, test_rul, feature_cols, out_dir, seed)

    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "subset": cfg["data"]["subset"],
        "rul_cap": cfg["data"].get("rul_cap", 125),
        "n_base_features_kept": len(keep),
        "rolling_window": roll_w,
        "n_features_total": len(feature_cols),
        "groupkfold_xgb_rmse_mean": cv,
        "test_metrics": {"ridge": metrics_ridge, "xgboost": metrics_xgb},
        "notes": [
            "Train labels use capped RUL (125).",
            "Primary reported metric: rmse_capped125 on last cycle of each test unit.",
            "Also report nasa_score_capped125 (asymmetric).",
            "Reference idea: tabular PdM baseline similar in spirit to eastani/cmapss pipelines; code rewritten in-repo.",
        ],
    }
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary["test_metrics"], indent=2))
    print(f"Wrote experiment to {out_dir}")


if __name__ == "__main__":
    main()
