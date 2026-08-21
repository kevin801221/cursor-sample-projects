# Walkthrough：用 Subagent + Hooks 完成一個真實任務

> 任務：為既有的 Node/TypeScript API 專案新增「使用者自助刪除帳號」功能（`DELETE /api/account`），並確保它被規劃過、被稽核過、被驗證過、留下紀錄。
> 這個任務刻意選得有點危險：它碰認證、碰資料刪除、碰不可逆的操作。正因為危險，才看得出 Subagent 跟 Hooks 各自的價值。

---

## 0. 先建立心智模型

新手最常見的誤解是「Subagent 和 Hooks 都是拿來擴充 Cursor 的，二選一就好」。不是。它們解決的是兩種完全不同的問題：

| 維度 | Subagent（次代理人） | Hook（鉤子程式） |
|---|---|---|
| **本質** | 另一個 LLM 實例 | 一個被 spawn 的程序（bash / python / node） |
| **行為** | 機率性 —— 你用 prompt 拜託它 | 確定性 —— 它**一定會執行** |
| **拿來做** | 分工、隔離 context、平行處理 | 護欄、自動化、留痕 |
| **失敗模式** | 忘記、跳過、自我感覺良好 | 腳本寫錯、regex 沒對到 |

> 💡 **一句話總結**：
> **Subagent 決定「誰來做這件事」，Hook 決定「什麼一定會發生、什麼絕對不准發生」。**

寫在 subagent prompt 裡的「記得跑 formatter」「不要碰 .env」是祈求；寫在 hook 裡的同一件事是事實。這篇 walkthrough 的整個設計就是圍繞這個分界線。

---

## 1. 前置準備

1. **Cursor 2.4 以上**（subagent 從 2.4 開始，2.5 加了非同步與巢狀）。
2. **安裝 jq** —— 底下所有 hook 腳本都靠它解析 stdin 的 JSON：
   ```bash
   brew install jq       # macOS
   sudo apt install jq   # Debian/Ubuntu
   ```
3. **目錄結構與 gitignore**：
   產出目錄不要進版控，但 `.cursor/agents/` 和 `.cursor/hooks.json` 必須進版控（那是團隊共用的契約）：
   ```gitignore
   .cursor/reports/
   .cursor/state/
   .cursor/hooks/log/
   ```

---

## 2. Step 1：定義三個 Subagent

`.cursor/agents/` 底下每個 `.md` 就是一個 subagent。格式是 YAML frontmatter + prompt 本體。

### 2.1 planner —— 先想再做
`.cursor/agents/planner.md`：
```markdown
---
name: planner
description: 動手改任何程式碼之前先產出實作計畫。當任務跨越三個以上檔案，或牽涉認證、權限、資料刪除、金流時主動使用。
model: inherit
readonly: true
---

你負責規劃，不負責實作。你絕對不修改任何檔案。

收到任務時：
1. 先搜尋 codebase，找出這次改動會碰到的所有檔案
2. 找出專案既有的慣例（錯誤處理、驗證、交易、測試怎麼寫）
3. 標出所有不可逆或有風險的步驟

輸出固定用這個結構：
## 受影響的檔案
## 實作步驟
## 風險
## 需要人類決定的事
## 驗收標準
```

### 2.2 security-auditor —— 平行稽核
`.cursor/agents/security-auditor.md`：
```markdown
---
name: security-auditor
description: 安全稽核專家。實作完認證、權限、使用者資料刪除、金流相關的程式碼後一律使用。
model: inherit
readonly: true
is_background: true
---

你是資安稽核者。你只讀、只回報，不修改任何檔案。

針對這次的改動，依序檢查：
1. 授權：呼叫者能不能影響到「不是自己」的資源？
2. 資料刪除：關聯資料有沒有漏刪？該保留的稽核紀錄有沒有被一起刪掉？
3. 不可逆性：有沒有二次確認？有沒有復原窗口？
4. 濫用：有沒有 rate limit？
5. 資訊洩漏：錯誤訊息或回應有沒有洩漏不該給的資訊
6. Secrets：有沒有硬編碼的金鑰、token、連線字串

**輸出格式（必須嚴格遵守，下游有自動化程式在讀）**：
Critical: <問題> — <檔案:行號> — <怎麼修>
High: <問題> — <檔案:行號> — <怎麼修>
Medium: <問題> — <檔案:行號> — <怎麼修>

沒有發現就只輸出一行：`No findings.`
```

### 2.3 verifier —— 不信任地驗證
`.cursor/agents/verifier.md`：
```markdown
---
name: verifier
description: 懷疑論驗證者。任何任務被宣稱「完成」之後使用，確認實作真的能跑。
model: inherit
---

你是個懷疑論者。你的工作是證明「宣稱完成的東西」其實沒完成。

流程：
1. 列出這次被宣稱完成的項目
2. 逐項確認程式碼真的存在而且會被執行到（不是寫了但沒接上）
3. 實際執行測試，貼出真實輸出。不要用「應該會過」這種說法
4. 主動找 edge case：空值、重複呼叫、併發、權限邊界

**你不修改任何原始碼**。測試沒過就回報沒過，不要動手改到它過。
```

> 🔍 **為什麼 verifier 沒有 readonly: true？**
> 因為 readonly 會擋掉「會改變狀態的 shell 指令」，而測試指令有機會被歸在這一類，導致 verifier 跑不了測試。所以這裡改用兩層防護：prompt 裡明講不准改檔，加上 hook 會把實際改過的檔案列出來。

---

## 3. Step 2：搭建 Hooks 骨架

`.cursor/hooks.json`：
```json
{
  "version": 1,
  "hooks": {
    "beforeReadFile": [
      { "command": ".cursor/hooks/guard-secrets.sh", "failClosed": true }
    ],
    "beforeShellExecution": [
      {
        "command": ".cursor/hooks/guard-shell.sh",
        "matcher": "rm\\s+-rf|drop\\s+(table|database)|truncate|migrate\\s+reset|--force",
        "failClosed": true
      }
    ],
    "afterFileEdit": [
      { "command": ".cursor/hooks/format-edit.sh", "timeout": 15 }
    ],
    "subagentStop": [
      { "command": ".cursor/hooks/subagent-report.sh", "loop_limit": 2 }
    ],
    "stop": [
      { "command": ".cursor/hooks/session-wrap.sh", "loop_limit": 1 }
    ]
  }
}
```

三個一定要記住的規則：
1. **專案 hook 的工作目錄是專案根目錄**，路徑寫 `.cursor/hooks/x.sh`。
2. **matcher 用的是 JavaScript regex**，不是 POSIX（所以是 `\s` 不是 `[[:space:]]`）。
3. **`failClosed: true`** 代表腳本自己壞掉時要擋下動作。安全相關的 hook 一定要加。

---

## 4. Step 3–5：實現五大 Hook 腳本

### 4.1 護欄一：不讓 secrets 進到任何 context (`guard-secrets.sh`)
* 阻擋讀取 `.env`, `*.pem`, `*.key`, `*id_rsa*`, `*/secrets/*`。
* 放行 `*.env.example`, `*.env.sample`。

### 4.2 護欄二：擋不可逆指令 (`guard-shell.sh`)
* 阻擋 `prisma migrate reset`, `drop table`, `truncate`。
* 阻擋危險的 `rm -rf /`。
* 對 `force push` 攔截改跳出詢問人類（`ask`）。

### 4.3 自動化：每次改檔自動格式化 (`format-edit.sh`)
* 每次 Agent 改完 `.ts`/`.js`/`.json`/`.md`，背景自動執行 Prettier 與 ESLint 修復排版。

### 4.4 留痕：把 Subagent 的產出落檔 (`subagent-report.sh`)
* Subagent 結束時自動將報告寫入 `.cursor/reports/${timestamp}-${role}.md`。
* 若資安稽核回報包含 `Critical:`，**自動產生 `followup_message` 把球踢回給主 Agent 強制回頭修正**！

### 4.5 收尾：確保驗證真的有發生 (`session-wrap.sh`)
* 整個 Agent session 結束時，檢查是否有呼叫過 `verifier`。若沒有，主動催促 Agent 執行真實測試。

---

## 5. Step 9：實際跑一遍（三輪標準流程）

### 第一輪：規劃
對 Agent 說：
> 我要為這個專案新增「使用者自助刪除帳號」功能：`DELETE /api/account`。
> 先用 planner 產出實作計畫給我看，這一輪不要動任何程式碼。

你會看到：
1. `planner` subagent 啟動並調用 `explore`。
2. 回傳結構化計畫，`.cursor/reports/` 出現 `*-planner.md`。

### 第二輪：實作 + 平行審查
計畫審查確認後，對 Agent 說：
> 照計畫實作。實作完成後同時做兩件事：
> 1. 用 `security-auditor` 稽核這次的所有改動
> 2. 用 `verifier` 確認功能真的能跑
> 兩個平行跑。

執行時的自動化鏈路：
1. 改檔時 `afterFileEdit` 自動排版。
2. 嘗試危險指令時 `beforeShellExecution` 阻擋。
3. 實作完成後，兩個 subagent 平行啟動。
4. 結束時報告自動落檔進 `.cursor/reports/`。
5. 若發現 `Critical:`，主 agent 被自動要求回頭修復。

### 第三輪：看報告，不是看對話
```bash
ls -t .cursor/reports/ | head -5
```
打開報告確認稽核無 Critical、驗證全數通過。

---

## 6. 驗收清單

- [x] Customize → Hooks 分頁列出五個 hook，沒有紅字。
- [x] 叫 agent 讀 `.env` → 被擋，看得到阻擋訊息。
- [x] 叫 agent 讀 `.env.example` → 正常讀得到（例外規則有效）。
- [x] 叫 agent 跑 `prisma migrate reset` → 被擋，收到替代方案。
- [x] 讓 agent 隨便改一個 `.ts` 檔 → 存檔後自動格式化。
- [x] `.cursor/reports/` 裡每個 subagent 都有對應的 `.md` 落檔。
- [x] 故意在程式碼留授權漏洞，`security-auditor` 回報 `Critical:` 並自動觸發主 agent 修復。

---

## 7. 一句話總結

> **Subagent 讓你把工作分給對的人，Hook 讓你不必相信任何人。兩個一起用，Agent 產出的東西才有辦法進 Production。**
