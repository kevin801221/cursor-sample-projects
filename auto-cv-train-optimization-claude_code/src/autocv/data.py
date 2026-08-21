"""從 Roboflow Universe 下載資料集到 paths.raw。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from autocv.config import Config


def download(cfg: Config, root: Path) -> Path:
    """下載資料集，回傳下載目錄。"""
    load_dotenv(root / ".env")
    api_key = os.getenv(cfg.roboflow.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"{cfg.roboflow.api_key_env} 未設定，請複製 .env.example 成 .env 並填入"
        )

    from roboflow import Roboflow

    dest = root / cfg.paths.raw
    dest.mkdir(parents=True, exist_ok=True)
    rf = Roboflow(api_key=api_key)
    project = rf.workspace(cfg.roboflow.workspace).project(cfg.roboflow.project)
    dataset = project.version(cfg.roboflow.version).download(
        cfg.roboflow.format, location=str(dest), overwrite=True
    )
    print(f"DOWNLOAD_OK: {dataset.location}")
    return Path(dataset.location)
