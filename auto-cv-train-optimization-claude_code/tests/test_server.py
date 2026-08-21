import time
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from autocv.cli import app as cli_app
from autocv.config import load_config
from autocv.server.app import create_app
from autocv.server.events import Event
from autocv.server.real_stages import build_stages
from autocv.server.runner import GATED, PipelineRunner, Stage


def test_event_to_dict_round_trips():
    e = Event(kind="stage", stage="train", payload={"status": "running"})
    assert e.to_dict() == {
        "kind": "stage",
        "stage": "train",
        "payload": {"status": "running"},
    }


def test_event_kinds_constant():
    from autocv.server.events import KINDS

    assert {"stage", "log", "metric", "await_confirm", "result", "done"} <= set(KINDS)


def _wait(r, timeout=2.0):
    deadline = time.time() + timeout
    while r.status not in ("done", "error") and time.time() < deadline:
        time.sleep(0.05)


def test_runner_runs_stages_in_order_and_emits_done():
    calls = []
    r = PipelineRunner(
        [
            Stage("data", lambda emit: calls.append("data")),
            Stage("split", lambda emit: calls.append("split")),
        ]
    )
    r.start()
    _wait(r)
    drained = list(r.events.queue)
    assert calls == ["data", "split"]
    triples = [(e.kind, e.stage, e.payload.get("status")) for e in drained]
    assert ("stage", "data", "running") in triples
    assert ("stage", "data", "done") in triples
    assert drained[-1].kind == "done" and drained[-1].payload["ok"] is True


def test_runner_gate_blocks_until_confirm():
    ran = []
    r = PipelineRunner(
        [Stage("train", lambda emit: ran.append("train"), estimate=lambda: 3.0)]
    )
    r.start()
    time.sleep(0.25)
    assert ran == []
    awaits = [e for e in list(r.events.queue) if e.kind == "await_confirm"]
    assert awaits and awaits[0].payload["estimate_min"] == 3.0
    r.confirm()
    _wait(r)
    assert ran == ["train"] and r.status == "done"


def test_runner_error_emits_error_event():
    def boom(emit):
        raise RuntimeError("x")

    r = PipelineRunner([Stage("data", boom)])
    r.start()
    _wait(r)
    assert r.status == "error"
    assert list(r.events.queue)[-1].payload["ok"] is False


def test_gated_constant():
    assert "train" in GATED and "optimize" in GATED


def test_csv_tail_emits_metric_events(tmp_path):
    from autocv.server.real_stages import _final_flush, _start_csv_tail

    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        "epoch,metrics/mAP50(B),metrics/mAP50-95(B),train/box_loss\n"
        "1,0.5,0.3,0.8\n"
        "2,0.7,0.4,0.6\n"
    )
    events: list = []
    stop, t, seen = _start_csv_tail(csv_path, events.append)
    time.sleep(1.3)
    stop.set()
    t.join(timeout=2)
    _final_flush(csv_path, events.append, seen)
    metrics = [e for e in events if e.kind == "metric"]
    assert len(metrics) >= 2
    assert metrics[0].payload["epoch"] == 1 and metrics[0].payload["map50"] == 0.5
    assert metrics[1].payload["epoch"] == 2 and metrics[1].payload["map50"] == 0.7


def test_build_real_stages_shape():
    cfg = load_config(Path("configs/wafer.yaml"))
    names = [s.name for s in build_stages(cfg, Path.cwd(), optimize=False)]
    assert names == ["data", "split", "train", "infer"]
    opt = [s.name for s in build_stages(cfg, Path.cwd(), optimize=True)]
    assert opt == ["data", "split", "optimize", "infer"]
    train = next(
        s for s in build_stages(cfg, Path.cwd(), optimize=False) if s.name == "train"
    )
    assert train.estimate is not None


def _fake_factory():
    def factory(config: str, optimize: bool):
        return PipelineRunner([Stage("data", lambda emit: None)])

    return factory


def _blocking_factory():
    # "train" 屬 GATED：runner 會卡在 _gate.wait()，未 confirm 前狀態恆為 running，
    # 用來確定性測 409（不靠 sleep / 時間競態）。
    def factory(config: str, optimize: bool):
        return PipelineRunner([Stage("train", lambda emit: None, estimate=lambda: 0.0)])

    return factory


def test_configs_endpoint_lists_yaml():
    c = TestClient(create_app(runner_factory=_fake_factory()))
    r = c.get("/configs")
    assert r.status_code == 200
    assert "configs/wafer.yaml" in r.json()["configs"]


def test_index_served():
    c = TestClient(create_app(runner_factory=_fake_factory()))
    r = c.get("/")
    assert r.status_code == 200
    assert 'id="stages"' in r.text and "cockpit" in r.text.lower()


def test_run_then_double_run_409():
    c = TestClient(create_app(runner_factory=_blocking_factory()))
    assert c.post("/run", json={"config": "configs/wafer.yaml"}).status_code == 200
    assert c.post("/run", json={"config": "configs/wafer.yaml"}).status_code == 409


def test_ws_streams_events():
    c = TestClient(create_app(runner_factory=_fake_factory()))
    c.post("/run", json={"config": "configs/wafer.yaml"})
    with c.websocket_connect("/ws") as ws:
        kinds = []
        for _ in range(10):
            msg = ws.receive_json()
            kinds.append(msg["kind"])
            if msg["kind"] == "done":
                break
    assert "done" in kinds


def test_cli_has_ui_command():
    r = CliRunner().invoke(cli_app, ["--help"])
    assert r.exit_code == 0 and "ui" in r.output
    r2 = CliRunner().invoke(cli_app, ["ui", "--help"])
    assert r2.exit_code == 0 and "--no-browser" in r2.output
