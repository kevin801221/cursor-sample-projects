"""推論並產出帶 bbox 的視覺化 PNG 與 summary.md。"""

from __future__ import annotations

import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

from autocv.config import Config  # noqa: E402
from autocv.device import pick_device  # noqa: E402


def _latest_best(runs: Path) -> Path:
    cands = sorted(runs.glob("*/weights/best.pt"), key=lambda p: p.stat().st_mtime)
    if not cands:
        raise SystemExit(f"{runs} 下找不到 best.pt，請先跑 autocv train 或 optimize")
    return cands[-1]


def infer(
    cfg: Config,
    root: Path,
    on_image: object | None = None,
    on_eval: object | None = None,
) -> Path:
    """推論 + 視覺化，支援單張完成即時回調 (on_image) 與評估回調 (on_eval)，回傳輸出目錄。"""
    runs = root / cfg.paths.runs
    named = runs / cfg.train.name / "weights" / "best.pt"
    best = named if named.exists() else _latest_best(runs)
    processed = root / cfg.paths.processed
    test_dir = processed / "images" / "test"
    if not test_dir.is_dir() or not any(test_dir.iterdir()):
        test_dir = processed / "images" / "val"
        print("test/ 不存在或為空，改用 val/")

    out_dir = runs / "infer"
    out_dir.mkdir(parents=True, exist_ok=True)
    device = pick_device(cfg.train.device)

    from ultralytics import YOLO

    model = YOLO(str(best))
    random.seed(cfg.dataset.seed)
    imgs = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    sample = random.sample(imgs, min(cfg.infer.num_samples, len(imgs)))

    lines: list[str] = ["# Inference Summary\n", f"- 模型：`{best}`\n"]
    for img_path in sample:
        result = model.predict(str(img_path), conf=cfg.infer.conf, device=device)[0]
        img = Image.open(img_path)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(img)
        detected_boxes = []
        if len(result.boxes) == 0:
            ax.set_title(f"{img_path.name} — No prediction")
        else:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls = result.names[int(box.cls[0])]
                conf = float(box.conf[0])
                detected_boxes.append({"class": cls, "conf": round(conf, 3), "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]})
                ax.add_patch(
                    patches.Rectangle(
                        (x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="red", linewidth=2
                    )
                )
                ax.text(
                    x1,
                    y1 - 5,
                    f"{cls} {conf:.2f}",
                    color="white",
                    bbox=dict(facecolor="red", alpha=0.7),
                )
            ax.set_title(img_path.name)
        ax.axis("off")
        out_png = out_dir / f"pred_{img_path.name}.png"
        plt.savefig(out_png, dpi=100, bbox_inches="tight")
        plt.close()
        lines.append(f"![{out_png.stem}]({out_png.name})\n")

        if callable(on_image):
            try:
                on_image(out_png, img_path.name, len(detected_boxes), detected_boxes)
            except Exception:
                pass

    data_yaml = processed / "data.yaml"
    try:
        metrics = model.val(data=str(data_yaml), split="test")
    except Exception:
        metrics = model.val(data=str(data_yaml), split="val")

    eval_info = {
        "map50": round(float(metrics.box.map50), 4),
        "map": round(float(metrics.box.map), 4),
        "precision": round(float(metrics.box.mp), 4) if hasattr(metrics.box, "mp") else None,
        "recall": round(float(metrics.box.mr), 4) if hasattr(metrics.box, "mr") else None,
    }

    lines.insert(
        2,
        f"- mAP@0.5: {eval_info['map50']:.4f}  mAP@0.5:0.95: {eval_info['map']:.4f}\n",
    )
    (out_dir / "summary.md").write_text("\n".join(lines))
    print(f"summary.md -> {out_dir / 'summary.md'}")
    print(f"mAP@0.5: {eval_info['map50']:.4f}  mAP@0.5:0.95: {eval_info['map']:.4f}")

    if callable(on_eval):
        try:
            on_eval(eval_info)
        except Exception:
            pass

    return out_dir
