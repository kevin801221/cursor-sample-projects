"""YOLOv8 訓練，預設先報預估時間並等使用者確認。"""

from __future__ import annotations

import math
import time
from pathlib import Path

import typer

from autocv.config import Config
from autocv.device import pick_device


def _count_train_imgs(processed: Path) -> int:
    d = processed / "images" / "train"
    if not d.is_dir():
        return 0
    return sum(1 for _ in d.iterdir())


def _estimate_minutes(n_imgs: int, epochs: int, batch: int) -> float:
    iters = math.ceil(max(n_imgs, 1) / batch) * epochs
    return iters * 0.2 / 60.0


def train(cfg: Config, root: Path, yes: bool = False) -> Path:
    """訓練並回傳 best.pt 路徑。"""
    data_yaml = root / cfg.paths.processed / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"找不到 {data_yaml}，請先跑 autocv split")

    device = pick_device(cfg.train.device)
    n_imgs = _count_train_imgs(root / cfg.paths.processed)
    est = _estimate_minutes(n_imgs, cfg.train.epochs, cfg.train.batch)
    typer.echo(
        f"📊 訓練預估\n"
        f"- train 圖片: {n_imgs}\n"
        f"- epochs={cfg.train.epochs} batch={cfg.train.batch} device={device}\n"
        f"- 預估時間: 約 {est:.1f} 分鐘\n"
        f"- 輸出: {root / cfg.paths.runs}/train/"
    )
    if not yes and not typer.confirm("要開始訓練嗎？"):
        raise typer.Abort()

    from ultralytics import YOLO

    t0 = time.time()
    model = YOLO(cfg.train.model)
    results = model.train(
        data=str(data_yaml),
        epochs=cfg.train.epochs,
        batch=cfg.train.batch,
        imgsz=cfg.train.imgsz,
        device=device,
        project=str(root / cfg.paths.runs),
        name="train",
        exist_ok=True,
    )
    best = Path(results.save_dir) / "weights" / "best.pt"
    typer.echo(f"耗時 {(time.time() - t0) / 60:.2f} 分鐘  best.pt -> {best}")
    return best
