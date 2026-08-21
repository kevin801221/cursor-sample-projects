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

    @app.websocket("/ws")
    async def ws(sock: WebSocket) -> None:
        await sock.accept()
        try:
            while True:
                r = state["runner"]
                if r is None:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    ev = r.events.get_nowait()
                except Exception:
                    await asyncio.sleep(0.05)
                    continue
                await sock.send_json(ev.to_dict())
                if ev.kind == "done":
                    break
        except WebSocketDisconnect:
            return

    if STATIC.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    @app.get("/artifacts/{name}")
    def artifact(name: str):
        p = Path.cwd() / "runs" / "infer" / name
        if not p.is_file():
            return HTMLResponse("not found", status_code=404)
        return FileResponse(str(p))

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        f = STATIC / "index.html"
        return HTMLResponse(f.read_text() if f.is_file() else "<h1>cockpit</h1>")

    return app
