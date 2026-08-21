"""Ultralytics 內建 tuner 做超參搜尋，回傳最佳結果目錄。"""

from __future__ import annotations

import time
from pathlib import Path

import typer

from autocv.config import Config
from autocv.device import pick_device


def optimize(cfg: Config, root: Path, yes: bool = False) -> Path:
    """跑超參搜尋並回傳 tune 結果目錄。"""
    data_yaml = root / cfg.paths.processed / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"找不到 {data_yaml}，請先跑 autocv split")

    device = pick_device(cfg.train.device)
    typer.echo(
        f"🔧 超參優化預估\n"
        f"- iterations={cfg.optimize.iterations} 每輪 epochs={cfg.optimize.epochs}\n"
        f"- device={device}（每輪都是一次短訓，總時間 ≈ iterations × 單輪）\n"
        f"- 輸出: {root / cfg.paths.runs}/tune/"
    )
    if not yes and not typer.confirm("要開始超參搜尋嗎？（很耗時）"):
        raise typer.Abort()

    from ultralytics import YOLO

    t0 = time.time()
    model = YOLO(cfg.train.model)
    model.tune(
        data=str(data_yaml),
        epochs=cfg.optimize.epochs,
        iterations=cfg.optimize.iterations,
        imgsz=cfg.train.imgsz,
        batch=cfg.train.batch,
        device=device,
        project=str(root / cfg.paths.runs),
        name="tune",
        exist_ok=True,
    )
    tune_dir = root / cfg.paths.runs / "tune"
    typer.echo(
        f"耗時 {(time.time() - t0) / 60:.2f} 分鐘\n"
        f"最佳超參 -> {tune_dir / 'best_hyperparameters.yaml'}"
    )
    return tune_dir
