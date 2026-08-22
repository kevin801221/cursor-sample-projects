from pathlib import Path

import pytest

from autocv.config import Config, load_config

WAFER = Path("configs/wafer.yaml")


def test_load_wafer_config():
    cfg = load_config(WAFER)
    assert isinstance(cfg, Config)
    assert cfg.roboflow.workspace == "wm811k-paasr"
    assert cfg.roboflow.version == 3
    assert cfg.dataset.split == [0.7, 0.2, 0.1]
    assert cfg.train.model == "yolov8n.pt"
    assert cfg.optimize.iterations == 20
    assert cfg.infer.num_samples == 10
    assert cfg.paths.raw == "data/raw"


def test_split_must_sum_to_one():
    with pytest.raises(ValueError, match="split"):
        Config.from_dict(
            {
                "roboflow": {"workspace": "w", "project": "p", "version": 1},
                "dataset": {"split": [0.5, 0.2, 0.1]},
            }
        )


def test_missing_roboflow_section_raises():
    with pytest.raises(ValueError, match="roboflow"):
        Config.from_dict({"dataset": {"split": [0.7, 0.2, 0.1]}})


def test_load_aquarium_config_train_name():
    cfg = load_config(Path("configs/aquarium.yaml"))
    assert cfg.train.name == "aq-n-640"
    assert cfg.paths.raw == "data/raw/aquarium"


def test_train_name_defaults_to_train():
    cfg = Config.from_dict({"roboflow": {"workspace": "w", "project": "p", "version": 1}})
    assert cfg.train.name == "train"
