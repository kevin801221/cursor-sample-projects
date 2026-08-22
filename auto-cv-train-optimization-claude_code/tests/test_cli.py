from typer.testing import CliRunner

from autocv.cli import app

runner = CliRunner()


def test_help():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for cmd in ("data", "split", "train", "optimize", "infer", "all"):
        assert cmd in r.output


def test_version():
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert "autocv" in r.output


def test_train_dedup_skips_when_best_exists(tmp_path):
    from autocv.config import Config
    from autocv.train import train as do_train

    cfg = Config.from_dict(
        {
            "roboflow": {"workspace": "w", "project": "p", "version": 1},
            "train": {"name": "aq-n-640"},
        }
    )
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "processed" / "data.yaml").write_text("nc: 1\n")
    best = tmp_path / "runs" / "aq-n-640" / "weights" / "best.pt"
    best.parent.mkdir(parents=True)
    best.write_bytes(b"weights")

    # 已有權重：不 import ultralytics、不問確認，直接回傳既有 best.pt
    assert do_train(cfg, tmp_path) == best
