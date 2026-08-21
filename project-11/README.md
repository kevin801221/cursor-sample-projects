# Rooftop Dash — Phaser 3 網頁遊戲

> Cursor 課程 Project 11（第 32 章）：Phaser 3 + Vite。
> 一句話：**從一頁 GDD 開始，用結構化 prompt 與一檔一職責讓 AI 疊代出一個能玩的平台跳躍遊戲**——不要讓 Agent 自由發揮，邊界越清楚改動越準確。

## 專案規格

| | |
|---|---|
| **最終成果** | 含控制、地圖、敵人、關卡、音效、暫停的網頁遊戲 |
| **技術棧** | Vite 5+、Phaser 3.80+、Vanilla JavaScript ES Module |
| **預估時間** | 8–12 小時，分多個迭代階段，建議每次迭代只做一個功能 |
| **前置需求** | 基礎 JavaScript 語法、已安裝 Node.js 18+ |

## 這個遊戲做什麼

- 角色在屋頂平台上跳躍、躲避敵人、收集金幣
- 按方向鍵移動、按空格跳躍；按 P 暫停、按 R 重新開始
- 敵人在平台上巡邏，碰撞會扣命
- 收集完當前關卡金幣才能打開出口門進下一關
- 完整的聲音反饋與視覺效果

## 場景架構（文字版）

```
Rooftop Dash
├── MenuScene              遊戲主菜單
├── PlayScene              玩家遊戲進行的場景
│   ├── Player            可控角色（位置、速度、跳躍狀態）
│   ├── Platforms         靜態平台群（碰撞體、視覺層）
│   ├── Enemies           敵人（巡邏、傷害檢測）
│   ├── Collectibles      金幣（收集計數）
│   ├── ExitDoor          出口門（需收集完金幣才開啟）
│   ├── Camera            跟隨玩家視角
│   └── Audio             背景音樂、特效音
└── GameOverScene         遊戲結束（顯示分數、按 R 重來）
```

## 開發階段表

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 0. GDD 與骨架 | 寫一頁 GDD、建 Vite 專案、裝 Phaser、建立三個空場景 | Vite 能啟動，場景能切換 |
| 1. 核心玩法 | 玩家移動、跳躍、重力、碰撞檢測 | 能跑、能跳、不穿過平台 |
| 2. 敵人與傷害 | 敵人巡邏、碰撞判定、命數系統 | 碰敵人扣命、命數為零進 Game Over |
| 3. 收集與通關 | 金幣收集、出口門機制、關卡切換 | 收集完金幣打開門，進下一關 |
| 4. 視覺與音效 | UI、動畫、音樂、暫停功能 | 完整視覺反饋、暫停能停止一切 |
| 5. 調整與打磨 | 手感調整、邊界情況修復 | 全部動手練習完成 |

## 專案結構

```
rooftop-dash/
├── .cursor/rules/
│   ├── 00-architecture.mdc    # 一檔一職責 + 常數置頂 alwaysApply
│   ├── phaser.mdc             # Phaser 慣例（globs 按需載入）
│   └── prompt-template.mdc    # 八欄位模板參考
├── src/
│   ├── main.js                # 唯一的 Phaser Game 實例
│   ├── constants.js           # 所有數值集中（速度、重力、敵人 HP 等）
│   ├── scenes/
│   │   ├── MenuScene.js       # 主菜單
│   │   ├── PlayScene.js       # 遊戲主場景
│   │   └── GameOverScene.js   # 遊戲結束
│   ├── input.js               # 鍵盤/滑鼠輸入（不與邏輯混雜）
│   ├── prefabs/               # 可重用物件類（Player、Enemy、Platform）
│   │   ├── Player.js
│   │   ├── Enemy.js
│   │   └── Collectible.js
│   └── assets/                # 圖片、音效、字型
├── vite.config.js             # Vite 設定（注意 base 路徑）
├── index.html
└── walkthrough.md             # 完整逐步教學
```

## 三條鐵律（本課核心）

1. **結構化 prompt 八欄位模板讓指令清晰**——Goal、Must ship、Tech & limits、Do NOT、Done when 等欄位寫得具體，Agent 才不會超出範圍亂加功能；避免「加個血條」最後變成「加血條、動畫、數值平衡」。

2. **一檔一職責 + 常數置頂**——input.js 只管輸入、constants.js 只放可調數值、每個場景各自一檔；禁止在場景檔寫死數值，Agent 改手感時才不會誤動到碰撞或其他邏輯。

3. **沉默故障不會報錯，必須靠實際遊玩發現**——高速跳躍穿過平台、分數沒存進 registry、敵人沒正確檢測碰撞，都是能跑沒報錯的邏輯錯；每個迭代完都要親自玩一遍，尤其是邊界情況（快速移動、連續碰撞、關卡邊界）。

## 快速開始

```bash
npm install
npm run dev                     # http://localhost:5173
npm run build                   # 打包部署（記得檢查 vite.config.js 的 base）

# 開發時，對 Cursor Agent 說：
# "用結構化 prompt 八欄位模板讓我加入 [功能名稱]"
# 模板見 walkthrough.md § 5
```

完整建置步驟、GDD 怎麼寫、八欄位模板實例、四大坑詳解、三個動手練習，見 **[walkthrough.md](./walkthrough.md)**。

---

**常見坑速查**：見 walkthrough.md § 8。
**本章小結**：見 walkthrough.md § 9。
