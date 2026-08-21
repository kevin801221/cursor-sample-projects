# Roadmap

開發中與規劃中的功能。歡迎 PR / issue 認領。
What's in flight and what's planned. PRs and issues welcome.

## ✅ Shipped

- 五階段 CLI（data / split / train / optimize / infer + `all`）
- `autocv ui` 視覺駕駛艙（FastAPI + 零建置單頁前端）
- GO-gate：train / optimize 預估時間 + server 端 `threading.Event` 物理阻塞
- 訓練曲線即時 tail `results.csv`
- 5 個 Claude Code agent（config 驅動）
- 中英雙語 README + 內建 wafer showcase（mAP@0.5 = 0.9950）
- GitHub Actions CI（ruff + pytest）

## 🛠 Next — Cockpit UX 強化

- [ ] `GET /status` 暴露 pending_confirm；前端 reconnect / refresh 自動復原 modal
- [ ] gated stage 旁加 inline confirm 按鈕，當 modal 渲染失敗的備援
- [ ] 「Abort」按鈕：跑到一半中止整條 pipeline（含正確清理 thread）
- [ ] 訓練曲線同時繪 train/box_loss + val/box_loss，雙線對照
- [ ] log 區加搜尋 / 過濾、可下載成檔
- [ ] 多執行歷史頁：列出 `runs/` 下所有過往 run，點進看 metrics + 成果圖

## 📦 Next — 訓練能力擴充

- [ ] 自動 augmentation pipeline（整合 albumentations，augment 設定也走 config）
- [ ] 模型一鍵匯出：CoreML / ONNX / TensorRT，UI 上一個按鈕
- [ ] benchmark：對同一 test set 跑多個模型版本對比表
- [ ] 多框架支援抽象層：YOLOv8 → YOLOv9 / YOLOv10 / RT-DETR
- [ ] 跨資料集 transfer：base model + new dataset fine-tune flow

## ☁️ Later — 雲端與多人

- [ ] 雲端訓練 backend：本機跑不動時把 job 丟 Modal / Runpod，回來拿模型
- [ ] 多資料集競技場：同時跑 N 個 config 設定，自動排名選最強
- [ ] 一鍵分享單次 run（產生靜態 HTML 報告 + 成果圖 + metric）

## 🧪 Engineering / Hygiene

- [ ] `results.csv` tail 整合測試（用假 YOLO writer 模擬寫入）
- [ ] cockpit E2E 測試（Playwright + 注入假 stage 函式）
- [ ] runner / app coverage 提升到 90%
- [ ] CI 加 macOS runner 跑 MPS smoke（無真實訓練）
- [ ] 多 Python 版本矩陣（3.11 / 3.12）

## 📝 Docs

- [ ] CONTRIBUTING.md
- [ ] BYO dataset 詳細教學（含非 Roboflow 來源接法）
- [ ] cockpit 架構圖（pipeline 接力如何映射到 WebSocket 事件流）
- [ ] FAQ：常見訓練問題、MPS / CUDA 切換

---

想做哪條？開 issue 標 `roadmap:<section>` 認領。
Want to pick one up? Open an issue tagged `roadmap:<section>`.
