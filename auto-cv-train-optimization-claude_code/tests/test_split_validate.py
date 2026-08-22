from autocv.split import validate_label_file


def test_valid_label(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.2 0.2\n1 0.1 0.1 0.05 0.05\n")
    errors, cids, n = validate_label_file(f)
    assert errors == []
    assert cids == [0, 1]
    assert n == 2


def test_missing_file(tmp_path):
    errors, cids, n = validate_label_file(tmp_path / "nope.txt")
    assert len(errors) == 1
    assert n == 0


def test_out_of_range_and_bad_fields(tmp_path):
    f = tmp_path / "b.txt"
    f.write_text("0 1.5 0.5 0.2 0.2\n0 0.5 0.5\n-1 0.5 0.5 0.2 0.2\n")
    errors, cids, n = validate_label_file(f)
    assert any("超出" in e for e in errors)
    assert any("欄位數" in e for e in errors)
    assert any("為負" in e for e in errors)


def test_split_merges_presplit_dirs(tmp_path, monkeypatch):
    import yaml as _yaml

    from autocv.config import Config
    from autocv.split import split as do_split

    raw = tmp_path / "data" / "raw"
    for sub, n in (("train", 6), ("valid", 3), ("test", 1)):
        (raw / sub / "images").mkdir(parents=True)
        (raw / sub / "labels").mkdir(parents=True)
        for i in range(n):
            (raw / sub / "images" / f"{sub}{i}.jpg").write_bytes(b"img")
            (raw / sub / "labels" / f"{sub}{i}.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (raw / "data.yaml").write_text(_yaml.safe_dump({"nc": 1, "names": ["defect"]}))

    cfg = Config.from_dict(
        {
            "roboflow": {"workspace": "w", "project": "p", "version": 1},
            "paths": {"raw": "data/raw", "processed": "data/processed"},
        }
    )
    do_split(cfg, tmp_path)
    processed = tmp_path / "data" / "processed"
    counts = {s: len(list((processed / "images" / s).iterdir())) for s in ("train", "val", "test")}
    assert sum(counts.values()) == 10  # 三個預切分目錄全數合併
    assert counts["train"] == 7 and counts["val"] == 2 and counts["test"] == 1


def test_split_prefixes_duplicate_names_and_cleans_stale(tmp_path):
    import yaml as _yaml

    from autocv.config import Config
    from autocv.split import split as do_split

    raw = tmp_path / "data" / "raw"
    for sub in ("train", "valid"):
        (raw / sub / "images").mkdir(parents=True)
        (raw / sub / "labels").mkdir(parents=True)
        for i in range(5):
            (raw / sub / "images" / f"{i}.jpg").write_bytes(sub.encode())
            (raw / sub / "labels" / f"{i}.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (raw / "data.yaml").write_text(_yaml.safe_dump({"nc": 1, "names": ["defect"]}))

    cfg = Config.from_dict(
        {
            "roboflow": {"workspace": "w", "project": "p", "version": 1},
            "paths": {"raw": "data/raw", "processed": "data/processed"},
        }
    )
    processed = tmp_path / "data" / "processed"
    stale = processed / "images" / "train" / "stale.jpg"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old")

    do_split(cfg, tmp_path)
    imgs = [p.name for s in ("train", "val", "test") for p in (processed / "images" / s).iterdir()]
    assert len(imgs) == 10  # 重名不互相覆蓋
    assert all(n.startswith(("train_", "valid_")) for n in imgs)  # 重名加來源前綴
    assert "stale.jpg" not in imgs  # 重跑會清掉舊分派
    lbls = [p.name for s in ("train", "val", "test") for p in (processed / "labels" / s).iterdir()]
    assert len(lbls) == 10 and all(n.startswith(("train_", "valid_")) for n in lbls)
