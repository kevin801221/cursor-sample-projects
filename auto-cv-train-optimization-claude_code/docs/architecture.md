# 架構

## Pipeline

```
configs/*.yaml ──┐
                 ▼
ROBOFLOW_API_KEY → data  → data/raw/
                            │
                            ▼
                 split → data/processed/{images,labels}/{train,val,test}/ + data.yaml
                            │
              ┌─────────────┴──────────────┐
              ▼                             ▼
           train                       optimize
      runs/train/weights/best.pt   runs/tune/ + best_hyperparameters.yaml
              └─────────────┬──────────────┘
                            ▼
                         infer → runs/infer/pred_*.png + summary.md
```

## 模組職責

| 模組 | 職責 |
|---|---|
| `config.py` | 載入+驗證 YAML |
| `device.py` | auto 挑 mps/cuda/cpu |
| `data.py` | Roboflow 下載 |
| `split.py` | 標註驗證 + 切分 + data.yaml |
| `train.py` | 單次訓練（GO-gate） |
| `optimize.py` | 超參搜尋 |
| `infer.py` | 推論 + 視覺化 + summary |
| `cli.py` | typer 指令路由 |

## 安全設計

`train` / `optimize` 預設先印預估時間並等 `typer.confirm`，`--yes` 才跳過。Claude Code agent 規定不可加 `--yes`，確保不會偷偷燒運算資源。
