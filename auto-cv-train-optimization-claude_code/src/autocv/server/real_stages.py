"""把 autocv 五階段包成 Stage，捕捉 stdout 成 log 事件；train/optimize tail results.csv 推訓練曲線。"""

from __future__ import annotations

import csv
import io
import threading
import time
from pathlib import Path

from autocv.config import Config
from autocv.server.events import Event
from autocv.server.runner import Stage


import sys


class RealtimeStream(io.TextIOBase):
    def __init__(self, emit_fn, original_stream=None):
        self.emit_fn = emit_fn
        self.original_stream = original_stream
        self.buffer = ""

    def write(self, s: str) -> int:
        if self.original_stream:
            try:
                self.original_stream.write(s)
                self.original_stream.flush()
            except Exception:
                pass
        self.buffer += s
        while "\n" in self.buffer or "\r" in self.buffer:
            n_idx = self.buffer.find("\n")
            r_idx = self.buffer.find("\r")
            if n_idx != -1 and (r_idx == -1 or n_idx < r_idx):
                line, self.buffer = self.buffer[:n_idx], self.buffer[n_idx + 1:]
            else:
                line, self.buffer = self.buffer[:r_idx], self.buffer[r_idx + 1:]
            line = line.strip()
            if line:
                self.emit_fn(Event("log", payload={"line": line}))
        return len(s)

    def flush(self) -> None:
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass
        if self.buffer.strip():
            self.emit_fn(Event("log", payload={"line": self.buffer.strip()}))
            self.buffer = ""


def _logged(fn, emit) -> object:
    orig_out = sys.stdout
    orig_err = sys.stderr
    out_stream = RealtimeStream(emit, original_stream=orig_out)
    err_stream = RealtimeStream(emit, original_stream=orig_err)
    sys.stdout = out_stream
    sys.stderr = err_stream
    try:
        return fn()
    finally:
        out_stream.flush()
        err_stream.flush()
        sys.stdout = orig_out
        sys.stderr = orig_err


def _emit_metric_row(emit, row: dict, idx: int, t0: float, total_epochs: int) -> None:
    try:
        epoch = int(float(row.get("epoch", idx + 1)))
        elapsed = round(time.time() - t0)
        # ETA 用「已耗時 / 已完成 epoch × 剩餘 epoch」估；重播歷史（去重時）elapsed≈0 → eta 0
        eta = round(elapsed / max(epoch, 1) * max(total_epochs - epoch, 0)) if total_epochs else 0
        emit(
            Event(
                "metric",
                "train",
                {
                    "epoch": epoch,
                    "total_epochs": total_epochs,
                    "elapsed_s": elapsed,
                    "eta_s": eta,
                    "map50": float(row.get("metrics/mAP50(B)") or 0),
                    "map": float(row.get("metrics/mAP50-95(B)") or 0),
                    "loss": float(row.get("train/box_loss") or 0),
                },
            )
        )
    except Exception:
        pass


def _start_csv_tail(
    csv_path: Path, emit, total_epochs: int = 0
) -> tuple[threading.Event, threading.Thread, list]:
    """背景 thread 邊跑邊讀 results.csv，每多一列就推 metric 事件。"""
    stop = threading.Event()
    seen = [0]
    t0 = time.time()

    def watcher() -> None:
        while not stop.is_set():
            if csv_path.exists():
                try:
                    with csv_path.open() as f:
                        rows = list(csv.DictReader(f))
                    while seen[0] < len(rows):
                        _emit_metric_row(emit, rows[seen[0]], seen[0], t0, total_epochs)
                        seen[0] += 1
                except Exception:
                    pass
            stop.wait(1.0)

    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    return stop, t, seen


def _final_flush(csv_path: Path, emit, seen: list, total_epochs: int = 0) -> None:
    if not csv_path.exists():
        return
    try:
        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        t0 = time.time()
        while seen[0] < len(rows):
            _emit_metric_row(emit, rows[seen[0]], seen[0], t0, total_epochs)
            seen[0] += 1
    except Exception:
        pass


def build_stages(cfg: Config, root: Path, optimize: bool) -> list[Stage]:
    from autocv.data import download
    from autocv.infer import infer
    from autocv.split import split

    runs_dir = root / cfg.paths.runs

    def data_run(emit):
        loc = _logged(lambda: download(cfg, root), emit)
        if loc:
            emit(Event("result", "data", {"location": str(loc)}))

    def split_run(emit):
        _logged(lambda: split(cfg, root), emit)

    def train_run(emit):
        from autocv.train import train

        run_dir = runs_dir / cfg.train.name
        csv_path = run_dir / "results.csv"
        # 去重沿用權重時不清 csv：watcher 會重播歷史列，曲線立即補齊
        if not (run_dir / "weights" / "best.pt").exists():
            csv_path.unlink(missing_ok=True)  # 清舊列避免 watcher emit 上一輪歷史
        stop, t, seen = _start_csv_tail(csv_path, emit, total_epochs=cfg.train.epochs)
        try:
            _logged(lambda: train(cfg, root, yes=True), emit)
        finally:
            stop.set()
            t.join(timeout=2)
            _final_flush(csv_path, emit, seen, total_epochs=cfg.train.epochs)

    def opt_run(emit):
        from autocv.optimize import optimize as do_opt

        csv_path = runs_dir / "tune" / "results.csv"
        csv_path.unlink(missing_ok=True)
        stop, t, seen = _start_csv_tail(csv_path, emit, total_epochs=cfg.optimize.epochs)
        try:
            _logged(lambda: do_opt(cfg, root, yes=True), emit)
        finally:
            stop.set()
            t.join(timeout=2)
            _final_flush(csv_path, emit, seen, total_epochs=cfg.optimize.epochs)

    def infer_run(emit):
        def on_single_image(png_path: Path, raw_name: str, box_count: int, boxes: list):
            emit(
                Event(
                    "image_stream",
                    "infer",
                    {
                        "url": f"/artifacts/{png_path.name}",
                        "name": raw_name,
                        "box_count": box_count,
                        "boxes": boxes,
                    },
                )
            )

        def on_eval_done(eval_data: dict):
            emit(Event("eval_stream", "infer", eval_data))

        out_dir = _logged(
            lambda: infer(
                cfg,
                root,
                on_image=on_single_image,
                on_eval=on_eval_done,
            ),
            emit,
        )
        if out_dir:
            pngs = sorted(Path(out_dir).glob("pred_*.png"))
            emit(
                Event(
                    "result",
                    "infer",
                    {"images": [f"/artifacts/{p.name}" for p in pngs]},
                )
            )

    def report_run(emit):
        import json

        from autocv.report import discover_runs
        from autocv.report import report as do_report

        _logged(lambda: do_report(cfg, root), emit)
        data_yaml = root / cfg.paths.processed / "data.yaml"
        rows = []
        for d in discover_runs(runs_dir, data_yaml):
            mfile = d / "metrics.json"
            if not mfile.exists():
                continue
            m = json.loads(mfile.read_text())
            args = m.get("args", {})
            rows.append(
                {
                    "name": m["name"],
                    "model": Path(str(args.get("model", ""))).name,
                    "imgsz": args.get("imgsz"),
                    "val_map50": m["val"]["map50"],
                    "val_map": m["val"]["map"],
                    "test_map50": m["test"]["map50"],
                    "test_map": m["test"]["map"],
                }
            )
        report_pngs = (
            "ladder.png",
            "training_curves.png",
            "per_class_ap.png",
            "confusion_matrix_normalized.png",
        )
        emit(
            Event(
                "result",
                "report",
                {
                    "runs": rows,
                    "images": [
                        f"/artifacts/{n}" for n in report_pngs if (runs_dir / "report" / n).exists()
                    ],
                },
            )
        )

    def train_estimate() -> float:
        if (runs_dir / cfg.train.name / "weights" / "best.pt").exists():
            return 0.0  # 已訓練過：train 會直接沿用權重，不需守門
        from autocv.train import _count_train_imgs, _estimate_minutes

        n = _count_train_imgs(root / cfg.paths.processed)
        return round(_estimate_minutes(n, cfg.train.epochs, cfg.train.batch), 1)

    mid = (
        Stage("optimize", opt_run, estimate=lambda: float(cfg.optimize.iterations))
        if optimize
        else Stage("train", train_run, estimate=train_estimate)
    )
    return [
        Stage("data", data_run),
        Stage("split", split_run),
        mid,
        Stage("infer", infer_run),
        Stage("report", report_run),
    ]
