from autocv.report import discover_runs, label_stats, parse_results_csv, render_ladder_md


def test_parse_results_csv(tmp_path):
    f = tmp_path / "results.csv"
    f.write_text(
        "epoch, train/box_loss, metrics/mAP50-95(B)\n"
        "1, 1.5, 0.10\n"
        "2, 1.2, 0.25\n"
    )
    cols = parse_results_csv(f)
    assert cols["epoch"] == [1.0, 2.0]
    assert cols["metrics/mAP50-95(B)"] == [0.10, 0.25]


def test_label_stats(tmp_path):
    (tmp_path / "a.txt").write_text("0 0.5 0.5 0.2 0.1\n1 0.5 0.5 0.5 0.5\n")
    (tmp_path / "b.txt").write_text("0 0.5 0.5 0.1 0.1\nbad line\n")
    counter, areas = label_stats(tmp_path)
    assert counter == {0: 2, 1: 1}
    assert len(areas) == 3
    assert abs(areas[0] - 0.02) < 1e-9


def test_discover_runs_sorted_by_mtime(tmp_path):
    import os

    for i, name in enumerate(["b-run", "a-run"]):
        w = tmp_path / name / "weights"
        w.mkdir(parents=True)
        pt = w / "best.pt"
        pt.write_bytes(b"x")
        os.utime(pt, (1000 + i, 1000 + i))
    (tmp_path / "no-weights").mkdir()
    assert [d.name for d in discover_runs(tmp_path)] == ["b-run", "a-run"]


def test_render_ladder_md_deltas():
    metrics = [
        {
            "name": "r0",
            "args": {"model": "yolov8n.pt", "imgsz": 640, "epochs": 60},
            "val": {"map50": 0.70, "map": 0.40},
            "test": {"map50": 0.72, "map": 0.41},
        },
        {
            "name": "r1",
            "args": {"model": "yolov8s.pt", "imgsz": 640, "epochs": 60},
            "val": {"map50": 0.75, "map": 0.45},
            "test": {"map50": 0.76, "map": 0.46},
        },
    ]
    md = render_ladder_md(metrics)
    assert "| r0 |" in md and "| r1 |" in md
    assert "+5.0 pp" in md
    assert md.count("|", 0, md.index("\n")) == 10  # 表頭 9 欄


def test_discover_runs_filters_other_datasets_and_tune(tmp_path):
    import yaml

    data_yaml = tmp_path / "proc" / "data.yaml"
    data_yaml.parent.mkdir()
    data_yaml.write_text("nc: 1\n")
    runs = tmp_path / "runs"
    for name, data in (
        ("aq-n-640", str(data_yaml)),
        ("wafer-run", str(tmp_path / "other" / "data.yaml")),
        ("tune", str(data_yaml)),
    ):
        w = runs / name / "weights"
        w.mkdir(parents=True)
        (w / "best.pt").write_bytes(b"x")
        (runs / name / "args.yaml").write_text(yaml.safe_dump({"data": data}))
    assert [d.name for d in discover_runs(runs, data_yaml)] == ["aq-n-640"]
    assert {d.name for d in discover_runs(runs)} == {"aq-n-640", "wafer-run"}


def test_label_stats_skips_unparseable_lines(tmp_path):
    (tmp_path / "a.txt").write_text("a 0.5 0.5 0.2 0.2\n0 0.5 0.5 0.1 0.1\n")
    counter, areas = label_stats(tmp_path)
    assert counter == {0: 1} and len(areas) == 1
