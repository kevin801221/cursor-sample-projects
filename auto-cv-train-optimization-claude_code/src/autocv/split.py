"""驗證 YOLO 標註並切分 train/val/test，產生 data.yaml。"""

from __future__ import annotations

import random
import shutil
from collections import Counter
from pathlib import Path

import yaml

from autocv.config import Config

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def validate_label_file(label_path: Path) -> tuple[list[str], list[int], int]:
    """回傳 (errors, class_ids, bbox_count)。"""
    errors: list[str] = []
    class_ids: list[int] = []
    bbox_count = 0
    if not label_path.exists():
        return [f"{label_path.name}: 缺少 label 檔"], class_ids, 0
    for lineno, raw in enumerate(label_path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{label_path.name}:L{lineno} 欄位數 != 5")
            continue
        try:
            cid = int(parts[0])
            cx, cy, w, h = (float(x) for x in parts[1:])
        except ValueError:
            errors.append(f"{label_path.name}:L{lineno} 解析失敗")
            continue
        if cid < 0:
            errors.append(f"{label_path.name}:L{lineno} class_id 為負")
        for name, val in (("cx", cx), ("cy", cy), ("w", w), ("h", h)):
            if not (0.0 <= val <= 1.0):
                errors.append(f"{label_path.name}:L{lineno} {name}={val} 超出 [0,1]")
        class_ids.append(cid)
        bbox_count += 1
    return errors, class_ids, bbox_count


def _find_src(raw_dir: Path) -> tuple[Path, Path, Path]:
    """找出 raw 下的 images / labels / data.yaml（相容 train/ 子層）。"""
    for base in (raw_dir, raw_dir / "train"):
        img_dir = base / "images"
        lbl_dir = base / "labels"
        if img_dir.is_dir() and lbl_dir.is_dir():
            yaml_path = raw_dir / "data.yaml"
            return img_dir, lbl_dir, yaml_path
    raise FileNotFoundError(f"{raw_dir} 下找不到 images/ 與 labels/，請先跑 autocv data")


def split(cfg: Config, root: Path) -> Path:
    """執行驗證 + 切分，回傳 processed/data.yaml 路徑。"""
    raw_dir = root / cfg.paths.raw
    out_dir = root / cfg.paths.processed
    img_dir, lbl_dir, raw_yaml = _find_src(raw_dir)

    raw_cfg = yaml.safe_load(raw_yaml.read_text())
    names = raw_cfg["names"]
    nc = raw_cfg["nc"]

    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXTS)
    print(f"圖片總數: {len(images)}")

    all_errors: list[str] = []
    class_counter: Counter[int] = Counter()
    total_bbox = 0
    empty_labels = 0
    paired: list[tuple[Path, Path]] = []
    for img in images:
        lbl = lbl_dir / f"{img.stem}.txt"
        errors, cids, bcount = validate_label_file(lbl)
        all_errors.extend(errors)
        class_counter.update(cids)
        total_bbox += bcount
        if bcount == 0:
            empty_labels += 1
        if lbl.exists():
            paired.append((img, lbl))

    print(f"label 配對成功: {len(paired)}  bbox 總數: {total_bbox}  空 label: {empty_labels}")
    print(f"類別分佈: {dict(class_counter)}  異常行數: {len(all_errors)}")
    for e in all_errors[:5]:
        print(f"  - {e}")

    if total_bbox and len(all_errors) / total_bbox > 0.1:
        raise SystemExit(f"格式錯誤比例 > 10%（{len(all_errors)}/{total_bbox}），中止")

    rng = random.Random(cfg.dataset.seed)
    shuffled = paired.copy()
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * cfg.dataset.split[0])
    n_val = int(n * cfg.dataset.split[1])
    splits = {
        "train": shuffled[:n_train],
        "val": shuffled[n_train : n_train + n_val],
        "test": shuffled[n_train + n_val :],
    }
    for s in splits:
        (out_dir / "images" / s).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / s).mkdir(parents=True, exist_ok=True)
    for s, items in splits.items():
        for img, lbl in items:
            shutil.copy2(img, out_dir / "images" / s / img.name)
            shutil.copy2(lbl, out_dir / "labels" / s / lbl.name)
        print(f"{s}: {len(items)} 張")

    out_yaml = {
        "path": str(out_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": nc,
        "names": {i: nm for i, nm in enumerate(names)} if isinstance(names, list) else names,
    }
    yaml_path = out_dir / "data.yaml"
    yaml_path.write_text(yaml.safe_dump(out_yaml, sort_keys=False, allow_unicode=True))
    print(f"data.yaml -> {yaml_path}")
    return yaml_path
