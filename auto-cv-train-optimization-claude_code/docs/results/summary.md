# Inference Summary — Wafer Showcase

- 範例：半導體晶圓圖瑕疵偵測（WM-811K）
- 模型：YOLOv8n（`runs/train/weights/best.pt`）
- Test set：42 張
- 裝置：Mac MPS

## Metrics (test split)

- **mAP@0.5**: 0.9913
- **mAP@0.5:0.95**: 0.7633
- **Precision**: 0.9331
- **Recall**: 0.9968

## 視覺化樣本（10 張）

![pred_7934_png.rf.3615919c694efba5d3a03b6f85a76e55](pred_7934_png.rf.3615919c694efba5d3a03b6f85a76e55.png)

![pred_278940_png.rf.e311df676cb47c29d6a49e6a4257cc39](pred_278940_png.rf.e311df676cb47c29d6a49e6a4257cc39.png)

![pred_11813_png.rf.9734b1e9350c30c532ee558aa08ee480](pred_11813_png.rf.9734b1e9350c30c532ee558aa08ee480.png)

![pred_279311_png.rf.f31ed253dbc58004433bdc05fd8cdad7](pred_279311_png.rf.f31ed253dbc58004433bdc05fd8cdad7.png)

![pred_279273_png.rf.43bc2c9c2694e8340eb3e44a96a924bb](pred_279273_png.rf.43bc2c9c2694e8340eb3e44a96a924bb.png)

![pred_279270_png.rf.1f4bb96be24171e112637c55480d5444](pred_279270_png.rf.1f4bb96be24171e112637c55480d5444.png)

![pred_278966_png.rf.0140615b2a6328071077f672e80aba64](pred_278966_png.rf.0140615b2a6328071077f672e80aba64.png)

![pred_278757_png.rf.2277f2b34ff792198cf29a3657b8fd1a](pred_278757_png.rf.2277f2b34ff792198cf29a3657b8fd1a.png)

![pred_278750_png.rf.13e5f4fa6fb3e41cc2c94ec6317e417c](pred_278750_png.rf.13e5f4fa6fb3e41cc2c94ec6317e417c.png)

![pred_391177_png.rf.4ca7532ac02a54022eb9d7ba87e9db20](pred_391177_png.rf.4ca7532ac02a54022eb9d7ba87e9db20.png)

## 觀察筆記

- 紅色矩形為模型預測 bbox，左上角顯示 class name 與 confidence。
- 標題顯示 `No prediction` 的圖代表模型在 conf=0.25 門檻下未輸出框。
- 若有大量漏偵測或低 confidence，可調整 config 的 `infer.conf` 門檻或重新訓練。
