#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EdgePdM-Agent 训练马拉松服务端（摸鱼长跑版）。

不再只跑一个实验就停，而是连续跑一串真实实验（超参扫描），
跑完一轮换随机种子自动进入下一轮，无限循环，撑满整个下午。
每个实验都是真实训练 NASA C-MAPSS FD001 的 LSTM RUL 模型，
指标通过 SSE 实时推给网页，并写进 experiments/<name>/metrics.json。

用法：
    .venv/Scripts/python.exe training_marathon.py
然后浏览器打开 http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import sys
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------------
# 配置
# ----------------------------------------------------------------------------
PORT = 8765
EPOCHS_M = 18          # 每个实验的 epoch 数（约 1.5~2 分钟）
BATCH_SIZE = 256
RUL_CAP = 125

# 超参扫描： (tag, window, hidden, num_layers, lr)
SWEEP = [
    ("w30_h64",     30, 64, 2, 1e-3),
    ("w20_h64",     20, 64, 2, 1e-3),
    ("w40_h64",     40, 64, 2, 1e-3),
    ("w30_h48",     30, 48, 2, 1e-3),
    ("w30_h96",     30, 96, 2, 1e-3),
    ("w30_h64_lr5e4", 30, 64, 2, 5e-4),
    ("w30_h64_lr2e3", 30, 64, 2, 2e-3),
    ("w25_h80",     25, 80, 2, 1e-3),
    ("w35_h72",     35, 72, 2, 1e-3),
    ("w30_h64_l1",  30, 64, 1, 1e-3),
    ("w30_h64_l3",  30, 64, 3, 1e-3),
    ("w15_h64",     15, 64, 2, 1e-3),
]
TOTAL = len(SWEEP)

# ----------------------------------------------------------------------------
# 状态 + 事件总线
# ----------------------------------------------------------------------------
state = {
    "status": "idle",
    "epoch": 0,
    "epochs": EPOCHS_M,
    "phase": "idle",
    "train_mse": None,
    "val_rmse": None,
    "elapsed": 0.0,
    "eta": None,
    "throughput": None,
    "final": None,
    "error": None,
    "sys": {"cpu": None, "mem": None, "disk": None, "proc_cpu": None, "rss_mb": None},
    "marathon": {"running": False, "round": 0, "index": 0, "total": TOTAL, "name": ""},
}
EVENTS: list[dict] = []
_lock = threading.Lock()
_event_id = 0
_train_thread: threading.Thread | None = None
_stop_marathon = threading.Event()
_abort_exp = threading.Event()
_intended = True  # 主进程是否应持续运行（仅在 Ctrl+C 时置 False）
_paused = False   # 用户暂停标志：为 True 时 watchdog 不拉起训练线程


def push_event(etype: str, data: dict) -> None:
    global _event_id
    with _lock:
        _event_id += 1
        EVENTS.append({"id": _event_id, "type": etype, "data": data})


def log(msg: str, level: str = "info") -> None:
    push_event("log", {"t": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})


# ----------------------------------------------------------------------------
# 系统指标采样
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
# 单个真实实验
# ----------------------------------------------------------------------------
def run_one_experiment(mod, window, hidden, num_layers, lr, seed, name, abort_ev):
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

    raw_dir = project_root() / "data/raw"
    log(f"[{name}] 加载 FD001 数据 ...", "info")
    push_event("phase", {"phase": "loading_data"})
    train_df, test_df, test_rul = load_subset(raw_dir, "FD001")
    train_df = add_rul_labels(train_df, rul_cap=RUL_CAP)
    keep = drop_constant_features(train_df, FEATURE_BASE)

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
    y_true_capped = np.minimum(y_true, RUL_CAP)

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
    model = RULSTM(n_features=len(keep), hidden=hidden, num_layers=num_layers, dropout=0.2).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    best_state = None
    t0 = time.time()
    epoch_times = []
    total_windows = int(tr_mask.sum())
    log(f"[{name}] 训练开始：{EPOCHS_M} epochs, hidden={hidden}, layers={num_layers}, lr={lr:.0e}", "info")
    push_event("phase", {"phase": "train"})

    for epoch in range(1, EPOCHS_M + 1):
        if abort_ev.is_set():
            return None
        ep_start = time.time()
        state["epoch"] = epoch
        state["phase"] = "train"
        push_event("phase", {"phase": "train", "epoch": epoch})
        model.train()
        tr_losses = []
        nb = 0
        for xb, yb in train_loader:
            if abort_ev.is_set():
                return None
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
            tr_losses.append(float(loss.item()))
            nb += 1
            if nb % 10 == 0:
                push_event("live_loss", {"epoch": epoch, "step": nb, "loss": float(loss.item()),
                                         "elapsed": round(time.time() - t0, 1)})
                log(f"[train] {name} ep {epoch:02d} step {nb:03d} loss={loss.item():.4f}", "debug")
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
        epoch_times.append(ep_t)
        elapsed = time.time() - t0
        avg_ep = sum(epoch_times) / len(epoch_times)
        eta = avg_ep * (EPOCHS_M - epoch)
        throughput = total_windows * epoch / elapsed if elapsed > 0 else 0.0
        state.update({"train_mse": tmse, "val_rmse": va_rmse, "elapsed": elapsed,
                      "eta": eta, "throughput": throughput})
        push_event("metric", {"epoch": epoch, "train_mse": tmse, "val_rmse": va_rmse,
                              "elapsed": round(elapsed, 1), "eta": round(eta, 1),
                              "throughput": round(throughput, 1), "best_val_rmse": best_val})
        log(f"[{name}] epoch {epoch:02d}/{EPOCHS_M}  mse={tmse:.4f}  val_rmse={va_rmse:.4f}  "
            f"({ep_t:.1f}s)  ETA {eta:.0f}s", "info")

    # 评估
    push_event("phase", {"phase": "eval"})
    log(f"[{name}] 训练完成，评估测试集 + MC Dropout ...", "info")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        y_pred = model(torch.from_numpy(x_te).to(device)).cpu().numpy()
    rmse_raw = rmse(y_true, y_pred)
    rmse_cap = rmse(y_true_capped, y_pred)
    mae_cap = mae(y_true_capped, y_pred)
    nasa_cap = nasa_score(y_true_capped, y_pred)
    mean_pred, std_pred = mc_dropout_predict(model, torch.from_numpy(x_te), n_samples=30, device=device)
    lo = mean_pred - 1.96 * std_pred
    hi = mean_pred + 1.96 * std_pred
    coverage = float(np.mean((y_true_capped >= lo) & (y_true_capped <= hi)))
    mean_std = float(std_pred.mean())
    rmse_mean = rmse(y_true_capped, mean_pred)
    push_event("preds", {"y_true": [round(float(v), 2) for v in y_true_capped],
                         "mean": [round(float(v), 2) for v in mean_pred],
                         "std": [round(float(v), 2) for v in std_pred]})
    push_event("unc", {"rmse_mean": rmse_mean, "coverage95": coverage, "mean_std": mean_std})
    xgb = 17.484151162176904
    final = {
        "name": name,
        "cfg": {"window": window, "hidden": hidden, "num_layers": num_layers, "lr": lr, "seed": seed},
        "rmse_raw_rul": rmse_raw,
        "rmse_capped125": rmse_cap,
        "mae_capped125": mae_cap,
        "nasa_score_capped125": nasa_cap,
        "baseline_xgboost_rmse_capped125": xgb,
        "beat_xgboost_rmse": bool(rmse_cap < xgb),
        "best_val_rmse": best_val,
        "rmse_mean_mcdropout": rmse_mean,
        "coverage95_mcdropout": coverage,
        "mean_std_mcdropout": mean_std,
        "elapsed_total": round(time.time() - t0, 1),
    }
    push_event("done", final)
    log(f"[{name}] 完成 → RMSE(cap125)={rmse_cap:.3f}  MAE={mae_cap:.3f}  "
        f"NASA={nasa_cap:.1f}  击败XGBoost={final['beat_xgboost_rmse']}", "success")
    return final


def save_experiment(name, final, round_idx):
    exp_dir = ROOT / "experiments" / name
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "metrics.json").write_text(
        json.dumps({"metrics": final, "round": round_idx + 1}, ensure_ascii=False, indent=2),
        encoding="utf-8")


def rotate_experiments(current_round):
    """只保留最近 2 轮的实验目录，避免无限膨胀。"""
    exp_root = ROOT / "experiments"
    if not exp_root.exists():
        return
    for d in exp_root.iterdir():
        if not d.is_dir():
            continue
        try:
            r = int(d.name.split("_")[0].lstrip("r"))
        except Exception:
            continue
        if r < current_round - 1:
            try:
                for f in d.iterdir():
                    f.unlink()
                d.rmdir()
            except Exception:
                pass


# ----------------------------------------------------------------------------
# 马拉松主循环
# ----------------------------------------------------------------------------
def run_marathon():
    global _train_thread
    try:
        import numpy as np  # noqa
        state["marathon"]["running"] = True
        log("🏃 马拉松模式启动：超参扫描连续训练，跑完一轮自动换种子续跑（无限循环）。", "info")
        round_idx = 0
        while not _stop_marathon.is_set():
            round_seed_base = 42 + round_idx * 1000
            push_event("marathon", {"kind": "round_start", "round": round_idx + 1})
            log(f"===== 马拉松 第 {round_idx + 1} 轮 / 共 {TOTAL} 个实验 =====", "info")
            for i, (tag, window, hidden, num_layers, lr) in enumerate(SWEEP):
                if _stop_marathon.is_set():
                    break
                _abort_exp.clear()
                seed = round_seed_base + i * 7
                name = f"r{round_idx + 1:02d}_{tag}"
                state["marathon"].update({"round": round_idx + 1, "index": i + 1, "total": TOTAL, "name": name})
                push_event("exp_start", {"round": round_idx + 1, "index": i + 1, "total": TOTAL,
                                         "name": name, "cfg": {"window": window, "hidden": hidden,
                                                               "num_layers": num_layers, "lr": lr, "seed": seed}})
                log(f"▶ 实验 {i + 1}/{TOTAL}：{name}  (win={window}, hid={hidden}, "
                    f"layers={num_layers}, lr={lr:.0e}, seed={seed})", "info")
                try:
                    final = run_one_experiment(tag, window, hidden, num_layers, lr, seed, name, _abort_exp)
                except Exception as e:  # noqa
                    log(f"✗ 实验 {name} 异常，跳过：{e}", "error")
                    continue
                if final is None:
                    log(f"⏭ 实验 {name} 被手动跳过", "info")
                    continue
                save_experiment(name, final, round_idx)
                time.sleep(1.5)
            rotate_experiments(round_idx + 1)
            round_idx += 1
            if _stop_marathon.is_set():
                break
            log(f"✓ 第 {round_idx} 轮完成，换随机种子进入下一轮 ...", "info")
            time.sleep(2)
        state["marathon"]["running"] = False
        log("马拉松已停止。", "info")
    except Exception as e:  # noqa
        state["marathon"]["running"] = False
        log(f"马拉松异常退出：{e}", "error")
    finally:
        _train_thread = None


def start_marathon():
    global _train_thread
    # 若已有线程在跑，先停下并等其真正退出，避免竞态导致 stop 标志残留
    if _train_thread and _train_thread.is_alive():
        _stop_marathon.set()
        _train_thread.join(timeout=30)
    _stop_marathon.clear()
    _train_thread = threading.Thread(target=run_marathon, daemon=True)
    _train_thread.start()


def watchdog():
    """看门狗：训练线程若意外死亡且未主动停止/暂停，自动拉起，保证一直跑着。"""
    while _intended:
        if (not _paused and not _stop_marathon.is_set()
                and (_train_thread is None or not _train_thread.is_alive())):
            log("⚠️ 训练线程意外停止，自动重启马拉松 ...", "warn")
            start_marathon()
        time.sleep(5)


# ----------------------------------------------------------------------------
# HTTP
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
                state["marathon"]["paused"] = _paused
                body = json.dumps(state).encode("utf-8")
            self._send(200, body)
        elif path == "/experiments":
            self._experiments()
        elif path == "/file":
            self._file(parsed)
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        global _paused
        parsed = urlparse(self.path)
        if parsed.path == "/start":
            # 重启马拉松（同时清除暂停）
            _paused = False
            _stop_marathon.set()
            time.sleep(0.3)
            start_marathon()
            self._send(200, json.dumps({"ok": True, "status": "restarted"}).encode("utf-8"))
        elif parsed.path == "/skip":
            # 跳过当前实验
            _abort_exp.set()
            self._send(200, json.dumps({"ok": True, "status": "skip"}).encode("utf-8"))
        elif parsed.path == "/pause":
            # 暂停：停止训练线程，但 HTTP 服务保留，watchdog 不再拉起
            _paused = True
            _stop_marathon.set()
            self._send(200, json.dumps({"ok": True, "status": "paused"}).encode("utf-8"))
        elif parsed.path == "/resume":
            # 恢复：清除暂停与停止标志，拉起训练线程
            _paused = False
            start_marathon()
            self._send(200, json.dumps({"ok": True, "status": "resumed"}).encode("utf-8"))
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
            return

    def _stream_loop(self):
        last_id = 0
        hdr = self.headers.get("Last-Event-ID")
        if hdr and hdr.isdigit():
            last_id = int(hdr)
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
            try:
                blob = {"id": _event_id, "type": "sys", "data": state["sys"]}
                self.wfile.write(f"id: {_event_id + 1}\n".encode("utf-8"))
                self.wfile.write(f"data: {json.dumps(blob, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
            except Exception:
                return
            time.sleep(1.0)

    def log_message(self, *args):
        pass


def main():
    global _intended
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"EdgePdM-Agent 训练马拉松已启动： http://127.0.0.1:{PORT}")
    print("超参扫描连续训练中 ... (Ctrl+C 退出，或浏览器点 '⏭ 跳过')")
    start_marathon()
    threading.Thread(target=watchdog, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _intended = False
        _stop_marathon.set()
        print("\n已停止")


if __name__ == "__main__":
    main()
