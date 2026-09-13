"""Export trained LSTM to ONNX + scaler sidecar + sample window for C++."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import add_rul_labels, load_subset, project_root  # noqa: E402
from src.features import FEATURE_BASE, drop_constant_features  # noqa: E402
from src.lstm_model import RULSTM  # noqa: E402
from src.sequence import last_window_per_unit  # noqa: E402


def main() -> None:
    with open(project_root() / "configs" / "default.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    ckpt_path = project_root() / "experiments" / "exp_20260722_lstm_fd001" / "lstm.pt"
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    feature_cols = ckpt["feature_cols"]
    window = int(ckpt["window"])
    mean = np.asarray(ckpt["scaler_mean"], dtype=np.float32)
    scale = np.asarray(ckpt["scaler_scale"], dtype=np.float32)

    model = RULSTM(n_features=len(feature_cols), hidden=64, num_layers=2, dropout=0.2)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    # Rebuild one scaled test window (unit 1) for C++ smoke test
    raw_dir = project_root() / cfg["data"]["raw_dir"]
    _, test_df, test_rul = load_subset(raw_dir, cfg["data"]["subset"])
    x_test, units = last_window_per_unit(test_df, feature_cols, window)
    # unit 1 is first after sort in training script; ensure unit==1
    idx = int(np.where(units == 1)[0][0])
    w = x_test[idx]
    w_scaled = (w - mean) / np.where(scale == 0, 1.0, scale)
    w_scaled = w_scaled.astype(np.float32)

    out_dir = project_root() / "models" / "onnx"
    out_dir.mkdir(parents=True, exist_ok=True)

    dummy = torch.from_numpy(w_scaled).unsqueeze(0)  # (1, T, F)
    onnx_path = out_dir / "rul_lstm.onnx"
    torch.onnx.export(
        model,
        dummy,
        onnx_path,
        input_names=["input"],
        output_names=["rul"],
        dynamic_axes={"input": {0: "batch"}, "rul": {0: "batch"}},
        opset_version=17,
        dynamo=False,  # legacy exporter; avoids Win console unicode issues in dynamo path
    )

    sidecar = {
        "model": "rul_lstm",
        "onnx": str(onnx_path.relative_to(project_root())).replace("\\", "/"),
        "window": window,
        "feature_cols": feature_cols,
        "scaler_mean": mean.tolist(),
        "scaler_scale": scale.tolist(),
        "sample_unit": 1,
        "sample_true_rul": float(test_rul.iloc[0]),
    }
    with open(out_dir / "rul_lstm_sidecar.json", "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2)

    # CSV: 30 lines, 17 floats — already scaled
    np.savetxt(out_dir / "sample_window_unit1_scaled.csv", w_scaled, delimiter=",", fmt="%.8f")

    with torch.no_grad():
        py_pred = float(model(dummy).item())
    print(json.dumps({"onnx": str(onnx_path), "python_pred_unit1": py_pred, "true_rul_unit1": float(test_rul.iloc[0])}, indent=2))


if __name__ == "__main__":
    main()
