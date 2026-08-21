"""autocv CLI：data / split / train / optimize / infer / all。"""

from __future__ import annotations

from pathlib import Path

import typer

from autocv import __version__
from autocv.config import load_config

app = typer.Typer(
    add_completion=False,
    help="改一個 YAML，一行指令跑完整 CV pipeline：data→split→train→optimize→infer。",
)

ConfigOpt = typer.Option("configs/wafer.yaml", "-c", "--config", help="config.yaml 路徑")
YesOpt = typer.Option(False, "--yes", "-y", help="跳過訓練前確認")


def _ctx(config: str) -> tuple:
    root = Path.cwd()
    return load_config(config), root


@app.command()
def version() -> None:
    """印出版本。"""
    typer.echo(f"autocv {__version__}")


@app.command()
def data(config: str = ConfigOpt) -> None:
    """從 Roboflow 下載資料集。"""
    from autocv.data import download

    cfg, root = _ctx(config)
    download(cfg, root)


@app.command()
def split(config: str = ConfigOpt) -> None:
    """驗證標註並切分 train/val/test。"""
    from autocv.split import split as do_split

    cfg, root = _ctx(config)
    do_split(cfg, root)


@app.command()
def train(config: str = ConfigOpt, yes: bool = YesOpt) -> None:
    """訓練 YOLOv8 模型。"""
    from autocv.train import train as do_train

    cfg, root = _ctx(config)
    do_train(cfg, root, yes=yes)


@app.command()
def optimize(config: str = ConfigOpt, yes: bool = YesOpt) -> None:
    """超參搜尋（很耗時）。"""
    from autocv.optimize import optimize as do_opt

    cfg, root = _ctx(config)
    do_opt(cfg, root, yes=yes)


@app.command()
def infer(config: str = ConfigOpt) -> None:
    """推論並產出視覺化 + summary。"""
    from autocv.infer import infer as do_infer

    cfg, root = _ctx(config)
    do_infer(cfg, root)


@app.command()
def all(
    config: str = ConfigOpt,
    yes: bool = YesOpt,
    optimize_step: bool = typer.Option(
        False, "--optimize", help="用 optimize 取代 train"
    ),
) -> None:
    """一條龍：data→split→(train|optimize)→infer。"""
    from autocv.data import download
    from autocv.infer import infer as do_infer
    from autocv.optimize import optimize as do_opt
    from autocv.split import split as do_split
    from autocv.train import train as do_train

    cfg, root = _ctx(config)
    download(cfg, root)
    do_split(cfg, root)
    if optimize_step:
        do_opt(cfg, root, yes=yes)
    else:
        do_train(cfg, root, yes=yes)
    do_infer(cfg, root)


@app.command()
def ui(
    config: str = ConfigOpt,
    host: str = typer.Option("127.0.0.1", help="綁定 host"),
    port: int = typer.Option(8787, help="綁定 port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="不自動開瀏覽器"),
) -> None:
    """開本機視覺駕駛艙（瀏覽器）。"""
    import uvicorn

    from autocv.server.app import create_app

    if not no_browser:
        import threading
        import webbrowser

        threading.Timer(1.2, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    typer.echo(f"cockpit -> http://{host}:{port}（Ctrl+C 結束）")
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")


if __name__ == "__main__":
    app()
