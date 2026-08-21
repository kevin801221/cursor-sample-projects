# Wafer Showcase

內建範例：半導體晶圓圖瑕疵偵測（WM-811K，YOLOv8n，Mac MPS）。

## 重現

```bash
cp .env.example .env   # 填入 ROBOFLOW_API_KEY
uv run autocv all -c configs/wafer.yaml --yes
```

## 已達成績（見 docs/results/）

| 指標 | 數值 |
|---|---|
| mAP@0.5 | 0.9913 |
| mAP@0.5:0.95 | 0.7633 |
| Precision | 0.9331 |
| Recall | 0.9968 |

成果視覺化見 [`docs/results/summary.md`](../../docs/results/summary.md)。
