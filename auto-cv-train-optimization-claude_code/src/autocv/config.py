"""載入並驗證 config.yaml。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class RoboflowCfg:
    workspace: str
    project: str
    version: int
    format: str = "yolov8"
    api_key_env: str = "ROBOFLOW_API_KEY"


@dataclass
class PathsCfg:
    raw: str = "data/raw"
    processed: str = "data/processed"
    runs: str = "runs"


@dataclass
class DatasetCfg:
    split: list[float] = field(default_factory=lambda: [0.7, 0.2, 0.1])
    seed: int = 42


@dataclass
class TrainCfg:
    model: str = "yolov8n.pt"
    epochs: int = 50
    batch: int = 8
    imgsz: int = 416
    device: str = "auto"


@dataclass
class OptimizeCfg:
    iterations: int = 20
    epochs: int = 15


@dataclass
class InferCfg:
    conf: float = 0.25
    num_samples: int = 10


@dataclass
class Config:
    roboflow: RoboflowCfg
    paths: PathsCfg = field(default_factory=PathsCfg)
    dataset: DatasetCfg = field(default_factory=DatasetCfg)
    train: TrainCfg = field(default_factory=TrainCfg)
    optimize: OptimizeCfg = field(default_factory=OptimizeCfg)
    infer: InferCfg = field(default_factory=InferCfg)

    @classmethod
    def from_dict(cls, raw: dict) -> Config:
        if "roboflow" not in raw:
            raise ValueError("config 缺少 roboflow 區塊")
        rf = RoboflowCfg(**raw["roboflow"])
        dataset = DatasetCfg(**raw.get("dataset", {}))
        if abs(sum(dataset.split) - 1.0) > 1e-6 or len(dataset.split) != 3:
            raise ValueError("dataset.split 必須是 3 個和為 1 的比例")
        return cls(
            roboflow=rf,
            paths=PathsCfg(**raw.get("paths", {})),
            dataset=dataset,
            train=TrainCfg(**raw.get("train", {})),
            optimize=OptimizeCfg(**raw.get("optimize", {})),
            infer=InferCfg(**raw.get("infer", {})),
        )


def load_config(path: str | Path) -> Config:
    """讀 YAML 檔並回傳驗證過的 Config。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到 config: {path}")
    return Config.from_dict(yaml.safe_load(path.read_text()))
