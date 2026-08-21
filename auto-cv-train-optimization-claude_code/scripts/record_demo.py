#!/usr/bin/env python3
"""自動錄 cockpit 跑一輪 pipeline 並輸出 docs/screenshots/cockpit-demo.gif。

流程：
1. 確保 wafer-quick.yaml 存在（5 epochs 短訓）
2. 清舊 runs/，stage 燈、曲線、gallery 從空開始
3. 起 cockpit on :8788（不撞使用者已有 server）
4. Playwright 驅 Chromium：選 config → Run → 等 modal → 按確認 → 等 5 階段跑完
5. ffmpeg 把錄到的 webm 轉 GIF（1.5x 加速、960 寬、12 fps、palette 提升畫質）

需求：
  - ffmpeg：`brew install ffmpeg`
  - Playwright + Chromium：`uvx playwright install chromium`
  - .env 含 ROBOFLOW_API_KEY

執行：
  uv run --with playwright python scripts/record_demo.py
"""

from __future__ import annotations

import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
CONFIG_BASE = ROOT / "configs" / "wafer.yaml"
CONFIG_QUICK = ROOT / "configs" / "wafer-quick.yaml"
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_GIF = OUT_DIR / "cockpit-demo.gif"
TMP_DIR = OUT_DIR / "_tmp_video"
HOST = "127.0.0.1"
PORT = 8788
URL = f"http://{HOST}:{PORT}"

# GIF 參數
GIF_WIDTH = 960
GIF_FPS = 12
SPEED = 1.5  # 1.5x 加速：訊息看得到、節奏夠快


def step(msg: str) -> None:
    print(f"\n▶ {msg}", flush=True)


def preflight() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("❌ 缺 ffmpeg：brew install ffmpeg")
    if not (ROOT / ".env").exists():
        sys.exit("❌ 缺 .env（需 ROBOFLOW_API_KEY）")
    if not CONFIG_BASE.exists():
        sys.exit("❌ 缺 configs/wafer.yaml")
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        sys.exit(
            "❌ 缺 Playwright。請用：\n"
            "   uv run --with playwright python scripts/record_demo.py\n"
            "首次也要：uvx playwright install chromium"
        )


def ensure_quick_config() -> None:
    if CONFIG_QUICK.exists():
        return
    step("建立 wafer-quick.yaml（5 epochs）")
    CONFIG_QUICK.write_text(CONFIG_BASE.read_text().replace("epochs: 50", "epochs: 5"))


def cleanup_runs() -> None:
    step("清舊 runs/")
    if RUNS.exists():
        shutil.rmtree(RUNS)


def start_cockpit() -> subprocess.Popen:
    step(f"啟動 cockpit on {URL}")
    p = subprocess.Popen(
        [
            "uv", "run", "autocv", "ui",
            "--no-browser", "--host", HOST, "--port", str(PORT),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/configs", timeout=1)
            return p
        except Exception:
            time.sleep(0.3)
    p.terminate()
    sys.exit("❌ cockpit 起不來")


def record_pipeline() -> Path:
    step("Playwright 開瀏覽器跑 pipeline + 錄影")
    from playwright.sync_api import sync_playwright

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(TMP_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        page.goto(URL)
        page.wait_for_function(
            "document.querySelectorAll('#cfg option').length > 0", timeout=10_000
        )
        # 選快速 config
        page.select_option("#cfg", "configs/wafer-quick.yaml")
        time.sleep(0.6)
        page.click("#run")

        # 等 modal（GO-gate）出現；超時就 curl 救
        try:
            page.wait_for_selector(".modal.on", timeout=180_000)
            time.sleep(2.0)  # 停留讓畫面看到 modal
            page.click("#go")
        except Exception:
            urllib.request.urlopen(f"{URL}/confirm", data=b"", timeout=5)

        # 等 4 個非 optimize 的 stage 都 done（data/split/train/infer）
        page.wait_for_function(
            "document.querySelectorAll('.st.done').length >= 4", timeout=300_000
        )
        time.sleep(3.5)  # 停留秀完整最終畫面

        video = page.video.path()
        page.close()
        ctx.close()
        browser.close()
    return Path(video)


def webm_to_gif(video: Path) -> None:
    step(f"轉 GIF（{SPEED}x、{GIF_WIDTH}px、{GIF_FPS} fps、palette 提升畫質）")
    palette = TMP_DIR / "palette.png"
    vf_common = (
        f"setpts=PTS/{SPEED},fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video),
            "-vf", f"{vf_common},palettegen=stats_mode=diff",
            str(palette),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video), "-i", str(palette),
            "-filter_complex",
            f"{vf_common}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
            str(OUT_GIF),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cleanup_tmp() -> None:
    step("清暫存")
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR, ignore_errors=True)


def kill_cockpit(p: subprocess.Popen) -> None:
    step("關掉 cockpit server")
    p.send_signal(signal.SIGTERM)
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()


def main() -> None:
    preflight()
    ensure_quick_config()
    cleanup_runs()
    server = start_cockpit()
    video = None
    try:
        video = record_pipeline()
        webm_to_gif(video)
    finally:
        kill_cockpit(server)
        cleanup_tmp()
    if OUT_GIF.exists():
        size_mb = OUT_GIF.stat().st_size / 1024 / 1024
        print(f"\n✅ {OUT_GIF.relative_to(ROOT)}  ({size_mb:.1f} MB)")
    else:
        sys.exit("❌ GIF 沒生出來，看上面錯誤訊息")


if __name__ == "__main__":
    main()
