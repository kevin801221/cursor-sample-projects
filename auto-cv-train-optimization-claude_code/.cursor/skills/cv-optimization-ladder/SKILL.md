---
name: cv-optimization-ladder
description: 規劃或執行 YOLO 模型優化實驗時使用的科學階梯方法論。當使用者要「提升 mAP」「調參」「加開下一階實驗」「比較兩個 run」「決定要不要繼續優化」，或要新增 configs/*.yaml 跑新一輪訓練時載入。
---

# CV 優化階梯（Scientific Optimization Ladder）

核心原則：**一次只動一個變因**。同時改解析度＋模型尺寸＋epochs，漲了不知道是誰的功勞，跌了不知道是誰的鍋——無法歸因的實驗等於沒做。

貫穿範例：aquarium（brad-dwyer/aquarium-combined v6，7 類、638 張、類別不平衡）。

## 每一階的固定流程

1. 複製上一階的 config 檔，只改**一個**變因（`train` 區塊的 `model` / `imgsz` / `epochs` 其中之一，或改跑 `optimize`）
2. 給唯一的 `train.name`，命名編碼變因：`aq-n-640` → `aq-s-640` → `aq-s-800`
3. 跑訓練：`uv run autocv train -c configs/<name>.yaml`（加 `--yes` 跳過確認）
4. 跑完立刻 `uv run autocv report -c configs/<name>.yaml`，看 Δ test 欄歸因這一階的漲跌
5. 把結論（含 negative result）記下來再開下一階

## 階梯順序：先便宜後貴

| 階 | 動什麼 | 成本 | 何時做 |
|---|---|---|---|
| R0 | 基準線（預設值先跑起來） | 低 | 永遠第一步 |
| R+ | `imgsz`（如 640→800）、`epochs` | 中 | 小物件多、loss 還在降 |
| R+ | `model`（yolov8n.pt→yolov8s.pt→…） | 中高 | 便宜招數收斂後 |
| 最後 | `uv run autocv optimize -c configs/<name>.yaml` | 最貴 | 前面都收斂才做 |

aquarium 實際階梯（三個 config 都在 repo 裡，可直接對照）：

- `configs/aquarium.yaml`：R0 基準線，`model: yolov8n.pt`、`imgsz: 640`、`epochs: 60`、`name: aq-n-640`
- `configs/aquarium-s.yaml`：R1 只動模型 n→s，`name: aq-s-640`，其餘與 R0 相同
- `configs/aquarium-s800.yaml`：R2 只動解析度 640→800，`name: aq-s-800`

## 檢查清單：開新一階之前

- [ ] 新 config 與上一階 diff 後，`train` 區塊只有一個欄位不同（`name` 不算變因）
- [ ] `train.name` 唯一且沒用過（重名會蓋掉 `runs/` 下的舊結果）
- [ ] `roboflow`、`paths`、`dataset`（含 `split` 與 `seed`）與上一階完全相同——資料變了就不是同一個實驗
- [ ] config 開頭一行註解寫明「這一階動了什麼」（照 repo 現有三個 aquarium config 的寫法）
- [ ] 例外：`imgsz` 調大導致 OOM 時允許順帶降 `batch`（如 aquarium-s800 的 16→8），但必須在註解註明「純為記憶體安全」，且解讀結果時記得 batch 也變了

## 檢查清單：每一階跑完之後

- [ ] 跑了 `uv run autocv report -c configs/<name>.yaml`，確認新 run 出現在 report.md 裡
- [ ] 看 Δ test 欄：這一階相對上一階漲跌多少
- [ ] 漲跌能歸因到唯一變因（因為 diff 只有一個欄位）
- [ ] Negative result 也記錄：「imgsz 800 沒漲」本身就是有價值的結論，能省下之後所有人重跑一次的成本
- [ ] 不要在文件裡寫死數字結論，一律引用 report 輸出

## 決策規則：何時停

以下任一成立就停止加階：

- 連續兩階 test mAP 漲幅 < 1 pp
- 模型成本（推論延遲 / 模型大小）已超出部署需求——mAP 再高也沒用
- 只剩超參搜尋沒做：先確認前面的階都收斂，`optimize` 是最後一招（`optimize.iterations` 次試驗、每次 `optimize.epochs` epochs，很耗時）

## 決策規則：val 與 test 的分工

- 調參類決策（conf/NMS、挑超參、挑 epoch）**只看 val 欄**——report.md 的階梯表也如此標注，此規則所有 cv-* skill 通用
- 階梯歸因看 **Δ test**（階梯表相鄰 run 的 test mAP@0.5:0.95 差），但不可回頭用 test 反覆微調同一變因——test 是成績單，不是調參工具
- `dataset.split: [0.7, 0.2, 0.1]` 與 `seed: 42` 全程鎖死，任何一階都不准動

## 常用指令速查

```bash
uv run autocv data     -c configs/aquarium.yaml   # 下載資料（各階共用，只需跑一次）
uv run autocv split    -c configs/aquarium.yaml   # 驗證標註並切分（同上）
uv run autocv train    -c configs/aquarium-s.yaml --yes
uv run autocv report   -c configs/aquarium-s.yaml # 跨 run 比較 + report.md
uv run autocv optimize -c configs/aquarium.yaml --yes  # 最後一階才用
uv run autocv all      -c configs/aquarium.yaml --yes  # 一條龍 data→split→train→infer→report
```
