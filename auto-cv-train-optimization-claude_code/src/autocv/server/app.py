"""FastAPI：列 config / 啟動 / 確認 GO-gate / WebSocket 事件流 / 靜態。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from autocv.server.runner import PipelineRunner

STATIC = Path(__file__).parent / "static"


def _default_factory(config: str, optimize: bool) -> PipelineRunner:
    from autocv.config import load_config
    from autocv.server.real_stages import build_stages

    root = Path.cwd()
    cfg = load_config(config)
    return PipelineRunner(build_stages(cfg, root, optimize=optimize))


def create_app(
    runner_factory: Optional[Callable[[str, bool], PipelineRunner]] = None,
) -> FastAPI:
    factory = runner_factory or _default_factory
    app = FastAPI(title="autocv cockpit")
    state: dict = {"runner": None}

    @app.get("/configs")
    def configs() -> JSONResponse:
        files = sorted(str(p) for p in Path("configs").glob("*.yaml"))
        return JSONResponse({"configs": files})

    @app.post("/run")
    def run(body: dict) -> JSONResponse:
        r = state["runner"]
        if r is not None and r.status == "running":
            return JSONResponse({"error": "已有 pipeline 在跑"}, status_code=409)
        runner = factory(
            body.get("config", "configs/wafer.yaml"),
            bool(body.get("optimize", False)),
        )
        state["runner"] = runner
        runner.start()
        return JSONResponse({"status": "running"})

    @app.post("/confirm")
    def confirm() -> JSONResponse:
        r = state["runner"]
        if r is None:
            return JSONResponse({"error": "尚未啟動"}, status_code=400)
        r.confirm()
        return JSONResponse({"status": "confirmed"})

    @app.get("/status")
    def status() -> JSONResponse:
        r = state["runner"]
        if r is None:
            return JSONResponse({"status": "idle", "events": []})
        return JSONResponse({
            "status": r.status,
            "current_stage": r.current_stage,
            "events": [e.to_dict() for e in r.history[-150:]],
        })

    @app.websocket("/ws")
    async def ws(sock: WebSocket) -> None:
        await sock.accept()
        r = state["runner"]
        listener_q = None
        if r is not None:
            # 重播歷史事件給新連線的用戶端
            for ev in r.history:
                try:
                    await sock.send_json(ev.to_dict())
                except Exception:
                    break
            listener_q = r.add_listener()

        try:
            while True:
                curr_runner = state["runner"]
                if curr_runner is None:
                    await asyncio.sleep(0.2)
                    continue

                if listener_q is None or curr_runner != r:
                    r = curr_runner
                    listener_q = r.add_listener()

                try:
                    ev = listener_q.get_nowait()
                    await sock.send_json(ev.to_dict())
                    if ev.kind == "done":
                        await asyncio.sleep(0.5)
                except Exception:
                    await asyncio.sleep(0.05)
        except WebSocketDisconnect:
            pass
        finally:
            if r is not None and listener_q is not None:
                r.remove_listener(listener_q)

    if STATIC.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    @app.get("/artifacts/{name}")
    def artifact(name: str):
        # 優先找 runs/infer，若無則找 docs/results
        p = Path.cwd() / "runs" / "infer" / name
        if not p.is_file():
            p = Path.cwd() / "docs" / "results" / name
        if not p.is_file():
            # 也支援 runs/aq-n-640/ 下的圖表
            for run_p in Path.cwd().glob(f"runs/*/{name}"):
                if run_p.is_file():
                    p = run_p
                    break
        if not p.is_file():
            return HTMLResponse("not found", status_code=404)
        return FileResponse(str(p))

    @app.get("/showcase")
    def showcase() -> JSONResponse:
        results_dir = Path.cwd() / "docs" / "results"
        imgs = sorted(p.name for p in results_dir.glob("pred_*.png"))
        return JSONResponse({
            "dataset": "Wafer (WM-811K)",
            "model": "YOLOv8n (MPS/CUDA)",
            "map50": 0.9913,
            "map50_95": 0.7633,
            "precision": 0.9331,
            "recall": 0.9968,
            "images": [f"/artifacts/{name}" for name in imgs]
        })

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        f = STATIC / "index.html"
        return HTMLResponse(f.read_text() if f.is_file() else "<h1>cockpit</h1>")

    return app
