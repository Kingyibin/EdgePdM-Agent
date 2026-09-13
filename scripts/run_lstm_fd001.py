"""Train LSTM on FD001 windows and compare with G2 XGBoost baseline metrics.

Usage:
  .\\.venv\\Scripts\\python.exe scripts\\run_lstm_fd001.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import add_rul_labels, load_subset, project_root  # noqa: E402
from src.features import FEATURE_BASE, drop_constant_features  # noqa: E402
from src.lstm_model import RULSTM  # noqa: E402
from src.metrics import mae, nasa_score, rmse  # noqa: E402
from src.sequence import build_windows, last_window_per_unit  # noqa: E402


def load_config() -> dict:
    with open(project_root() / "configs" / "default.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def scale_train_test(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    # train: (N, T, F) — fit scaler on flattened train timesteps
    n, t, f = train.shape
    scaler = StandardScaler()
    scaler.fit(train.reshape(-1, f))
    train_s = scaler.transform(train.reshape(-1, f)).reshape(n, t, f).astype(np.float32)
    nt = test.shape[0]
    test_s = scaler.transform(test.reshape(-1, f)).reshape(nt, t, f).astype(np.float32)
    return train_s, test_s, scaler


def main() -> None:
    cfg = load_config()
    seed = int(cfg.get("project", {}).get("seed", 42))
    window = int(cfg.get("features", {}).get("window_size", 30))
    rul_cap = int(cfg["data"].get("rul_cap", 125))
    subset = cfg["data"]["subset"]
    raw_dir = project_root() / cfg["data"]["raw_dir"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")

    train_df, test_df, test_rul = load_subset(raw_dir, subset)
    train_df = add_rul_labels(train_df, rul_cap=rul_cap)
    keep = drop_constant_features(train_df, FEATURE_BASE)

    x_all, y_all, units = build_windows(train_df, keep, window=window, label_col="RUL")
    # hold out 20% units for validation
    uniq = np.unique(units)
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_val_units = max(1, int(0.2 * len(uniq)))
    val_units = set(uniq[:n_val_units].tolist())
    tr_mask = np.array([u not in val_units for u in units])
    va_mask = ~tr_mask

    x_test, test_units = last_window_per_unit(test_df, keep, window=window)
    # align test order to unit 1..100
    order = np.argsort(test_units)
    x_test = x_test[order]
    y_true = test_rul.to_numpy(dtype=np.float64)
    y_true_capped = np.minimum(y_true, rul_cap)

    x_tr, x_te, scaler = scale_train_test(x_all[tr_mask], x_test)
    x_va = scaler.transform(x_all[va_mask].reshape(-1, x_all.shape[-1])).reshape(-1, window, len(keep)).astype(
        np.float32
    )
    y_tr, y_va = y_all[tr_mask], y_all[va_mask]

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(x_tr), torch.from_numpy(y_tr)),
        batch_size=256,
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.from_numpy(x_va), torch.from_numpy(y_va)),
        batch_size=256,
        shuffle=False,
    )

    model = RULSTM(n_features=len(keep), hidden=64, num_layers=2, dropout=0.2).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    best_state = None
    history = []
    epochs = 25
    for epoch in range(1, epochs + 1):
        model.train()
        tr_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
            tr_losses.append(float(loss.item()))
        model.eval()
        va_preds, va_tgts = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                pred = model(xb.to(device)).cpu().numpy()
                va_preds.append(pred)
                va_tgts.append(yb.numpy())
        va_pred = np.concatenate(va_preds)
        va_tgt = np.concatenate(va_tgts)
        va_rmse = rmse(va_tgt, va_pred)
        history.append({"epoch": epoch, "train_mse": float(np.mean(tr_losses)), "val_rmse": va_rmse})
        if va_rmse < best_val:
            best_val = va_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch:02d} train_mse={np.mean(tr_losses):.3f} val_rmse={va_rmse:.3f}")

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        y_pred = model(torch.from_numpy(x_te).to(device)).cpu().numpy()

    metrics = {
        "model": "lstm",
        "window": window,
        "n_features": len(keep),
        "epochs": epochs,
        "best_val_rmse": best_val,
        "n_test_units": int(len(y_true)),
        "rmse_raw_rul": rmse(y_true, y_pred),
        "rmse_capped125": rmse(y_true_capped, y_pred),
        "mae_capped125": mae(y_true_capped, y_pred),
        "nasa_score_capped125": nasa_score(y_true_capped, y_pred),
        "baseline_xgboost_rmse_capped125": 17.484151162176904,
        "baseline_xgboost_nasa_score_capped125": 929.3452913157207,
    }
    metrics["beat_xgboost_rmse"] = bool(metrics["rmse_capped125"] < metrics["baseline_xgboost_rmse_capped125"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_dir = project_root() / "experiments" / f"exp_{stamp}_lstm_fd001"
    out_dir.mkdir(parents=True, exist_ok=True)

    torch.save({"state_dict": best_state, "feature_cols": keep, "window": window, "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist()}, out_dir / "lstm.pt")
    with open(out_dir / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({"created_utc": datetime.now(timezone.utc).isoformat(), "metrics": metrics}, f, indent=2)

    import pandas as pd

    pd.DataFrame({"unit": np.arange(1, len(y_true) + 1), "y_true": y_true, "y_true_capped125": y_true_capped, "y_pred": y_pred}).to_csv(
        out_dir / "predictions_lstm.csv", index=False
    )

    plt.figure(figsize=(6, 6))
    plt.scatter(y_true_capped, y_pred, alpha=0.7)
    lim = [0, max(y_true_capped.max(), y_pred.max()) * 1.05]
    plt.plot(lim, lim, "r--")
    plt.xlabel("True RUL (capped)")
    plt.ylabel("Predicted RUL")
    plt.title("LSTM pred vs true")
    plt.tight_layout()
    plt.savefig(out_dir / "scatter_lstm.png", dpi=150)
    plt.close()

    print(json.dumps(metrics, indent=2))
    print(f"Wrote {out_dir}")


if __name__ == "__main__":
    main()
