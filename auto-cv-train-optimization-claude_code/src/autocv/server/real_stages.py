"""把 autocv 五階段包成 Stage，捕捉 stdout 成 log 事件；train/optimize tail results.csv 推訓練曲線。"""

from __future__ import annotations

import contextlib
import csv
import io
import threading
from pathlib import Path

from autocv.config import Config
from autocv.server.events import Event
from autocv.server.runner import Stage


def _logged(fn, emit) -> object:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn()
    for line in buf.getvalue().splitlines():
        if line.strip():
            emit(Event("log", payload={"line": line}))
    return result


def _emit_metric_row(emit, row: dict, idx: int) -> None:
    try:
        emit(
            Event(
                "metric",
                "train",
                {
                    "epoch": int(float(row.get("epoch", idx + 1))),
                    "map50": float(row.get("metrics/mAP50(B)") or 0),
                    "map": float(row.get("metrics/mAP50-95(B)") or 0),
                    "loss": float(row.get("train/box_loss") or 0),
                },
            )
        )
    except Exception:
        pass


def _start_csv_tail(csv_path: Path, emit) -> tuple[threading.Event, threading.Thread, list]:
    """背景 thread 邊跑邊讀 results.csv，每多一列就推 metric 事件。"""
    stop = threading.Event()
    seen = [0]

    def watcher() -> None:
        while not stop.is_set():
            if csv_path.exists():
                try:
                    with csv_path.open() as f:
                        rows = list(csv.DictReader(f))
                    while seen[0] < len(rows):
                        _emit_metric_row(emit, rows[seen[0]], seen[0])
                        seen[0] += 1
                except Exception:
                    pass
            stop.wait(1.0)

    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    return stop, t, seen


def _final_flush(csv_path: Path, emit, seen: list) -> None:
    if not csv_path.exists():
        return
    try:
        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        while seen[0] < len(rows):
            _emit_metric_row(emit, rows[seen[0]], seen[0])
            seen[0] += 1
    except Exception:
        pass


def build_stages(cfg: Config, root: Path, optimize: bool) -> list[Stage]:
    from autocv.data import download
    from autocv.infer import infer
    from autocv.split import split

    runs_dir = root / cfg.paths.runs

    def data_run(emit):
        _logged(lambda: download(cfg, root), emit)

    def split_run(emit):
        _logged(lambda: split(cfg, root), emit)

    def train_run(emit):
        from autocv.train import train

        csv_path = runs_dir / "train" / "results.csv"
        csv_path.unlink(missing_ok=True)  # 清舊列避免 watcher emit 上一輪歷史
        stop, t, seen = _start_csv_tail(csv_path, emit)
        try:
            _logged(lambda: train(cfg, root, yes=True), emit)
        finally:
            stop.set()
            t.join(timeout=2)
            _final_flush(csv_path, emit, seen)

    def opt_run(emit):
        from autocv.optimize import optimize as do_opt

        csv_path = runs_dir / "tune" / "results.csv"
        csv_path.unlink(missing_ok=True)
        stop, t, seen = _start_csv_tail(csv_path, emit)
        try:
            _logged(lambda: do_opt(cfg, root, yes=True), emit)
        finally:
            stop.set()
            t.join(timeout=2)
            _final_flush(csv_path, emit, seen)

    def infer_run(emit):
        out_dir = _logged(lambda: infer(cfg, root), emit)
        if out_dir:
            pngs = sorted(Path(out_dir).glob("pred_*.png"))
            emit(
                Event(
                    "result",
                    "infer",
                    {"images": [f"/artifacts/{p.name}" for p in pngs]},
                )
            )

    def train_estimate() -> float:
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
    ]
