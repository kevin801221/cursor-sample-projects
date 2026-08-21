# Subagent + Hooks 實戰 — 用確定性護欄與專業分工交付生產級 API

> Cursor 核心機制實戰篇：Subagent + Hooks。
> 一句話：**Subagent 決定「誰來做這件事」，Hook 決定「什麼一定會發生、什麼絕對不准發生」**——兩者協同，Agent 產出的程式碼才能真正安全進 Production。

---

## 專案規格

| | |
|---|---|
| **最終成果** | 為 Node/TypeScript API 專案安全新增「使用者自助刪除帳號（`DELETE /api/account`）」功能，完整走過規劃（Planner）、稽核（Security Auditor）、驗證（Verifier）與 5 大自動化 Hooks 護欄 |
| **技術棧** | TypeScript、Node.js 20+、Cursor Subagents、Cursor Hooks（POSIX Shell / jq） |
| **預估時間** | 45–60 分鐘 |
| **前置需求** | Cursor 2.4+、Node 20+、jq（`brew install jq`） |

---

## 0. 先建立心智模型

新手最常見的誤解是「Subagent 和 Hooks 都是拿來擴充 Cursor 的，二選一就好」。不是。它們解決的是兩種完全不同的問題：

| 維度 | Subagent（次代理人） | Hook（鉤子程式） |
|---|---|---|
| **本質** | 另一個 LLM 實例 | 一個被 spawn 的確定性程序（bash / python / node） |
| **行為** | 機率性 —— 你用 prompt 拜託它 | 確定性 —— 它**一定會執行** |
| **拿來做** | 分工、隔離 Context、平行處理 | 護欄、自動化、留痕 |
| **失敗模式** | 忘記、跳過、自我感覺良好 | 腳本寫錯、regex 沒對到 |

> 💡 **核心金句**：
> **寫在 Subagent prompt 裡的「記得跑 formatter」「不要碰 .env」是祈求；寫在 Hook 裡的同一件事是事實。**

---

## 專案結構

```text
project-subagent-hooks/
├── .cursor/
│   ├── agents/                   ← Subagent 定義（誰來做）
│   │   ├── planner.md            ← 唯讀，先規劃再動手
│   │   ├── security-auditor.md   ← 唯讀、背景執行，輸出格式固定給 Hook 讀
│   │   └── verifier.md           ← 懷疑論驗證，實際跑測試
│   ├── hooks.json                ← Hook 設定（什麼一定會發生）
│   ├── hooks/
│   │   ├── guard-secrets.sh      ← 擋 secrets 進入任何 context (beforeReadFile)
│   │   ├── guard-shell.sh        ← 擋破壞性指令 (beforeShellExecution)
│   │   ├── format-edit.sh        ← 每次改檔自動格式化 (afterFileEdit)
│   │   ├── subagent-report.sh    ← 每個 subagent 的報告落檔 (subagentStop)
│   │   ├── session-wrap.sh       ← 收尾檢查未驗證就催一次 (stop)
│   │   └── log-payload.sh        ← 除錯用，dump payload
│   ├── reports/                  ← 產出的稽核／驗證報告（.gitignore）
│   └── state/                    ← Hook 的跨呼叫狀態（.gitignore）
├── src/
│   ├── index.ts                  ← API 進入點
│   ├── db.ts                     ← 記憶體資料庫與稽核日誌
│   └── routes/account.ts         ← DELETE /api/account 自助刪帳號實作
├── tests/
│   └── account.test.mjs          ← 原生測試案例（正常刪除、越權防禦、二次確認）
├── demo.sh                       ← 課堂放映遙控器
└── walkthrough.md                ← Step-by-Step 實作指引
```

---

## 🎬 課堂放映與快速體驗

本專案附帶 6 幕課堂放映遙控器：

```bash
# 查看放映幕次清單
./demo.sh

# 播放特定幕次（例如第 1 幕看心智模型，第 4 幕測試安全護欄）
./demo.sh 1
./demo.sh 4
```

完整逐步實作指引請參閱 **[walkthrough.md](./walkthrough.md)**。
