# scripts/

開發者工具，不在套件 import path 上。

## record_demo.py — 錄 cockpit GIF

自動跑一輪 wafer pipeline 並輸出 `docs/screenshots/cockpit-demo.gif`。

### 前置
```bash
brew install ffmpeg
uvx playwright install chromium       # 一次性下載 Chromium
cp .env.example .env && vi .env       # 填 ROBOFLOW_API_KEY
```

### 執行
```bash
uv run --with playwright python scripts/record_demo.py
```

約 2 分鐘（含 ~30s 下載資料、~30s 訓 5 epochs、~10s 推論 + 影片轉檔）。
產出單檔：`docs/screenshots/cockpit-demo.gif`（~3-6 MB，適合 README hero 嵌入）。

### 微調

| 想要 | 改 `scripts/record_demo.py` |
|---|---|
| GIF 更小 | `GIF_WIDTH = 720` 或 `GIF_FPS = 10` |
| 播放更快 | `SPEED = 2.0` |
| 訓更多 epoch 讓曲線更漂亮 | 改 `configs/wafer-quick.yaml` 的 `epochs:` |
