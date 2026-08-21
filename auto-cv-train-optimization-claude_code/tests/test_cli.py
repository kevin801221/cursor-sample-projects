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
