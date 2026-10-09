#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EdgePdM-Agent 实时训练控制台服务端。

真实训练 C-MAPSS FD001 的 LSTM RUL 模型（复用 src/ 现有模块），
通过 SSE 把每个 epoch / batch 的真实指标推送给网页，网页端实时画曲线、高亮正在执行的代码。

用法：
    .venv/Scripts/python.exe training_console_server.py
然后浏览器打开 http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import sys
import time
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------------
# 配置
# ----------------------------------------------------------------------------
PORT = 8765
EPOCHS = 25  # 与项目原脚本一致；想快速演示可调到 10
HIDDEN = 64
NUM_LAYERS = 2
BATCH_SIZE = 256
LR = 1e-3

# ----------------------------------------------------------------------------
# 训练状态 + 事件总线（SSE 用）
# ----------------------------------------------------------------------------
state = {
    "status": "idle",        # idle | running | done | error
    "epoch": 0,
    "epochs": EPOCHS,
    "phase": "idle",
    "train_mse": None,
    "val_rmse": None,
    "elapsed": 0.0,
    "eta": None,
    "throughput": None,      # windows / s
    "final": None,
    "error": None,
    "sys": {"cpu": None, "mem": None, "disk": None, "proc_cpu": None, "rss_mb": None},
}
EVENTS: list[dict] = []      # {"id":int, "type":str, "data":dict}
_lock = threading.Lock()
_event_id = 0
_train_thread: threading.Thread | None = None
_train_running = False
_t0 = 0.0
_epoch_times: list[float] = []


def push_event(etype: str, data: dict) -> None:
    global _event_id
    with _lock:
        _event_id += 1
        ev = {"id": _event_id, "type": etype, "data": data}
        EVENTS.append(ev)


def log(msg: str, level: str = "info") -> None:
    push_event("log", {"t": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})


# ----------------------------------------------------------------------------
# 真实系统指标采样（优先 psutil，缺失则降级）
# ----------------------------------------------------------------------------
try:
    import psutil
    _HAVE_PS = True
except Exception:
    _HAVE_PS = False


def sample_sys() -> None:
    if not _HAVE_PS:
        return
    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    proc = psutil.Process()
    try:
        proc_cpu = proc.cpu_percent(interval=None)
    except Exception:
        proc_cpu = None
    rss = proc.memory_info().rss / (1024 * 1024)
    disk = psutil.disk_usage(str(ROOT)).percent
    state["sys"] = {
        "cpu": round(cpu, 1),
        "mem": round(vm.percent, 1),
        "disk": round(disk, 1),
        "proc_cpu": round(proc_cpu, 1) if proc_cpu is not None else None,
        "rss_mb": round(rss, 1),
    }


# ----------------------------------------------------------------------------
# 真实训练（复用 src/）
# ----------------------------------------------------------------------------
def run_training() -> None:
    global _train_running, _t0, _epoch_times, _train_thread
    try:
        import numpy as np
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
        from sklearn.preprocessing import StandardScaler

        from src.data import add_rul_labels, load_subset, project_root
        from src.features import FEATURE_BASE, drop_constant_features
        from src.lstm_model import RULSTM, mc_dropout_predict
        from src.metrics import mae, nasa_score, rmse
        from src.sequence import build_windows, last_window_per_unit

        cfg = {"data": {"rul_cap": 125, "subset": "FD001", "raw_dir": "data/raw"}, "features": {"window_size": 30}}
        seed = 42
        window = 30
        rul_cap = 125
        raw_dir = project_root() / cfg["data"]["raw_dir"]

        state["status"] = "running"
        state["epoch"] = 0
        state["phase"] = "loading_data"
        state["final"] = None
        log("加载 C-MAPSS FD001 数据 ...", "info")
        push_event("phase", {"phase": "loading_data"})
        t0 = time.time()
        train_df, test_df, test_rul = load_subset(raw_dir, "FD001")
        train_df = add_rul_labels(train_df, rul_cap=rul_cap)
        keep = drop_constant_features(train_df, FEATURE_BASE)
        log(f"数据加载完成：{len(keep)} 个特征，训练样本构建中 ...", "info")

        state["phase"] = "building_windows"
        push_event("phase", {"phase": "building_windows"})
        x_all, y_all, units = build_windows(train_df, keep, window=window, label_col="RUL")
        rng = np.random.default_rng(seed)
        uniq = np.unique(units)
        rng.shuffle(uniq)
        n_val = max(1, int(0.2 * len(uniq)))
        val_units = set(uniq[:n_val].tolist())
        tr_mask = np.array([u not in val_units for u in units])
        va_mask = ~tr_mask
        x_test, test_units = last_window_per_unit(test_df, keep, window=window)
        order = np.argsort(test_units)
        x_test = x_test[order]
        y_true = test_rul.to_numpy(dtype=np.float64)
        y_true_capped = np.minimum(y_true, rul_cap)
        log(f"窗口构建完成：训练窗口 {int(tr_mask.sum())} / 验证 {int(va_mask.sum())} / 测试 {len(y_true)} 单元", "info")

        # 标准化
        n, t, f = x_all.shape
        scaler = StandardScaler()
        scaler.fit(x_all.reshape(-1, f))
        x_tr = scaler.transform(x_all[tr_mask].reshape(-1, f)).reshape(-1, t, f).astype(np.float32)
        x_va = scaler.transform(x_all[va_mask].reshape(-1, f)).reshape(-1, t, f).astype(np.float32)
        x_te = scaler.transform(x_test.reshape(-1, f)).reshape(-1, t, f).astype(np.float32)
        y_tr, y_va = y_all[tr_mask], y_all[va_mask]

        train_loader = DataLoader(TensorDataset(torch.from_numpy(x_tr), torch.from_numpy(y_tr)),
                                  batch_size=BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(TensorDataset(torch.from_numpy(x_va), torch.from_numpy(y_va)),
                                batch_size=BATCH_SIZE, shuffle=False)
        device = torch.device("cpu")
        model = RULSTM(n_features=len(keep), hidden=HIDDEN, num_layers=NUM_LAYERS, dropout=0.2).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=LR)
        loss_fn = nn.MSELoss()

        best_val = float("inf")
        best_state = None
        _t0 = time.time()
        _epoch_times = []
        total_windows = int(tr_mask.sum())
        log(f"开始训练：{EPOCHS} epochs, batch={BATCH_SIZE}, hidden={HIDDEN}, layers={NUM_LAYERS}", "info")
        state["phase"] = "train"

        for epoch in range(1, EPOCHS + 1):
            ep_start = time.time()
            state["epoch"] = epoch
            state["phase"] = "train"
            push_event("phase", {"phase": "train", "epoch": epoch})
            model.train()
            tr_losses = []
            nb = 0
            for xb, yb in train_loader:
                xb, yb = xb.to(device), yb.to(device)
                opt.zero_grad()
                pred = model(xb)
                loss = loss_fn(pred, yb)
                loss.backward()
                opt.step()
                tr_losses.append(float(loss.item()))
                nb += 1
                if nb % 10 == 0:
                    push_event("live_loss", {"epoch": epoch, "step": nb,
                                             "loss": float(loss.item()),
                                             "elapsed": round(time.time() - _t0, 1)})
                    log(f"[train] epoch {epoch:02d} step {nb:03d} loss={loss.item():.4f}", "debug")
            model.eval()
            va_preds, va_tgts = [], []
            with torch.no_grad():
                for xb, yb in val_loader:
                    p = model(xb.to(device)).cpu().numpy()
                    va_preds.append(p)
                    va_tgts.append(yb.numpy())
            va_pred = np.concatenate(va_preds)
            va_tgt = np.concatenate(va_tgts)
            va_rmse = rmse(va_tgt, va_pred)
            tmse = float(np.mean(tr_losses))
            if va_rmse < best_val:
                best_val = va_rmse
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            ep_t = time.time() - ep_start
            _epoch_times.append(ep_t)
            elapsed = time.time() - _t0
            avg_ep = sum(_epoch_times) / len(_epoch_times)
            eta = avg_ep * (EPOCHS - epoch)
            throughput = total_windows * epoch / elapsed if elapsed > 0 else 0.0
            state.update({"train_mse": tmse, "val_rmse": va_rmse, "elapsed": elapsed,
                          "eta": eta, "throughput": throughput})
            push_event("metric", {"epoch": epoch, "train_mse": tmse, "val_rmse": va_rmse,
                                  "elapsed": round(elapsed, 1), "eta": round(eta, 1),
                                  "throughput": round(throughput, 1),
                                  "best_val_rmse": best_val})
            log(f"epoch {epoch:02d}/{EPOCHS}  train_mse={tmse:.4f}  val_rmse={va_rmse:.4f}  "
                f"({ep_t:.1f}s)  ETA {eta:.0f}s", "info")

        # 评估测试集
        state["phase"] = "eval"
        push_event("phase", {"phase": "eval"})
        log("训练完成，在测试集上评估最终指标 ...", "info")
        model.load_state_dict(best_state)
        model.eval()
        with torch.no_grad():
            y_pred = model(torch.from_numpy(x_te).to(device)).cpu().numpy()
        rmse_raw = rmse(y_true, y_pred)
        rmse_cap = rmse(y_true_capped, y_pred)
        mae_cap = mae(y_true_capped, y_pred)
        nasa_cap = nasa_score(y_true_capped, y_pred)
        # ---- MC Dropout 不确定性估计（项目新增能力）----
        log("MC Dropout 采样中（30 次随机前向）...", "info")
        push_event("phase", {"phase": "eval", "detail": "mc_dropout"})
        mean_pred, std_pred = mc_dropout_predict(model, torch.from_numpy(x_te), n_samples=30, device=device)
        lo = mean_pred - 1.96 * std_pred
        hi = mean_pred + 1.96 * std_pred
        coverage = float(np.mean((y_true_capped >= lo) & (y_true_capped <= hi)))
        mean_std = float(std_pred.mean())
        rmse_mean = rmse(y_true_capped, mean_pred)
        push_event("preds", {
            "y_true": [round(float(v), 2) for v in y_true_capped],
            "mean": [round(float(v), 2) for v in mean_pred],
            "std": [round(float(v), 2) for v in std_pred],
        })
        push_event("unc", {"rmse_mean": rmse_mean, "coverage95": coverage, "mean_std": mean_std})
        log(f"不确定性：RMSE(MC均值)={rmse_mean:.3f}  名义95%区间覆盖率={coverage*100:.1f}%  平均σ={mean_std:.2f}（未校准，不能当停机阈值）", "success")
        xgb_rmse = 17.484151162176904
        final = {
            "rmse_raw_rul": rmse_raw,
            "rmse_capped125": rmse_cap,
            "mae_capped125": mae_cap,
            "nasa_score_capped125": nasa_cap,
            "baseline_xgboost_rmse_capped125": xgb_rmse,
            "beat_xgboost_rmse": bool(rmse_cap < xgb_rmse),
            "best_val_rmse": best_val,
            "rmse_mean_mcdropout": rmse_mean,
            "coverage95_mcdropout": coverage,
            "mean_std_mcdropout": mean_std,
            "elapsed_total": round(time.time() - _t0, 1),
        }
        state["final"] = final
        state["status"] = "done"
        state["phase"] = "done"
        push_event("done", final)
        log(f"完成 → RMSE(capped125)={rmse_cap:.3f}  MAE={mae_cap:.3f}  "
            f"NASA={nasa_cap:.1f}  击败XGBoost基线={final['beat_xgboost_rmse']}", "success")
    except Exception as e:  # noqa
        state["status"] = "error"
        state["error"] = str(e)
        push_event("error", {"msg": str(e)})
        log(f"训练异常：{e}", "error")
    finally:
        _train_running = False
        _train_thread = None


def start_training() -> None:
    global _train_running, _train_thread
    if _train_running:
        return
    # 重置状态
    with _lock:
        state["status"] = "idle"
        state["final"] = None
        state["error"] = None
        state["epoch"] = 0
        state["train_mse"] = None
        state["val_rmse"] = None
    _train_running = True
    _train_thread = threading.Thread(target=run_training, daemon=True)
    _train_thread.start()


# ----------------------------------------------------------------------------
# HTTP 处理
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            html = (ROOT / "training_console.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
        elif path == "/stream":
            self._stream()
        elif path == "/state":
            with _lock:
                body = json.dumps(state).encode("utf-8")
            self._send(200, body)
        elif path == "/experiments":
            self._experiments()
        elif path == "/file":
            self._file(parsed)
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/start":
            start_training()
            self._send(200, json.dumps({"ok": True, "status": "starting"}).encode("utf-8"))
        else:
            self._send(404, b"not found")

    def _file(self, parsed):
        qs = parse_qs(parsed.query)
        name = qs.get("name", [""])[0]
        target = (ROOT / name).resolve()
        if not str(target).startswith(str(ROOT.resolve())):
            self._send(403, b"forbidden")
            return
        if not target.exists() or not target.is_file():
            self._send(404, b"no such file")
            return
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self._send(500, str(e).encode("utf-8"))
            return
        self._send(200, json.dumps({"name": name, "text": text}).encode("utf-8"))

    def _experiments(self):
        exp_dir = ROOT / "experiments"
        rows = []
        if exp_dir.exists():
            for d in sorted(exp_dir.iterdir()):
                if d.is_dir():
                    rec = {"name": d.name}
                    mj = d / "metrics.json"
                    if mj.exists():
                        try:
                            rec["metrics"] = json.loads(mj.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                    rows.append(rec)
        self._send(200, json.dumps(rows).encode("utf-8"))

    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self._stream_loop()
        except Exception:
            # 客户端断开（BrokenPipe / ConnectionReset）属正常，静默退出
            return

    def _stream_loop(self):
        last_id = 0
        hdr = self.headers.get("Last-Event-ID")
        if hdr and hdr.isdigit():
            last_id = int(hdr)
        # 补发错过的事件
        with _lock:
            missed = [ev for ev in EVENTS if ev["id"] > last_id]
        for ev in missed:
            try:
                self.wfile.write(f"id: {ev['id']}\n".encode("utf-8"))
                self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
            except Exception:
                return
            last_id = ev["id"]
        while True:
            with _lock:
                new = [ev for ev in EVENTS if ev["id"] > last_id]
            sample_sys()
            for ev in new:
                try:
                    self.wfile.write(f"id: {ev['id']}\n".encode("utf-8"))
                    self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    return
                last_id = ev["id"]
            # 周期广播系统指标
            try:
                blob = {"id": _event_id, "type": "sys", "data": state["sys"]}
                self.wfile.write(f"id: {_event_id + 1}\n".encode("utf-8"))
                self.wfile.write(f"data: {json.dumps(blob, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
            except Exception:
                return
            time.sleep(1.0)

    def log_message(self, *args):  # noqa
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"EdgePdM-Agent 训练控制台已启动： http://127.0.0.1:{PORT}")
    print("正在自动开始训练 ... (Ctrl+C 退出)")
    start_training()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
