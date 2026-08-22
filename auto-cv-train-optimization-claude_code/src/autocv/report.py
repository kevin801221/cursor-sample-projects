"""評估所有訓練 run 並產出 metric 視覺化 + report.md（優化階梯的成績單）。"""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402

from autocv.config import Config  # noqa: E402
from autocv.device import pick_device  # noqa: E402

# dataviz 已驗證分類色盤（固定順序，不可循環重配）
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
GRID = {"axis": "y", "color": "#e5e5e5", "linewidth": 0.8}


def discover_runs(runs: Path, data_yaml: Path | None = None) -> list[Path]:
    """回傳含 weights/best.pt 的 run 目錄，依 best.pt mtime 排序（= 訓練先後 = 階梯順序）。

    給 data_yaml 時，只保留 args.yaml 的 data 指向同一資料集的 run——
    共用 runs/ 目錄下別的資料集或超參試驗（tune*）不進階梯表。
    """
    dirs = sorted(
        (p.parent.parent for p in runs.glob("*/weights/best.pt")),
        key=lambda d: (d / "weights" / "best.pt").stat().st_mtime,
    )
    kept: list[Path] = []
    for d in dirs:
        if d.name.startswith("tune"):
            continue
        if data_yaml is not None and (d / "args.yaml").exists():
            args_data = yaml.safe_load((d / "args.yaml").read_text()).get("data")
            if args_data and Path(args_data).resolve() != data_yaml.resolve():
                continue
        kept.append(d)
    return kept


def parse_results_csv(csv_path: Path) -> dict[str, list[float]]:
    """讀 ultralytics results.csv → {欄名: 數列}（欄名去空白，非數值略過）。"""
    cols: dict[str, list[float]] = {}
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                if k is None:
                    continue
                try:
                    cols.setdefault(k.strip(), []).append(float(v))
                except (TypeError, ValueError):
                    pass
    return cols


def label_stats(labels_dir: Path) -> tuple[Counter[int], list[float]]:
    """掃 YOLO label txt → (類別實例數, bbox 面積比例 w*h 列表)。"""
    counter: Counter[int] = Counter()
    areas: list[float] = []
    for lbl in sorted(labels_dir.glob("*.txt")):
        for line in lbl.read_text().splitlines():
            parts = line.split()
            if len(parts) != 5:
                continue
            try:
                cid = int(parts[0])
                area = float(parts[3]) * float(parts[4])
            except ValueError:
                continue  # split 容忍 <10% 錯誤行，統計時跳過即可
            counter[cid] += 1
            areas.append(area)
    return counter, areas


def render_ladder_md(metrics: list[dict]) -> str:
    """把各 run 的 metrics dict 渲染成階梯表（val/test 並列，test mAP@0.5:0.95 附漲幅）。"""
    header = (
        "| Run | model | imgsz | epochs | val mAP@0.5 | val mAP@0.5:0.95 "
        "| test mAP@0.5 | test mAP@0.5:0.95 | Δ test |"
    )
    lines = [header, "|---|---|---|---|---|---|---|---|---|"]
    prev = None
    for m in metrics:
        a = m.get("args", {})
        cur = m["test"]["map"]
        delta = "-" if prev is None else f"{(cur - prev) * 100:+.1f} pp"
        lines.append(
            f"| {m['name']} | {Path(str(a.get('model', '?'))).name} | {a.get('imgsz', '?')} "
            f"| {a.get('epochs', '?')} | {m['val']['map50']:.3f} | {m['val']['map']:.3f} "
            f"| {m['test']['map50']:.3f} | {cur:.3f} | {delta} |"
        )
        prev = cur
    return "\n".join(lines)


def _axes_style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(**GRID)
    ax.set_axisbelow(True)


def _eval_run(run_dir: Path, data_yaml: Path, device: str, report_dir: Path) -> dict:
    """對單一 run 跑 val + test 評估並快取成 metrics.json。"""
    mfile = run_dir / "metrics.json"
    best_pt = run_dir / "weights" / "best.pt"
    # 快取只在權重沒變過時有效（train exist_ok=True 會覆寫同名 run 的 best.pt）
    if mfile.exists() and mfile.stat().st_mtime > best_pt.stat().st_mtime:
        return json.loads(mfile.read_text())

    from ultralytics import YOLO

    model = YOLO(str(run_dir / "weights" / "best.pt"))
    out: dict = {"name": run_dir.name, "args": {}}
    args_file = run_dir / "args.yaml"
    if args_file.exists():
        args = yaml.safe_load(args_file.read_text())
        out["args"] = {k: args.get(k) for k in ("model", "imgsz", "epochs", "batch")}

    for split_name in ("val", "test"):
        m = model.val(
            data=str(data_yaml),
            split=split_name,
            device=device,
            project=str(report_dir / "eval"),
            name=f"{run_dir.name}-{split_name}",
            exist_ok=True,
            plots=True,
            verbose=False,
        )
        entry = {
            "map50": float(m.box.map50),
            "map": float(m.box.map),
            "precision": float(m.box.mp),
            "recall": float(m.box.mr),
            "per_class": {},
        }
        try:
            for i, idx in enumerate(m.box.ap_class_index):
                entry["per_class"][m.names[int(idx)]] = {
                    "ap50": float(m.box.ap50[i]),
                    "ap": float(m.box.ap[i]),
                }
        except Exception:
            pass  # per-class 拿不到不擋整份報告
        out[split_name] = entry

    mfile.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out


def _plot_training_curves(runs_metrics: list[dict], runs: Path, out: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for i, m in enumerate(runs_metrics):
        csv_path = runs / m["name"] / "results.csv"
        if not csv_path.exists():
            continue
        cols = parse_results_csv(csv_path)
        epochs = cols.get("epoch", [])
        maps = cols.get("metrics/mAP50-95(B)", [])
        losses = cols.get("train/box_loss", [])
        n1, n2 = min(len(epochs), len(maps)), min(len(epochs), len(losses))
        color = PALETTE[i % len(PALETTE)]
        ax1.plot(epochs[:n1], maps[:n1], color=color, linewidth=2)
        ax2.plot(epochs[:n2], losses[:n2], color=color, linewidth=2)
        if n1:
            ax1.annotate(
                m["name"],
                (epochs[n1 - 1], maps[n1 - 1]),
                textcoords="offset points",
                xytext=(4, 0),
                fontsize=9,
                color="#333333",
            )
    ax1.set_title("val mAP@0.5:0.95 per epoch")
    ax2.set_title("train box loss per epoch")
    for ax in (ax1, ax2):
        ax.set_xlabel("epoch")
        _axes_style(ax)
    fig.tight_layout()
    fig.savefig(out / "training_curves.png", dpi=120)
    plt.close(fig)


def _plot_ladder(runs_metrics: list[dict], out: Path) -> None:
    names = [m["name"] for m in runs_metrics]
    map50 = [m["test"]["map50"] for m in runs_metrics]
    map5095 = [m["test"]["map"] for m in runs_metrics]
    x = range(len(names))
    fig, ax = plt.subplots(figsize=(1.8 * max(len(names), 3) + 2, 4.5))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], map50, w, color=PALETTE[0], label="mAP@0.5")
    b2 = ax.bar([i + w / 2 for i in x], map5095, w, color=PALETTE[1], label="mAP@0.5:0.95")
    for bars in (b1, b2):
        ax.bar_label(bars, fmt="%.3f", fontsize=9, color="#333333")
    ax.set_xticks(list(x), names)
    ax.set_ylim(0, 1)
    ax.set_title("Optimization ladder (test set)")
    ax.legend(frameon=False)
    _axes_style(ax)
    fig.tight_layout()
    fig.savefig(out / "ladder.png", dpi=120)
    plt.close(fig)


def _plot_per_class(best: dict, out: Path) -> None:
    per_class = best["test"]["per_class"]
    if not per_class:
        return
    names = list(per_class)
    ap50 = [per_class[n]["ap50"] for n in names]
    ap = [per_class[n]["ap"] for n in names]
    x = range(len(names))
    fig, ax = plt.subplots(figsize=(1.2 * max(len(names), 4) + 2, 4.5))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], ap50, w, color=PALETTE[0], label="AP@0.5")
    b2 = ax.bar([i + w / 2 for i in x], ap, w, color=PALETTE[1], label="AP@0.5:0.95")
    for bars in (b1, b2):
        ax.bar_label(bars, fmt="%.2f", fontsize=8, color="#333333")
    ax.set_xticks(list(x), names, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_title(f"Per-class AP — {best['name']} (test set)")
    ax.legend(frameon=False)
    _axes_style(ax)
    fig.tight_layout()
    fig.savefig(out / "per_class_ap.png", dpi=120)
    plt.close(fig)


def _plot_dataset_stats(processed: Path, out: Path) -> None:
    labels_dir = processed / "labels" / "train"
    if not labels_dir.is_dir():
        return
    counter, areas = label_stats(labels_dir)
    names = yaml.safe_load((processed / "data.yaml").read_text())["names"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    cids = sorted(counter)
    ax1.bar(
        [str(names.get(c, c)) if isinstance(names, dict) else names[c] for c in cids],
        [counter[c] for c in cids],
        color=PALETTE[0],
    )
    ax1.set_title("Class instances (train split)")
    ax1.tick_params(axis="x", rotation=20)
    ax2.hist(areas, bins=40, color=PALETTE[0])
    ax2.set_title("BBox area ratio (w*h, train split)")
    ax2.set_xlabel("box area / image area")
    for ax in (ax1, ax2):
        _axes_style(ax)
    fig.tight_layout()
    fig.savefig(out / "dataset_stats.png", dpi=120)
    plt.close(fig)


def report(cfg: Config, root: Path) -> Path:
    """評估所有 run、畫圖、寫 report.md，回傳報告目錄。"""
    runs = root / cfg.paths.runs
    processed = root / cfg.paths.processed
    data_yaml = processed / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"找不到 {data_yaml}，請先跑 autocv split")
    run_dirs = discover_runs(runs, data_yaml)
    if not run_dirs:
        raise SystemExit(f"{runs} 下找不到這個資料集的 best.pt，請先跑 autocv train")

    out = runs / "report"
    out.mkdir(parents=True, exist_ok=True)
    device = pick_device(cfg.train.device)

    metrics = [_eval_run(d, data_yaml, device, out) for d in run_dirs]
    best = max(metrics, key=lambda m: m["test"]["map"])

    _plot_training_curves(metrics, runs, out)
    _plot_ladder(metrics, out)
    _plot_per_class(best, out)
    _plot_dataset_stats(processed, out)
    for fname in ("confusion_matrix_normalized.png", "BoxPR_curve.png"):
        src = out / "eval" / f"{best['name']}-test" / fname
        if src.exists():
            shutil.copy2(src, out / fname)

    def embed(fname: str, alt: str) -> str:
        return f"![{alt}]({fname})" if (out / fname).exists() else f"_（{fname} 未產出）_"

    per_class = best["test"]["per_class"]
    per_class_md = (
        "| class | AP@0.5 | AP@0.5:0.95 |\n|---|---|---|\n"
        + "\n".join(f"| {n} | {v['ap50']:.3f} | {v['ap']:.3f} |" for n, v in per_class.items())
        if per_class
        else "_（此 run 在 test set 上抓不到 per-class AP）_"
    )
    md = f"""# 訓練成績單（Optimization Ladder Report)

- 資料集：`{data_yaml}`
- 最佳 run：**{best['name']}**（test mAP@0.5:0.95 = {best['test']['map']:.3f}）

## 階梯表

{render_ladder_md(metrics)}

> 判讀：一次只動一個變因，Δ test 欄就是那個變因的功勞。
> 調參（conf/NMS）只能看 val 欄；test 欄只在最後報成績，不可回頭用它做決策。

## 訓練曲線

{embed("training_curves.png", "training_curves")}

## 階梯比較（test set）

{embed("ladder.png", "ladder")}

## Per-class AP — 找弱點

{per_class_md}

{embed("per_class_ap.png", "per_class_ap")}

> AP 最低的類別 = 下一步該補資料或加增強的地方。

## Confusion Matrix / PR Curve（最佳 run，test set）

{embed("confusion_matrix_normalized.png", "confusion_matrix")}

{embed("BoxPR_curve.png", "pr_curve")}

## 資料集健檢（train split）

{embed("dataset_stats.png", "dataset_stats")}

> 類別分佈嚴重不均或 bbox 面積集中在極小值，都會直接反映在 per-class AP 上。
"""
    (out / "report.md").write_text(md)
    print(f"report.md -> {out / 'report.md'}")
    for m in metrics:
        print(
            f"  {m['name']}: test mAP@0.5={m['test']['map50']:.3f} "
            f"mAP@0.5:0.95={m['test']['map']:.3f}"
        )
    return out
