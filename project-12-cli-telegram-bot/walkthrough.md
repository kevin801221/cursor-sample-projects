# Walkthrough：一步一步做出可發佈的 CLI 與會發圖的 Telegram Bot

> 這份文件帶你從零做出 **CLI 工具** 與 **Telegram Bot**——一個能用 `npx` 執行的腳手架產生器，加上支援按鈕互動、會自動產生指板圖片的機器人。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，動手時才不會卡）

1. **跑通一次 CLI 完整流程**：先在本地 `npm link` → `scaffold init test-project` → 確認專案資料夾被建出來，exit code 正確（成功是 0、失敗是 1）。
2. **先跟 BotFather 申請一個 Bot token**：去 Telegram 搜尋 @BotFather → `/newbot` → 建一個 Bot 帳號 → 把 token 存起來。本地測試要用。
3. **用自己的手機試過 Bot 一次**：跑 `python main.py`，用自己的手機加 Bot 傳訊息，確認收得到回覆。最重要的是測試按鈕點擊：**點按鈕後不能轉圈超過 3 秒，必須立刻看到訊息更新。**
4. **把本文件每個「✅ 預期看到」瀏覽一遍**：知道正常畫面長怎樣，動手時才判斷得出「這是正常的」還是「出事了」。
5. **備用方案**：把 exit code 驗證、按鈕點擊成功的截圖存起來。如果 Node 或 Python 出事，直接看截圖講概念也能繼續。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 30 分 | 閱讀理解（全課靈魂，慢慢看） |
| 第 2 節 CLI 骨架與參數解析 | 25 分 | 動手做（npm link 效果立竿見影） |
| 第 3 節互動提問 + exit code | 20 分 | 動手做（驗證 exit code 是最精彩的一幕） |
| 第 4 節模板系統 | 20 分 | 閱讀理解 + 動手做（細節多，看懂再回頭補做） |
| 第 5 節發佈 npm | 15 分 | 閱讀理解（npm publish 用講解可以理解） |
| 第 6–7 節 Bot 基礎與按鈕 | 35 分 | 動手做（query.answer() 體感最好親自試） |
| 第 8 節圖片生成與部署 | 20 分 | 動手做（指板圖產出後再部署） |
| 最後三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./scaffold-and-bot/`，遙控器是 `./demo.sh`（位於 `project-12-cli-telegram-bot/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 內建 CLI 模板與 Telegram 機器人離線模擬器，全 5 幕 100% 離線可跑，不需 Telegram Token 即可完成演示。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd project-12-cli-telegram-bot/scaffold-and-bot && uv sync` | 第一次同步 uv 虛擬環境與下載依賴。課前做完後，課堂上全離線秒開 |
| 2 | 跑一次 `./demo.sh 5`（測試全綠） | 執行 pytest 確認 4 passed（CLI 退出碼、圖片生成、回調速度）全綠 |
| 3 | （選配）若有 Telegram Bot Token 可填入 `.env`，或直接使用內建模擬器放映 | 內建模擬器 100% 離線秒回，免費用、無轉圈風險 |

### 放映時間軸

時間軸切成 6 段，對應上方學習地圖（合計 180 分鐘），全長 **3 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 咒語/回報規則/信鴿管家三比喻、CLI Exit Code 意義、Webhook vs Polling | 指令列工具與機器人通訊基礎 |
| 0:30–0:55 | 第 1 幕：CLI 腳手架專案生成 | `./demo.sh 1` | `scaffold-and-bot/cli/bin/scaffold.js` | 執行 `scaffold init`，依據 React 模板產出完整專案 | 腳手架原理與樣板複製引擎 |
| 0:55–1:15 | 第 2 幕：Exit Code 規範驗證 ⭐ | `./demo.sh 2` | `scaffold-and-bot/cli/bin/scaffold.js` | 成功產出印 Exit 0；重複建立故意觸發退件並印 Exit 1 | 軟體回報規則：成功喊 0、出事喊 1 |
| 1:15–1:50 | 第 3 幕：Bot 按鈕秒回機制 ⭐ | `./demo.sh 3` | `scaffold-and-bot/bot/main.py` | `query.answer()` 毫秒級回調，按鈕點擊後轉圈立即停止 | 先承諾再交貨：消除使用者卡頓感的關鍵 |
| 1:50–2:30 | 第 4 幕：吉他指法圖生成 | `./demo.sh 4` | `scaffold-and-bot/bot/chord_generator.py` | Pillow 繪製產出 C, G, Am, Em, F, D 和弦高清指板圖 | Python 影像處理與動態多媒體產生 |
| 2:30–3:00 | 第 5 幕：pytest 測試全綠 | `./demo.sh 5` | `scaffold-and-bot/tests/test_scaffold_and_bot.py` | 4 passed 全綠色通過 | 跨語言 CLI 與機器人測試自動化驗證 |

### ⭐ 全場最值得停下來的一幕

**第 2 幕的 Exit Code 對照與第 3 幕的秒回機制。**
在第 2 幕現場展示：當目錄已存在時，CLI 印出紅色錯誤提示並以 Exit Code 1 退出，證明腳本能被 CI/CD 安全捕捉；在第 3 幕展示機器人處理流程：Handler 是如何在 10 毫秒內先送出 `query.answer()` 停止客戶端轉圈，再去背景生成圖片。

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 測試臨時資料夾衝突 | `/tmp` 權限或檔案殘留 | 腳本會自動 `rm -rf /tmp/demo-react-app`，也可手動清除 |
| 和弦圖片未生成 | 找不到圖片路徑 | 執行 `./demo.sh 4` 將自動產出所有 6 組和弦圖至 `data/` 目錄 |

---

## 🎬 開場故事：三種「跟電腦講話」的方式

今天要學的東西很「魔法」。平時我們用滑鼠點點點，叫電腦做事。今天要改一種方式——用『咒語』。

咒語長這樣：`scaffold init my-app`。一句話，電腦立刻替你從『藍圖』產出完整的專案資料夾。

還有另一種咒語，叫『回報規則』。軍隊裡有個傳統：士兵執行任務回報長官，成功喊『0 號』（everything is zero），出事喊『1 號、2 號』（something went wrong）。長官靠這些號碼決定下一步要不要派人。電腦的 exit code 就是這個——你的指令成功了嗎？0 是說『都行』，非 0 是說『我出事了，別信我』。

最後一種魔法，叫『信鴿管家』。你養一隻信鴿在房裡當秘書，她每隔幾秒就去外面信箱瞄一眼『有沒有新信』。這叫 polling——主動去拿。但有個偷懶的方式：改成『等郵差』，郵差直接按你家門鈴遞信，你一聽到鈴聲立刻回應『收到！』再去讀信。這叫 webhook——被動接收。但這兩招不能同時用，要嘛一直派信鴿，要嘛坐著等郵差，否則兩邊都來信會搶著敲門。

還有一件事：信鴿傳話時要先喊『我來了』，客人才知道要停止等待、放下電話。程式也一樣。Telegram Bot 的按鈕被點了，handler 要先喊『我收到了』（query.answer()），手機上的轉圈才會停下，客人才覺得快。這叫 callback——先承諾再交貨。

這份文件就是用這三個故事來貫穿的。

---

## 0. 課前準備

- 安裝 Cursor Pro、Node.js 20+、Python 3.8+、uv（Python 套件管理）
- 註冊 Telegram 帳號，用 @BotFather 建一個 Bot 帳號（申請 token）
- 本地 Terminal 習慣（npm link 的權限問題需要熟悉 nvm）

> 🔍 **名詞卡：CLI（Command Line Interface）**
> 白話：不用滑鼠點畫面、改用「打字下指令」操作電腦的方式。工程師愛用是因為指令可以複製、重播、寫成劇本。比喻：郵差有一本「遞信規則手冊」，每次按門鈴時直接依序照著手冊做，不用每次都問你「要不要收信」——效率爆表。
>
> 🔍 **名詞卡：参数解析（argument parsing）**
> 白話：電腦聽你講話時，要理解「哪部分是指令名稱、哪部分是參數」。例如 `scaffold init my-app` 裡，`init` 是子指令，`my-app` 是參數。比喻：點餐時服務生聽「請給我一份炒飯」，要理解「炒飯」是菜色名，數量是「一份」，不然可能給你十份。
>
> 🔍 **名詞卡：npm / package.json**
> 白話：Node.js 的「套件超市」與「購物清單」。package.json 是清單，列出你要用什麼工具、版本多少；npm install 就是去超市照單下訂。
>
> 🔍 **名詞卡：exit code（離開碼）**
> 白話：指令跑完後丟出來的一個數字，告訴後續的程式「我成功了嗎」。0 = 成功，非 0（通常 1）= 失敗。比喻：廚房做好一盤菜，服務生用『廚房給了我一個綠燈 / 紅燈』的方式告訴點餐系統「可以上菜嗎」。

---

## 1. 核心概念：DO NOT CODE、Exit Code、Callback

### 1.1 DO NOT CODE——為什麼先計畫省時間

常見模式：提需求 → Agent 立刻寫 100 行代碼 → 發現理解有誤 → 刪掉重寫。

**更好的做法**：提需求 → Agent 先產步驟清單 → 你審核設計 → 才動手寫。

原文 prompt：

```text
DO NOT CODE. Prepare a step-by-step
execution plan as it's going to be
implemented by a junior engineer
```

**三個層級**：
1. **禁止立刻寫程式**——明確告訴 Agent 不准動手
2. **步驟細到可交接**——連經驗較淺的工程師也能照著做
3. **這是審核機會**——比事後改成品便宜

為什麼要用 DO NOT CODE？如果你直接說『做一個 CLI』，Agent 可能會一口氣寫 500 行，裡面有你沒想到的決定。但你先用 DO NOT CODE 把它綁住，讓它先給計畫，你看了再說『可以』或『改一下』。這就像建築師先給施工圖，承包商照著圖施工，遠比『邊打邊想』安全。

本章會在每個大功能前都用這個 prompt。

### 1.2 Exit Code——CLI 的無聲殺手

你的 CLI 如果這樣寫：

```javascript
// ✗ 危險：永遠成功
const result = await copyTemplate(...);
// 沒有 process.exit() 或 exitCode 設定
```

CI 腳本測試會看到 `$? = 0`（成功），但實際失敗了——資料庫部署、自動化測試全部過，程式卻跑不起來。**一條命令把整條 pipeline 破壞。**

**正確做法**：

```javascript
// ✓ 安全：失敗時明確設 exit code
try {
  const result = await copyTemplate(...);
  console.log(`✓ 專案已建立: ${projectName}`);
  process.exit(0);  // 明確成功
} catch (error) {
  console.error(`✗ 建立失敗: ${error.message}`);
  process.exitCode = 1;  // 明確失敗
}

// 使用者取消也要清楚表達，但不算錯誤
if (answers.cancel) {
  console.log("操作已取消");
  process.exit(0);
}
```

**驗證方式**：`echo $?` 看最後一個指令的回傳值。

| 情況 | 該回傳 | 驗證 |
|---|---|---|
| 成功完成 | 0 | `scaffold init my-app; echo $?` → 0 |
| 使用者取消 | 0 | 同上，不算錯誤 |
| 失敗（磁碟滿、權限等） | 1 | 同上 → 1 |

> 🔍 **名詞卡：CI / CD（Continuous Integration / Deployment）**
> 白話：自動化測試與發佈工廠。你一 push 程式，工廠自動跑測試、部署，如果某一步失敗就停止。exit code 就是工廠判斷「這一步成功還是失敗」的訊號燈。比喻：工廠傳送帶上有檢驗員，他看盒子完不完整（exit code 是 0）還是缺角（exit code 是 1），來決定要不要繼續下個工序。

> ❓ **想一想**：如果 CLI 忘了設 exit code，CI 腳本會發生什麼？
> 
> **答案**：CI 無法分辨這個步驟成功還是失敗，會誤認為成功並繼續下一步，導致整個 pipeline 爆炸。

### 1.3 Callback Handler 的轉圈地獄

Telegram Bot 最常踩的坑：

```python
# ✗ 錯誤：漏了 query.answer()
async def button_click(update, context):
    query = update.callback_query
    # 直接回傳圖片，沒有 query.answer()
    await query.edit_message_media(...)
```

**表現**：使用者點按鈕後看到不停轉圈（Loading...），過幾秒才逾時消失。體感極糟。

**正確做法**：

```python
# ✓ 安全：先答、再更新
async def button_click(update, context):
    query = update.callback_query
    await query.answer()  # 立刻回應，清掉轉圈
    # 再慢慢產生圖片、更新訊息
    img = generate_fretboard_image(note_name)
    await query.edit_message_media(...)
```

**理解**：`query.answer()` 是告訴 Telegram「我收到了」，立刻在用戶端清掉轉圈。實際的圖片產生可能花 1-2 秒，但用戶已經不用等轉圈了。

> 🔍 **名詞卡：callback（回呼）**
> 白話：先承諾、再交貨的工作模式。客人按服務鈴，前台立刻喊「來了！」（query.answer()），然後再去廚房料理。不然客人會以為鈴壞了，一直按。比喻：餐廳點餐，點餐員收單時先說「好，我收到了」，然後才去廚房下單；不是點餐員收了單卻一句話不說，直接轉身走進廚房，客人會焦慮「他有沒有聽到我的單」。
>
> 🔍 **名詞卡：polling（輪詢）vs webhook（網路鉤子）**
> 白話：polling = 定期主動去問「有沒有新消息」（信鴿每 5 秒去信箱瞄一眼）；webhook = 有新消息時 Telegram 主動來敲門（郵差直接按門鈴）。比喻：polling 像你每隔幾分鐘去便利店看有沒有取件，webhook 像便利店員打電話「你的貨到了」。
>
> ❓ **想一想**：polling 和 webhook，哪一個會浪費網路？
>
> **答案**：polling。即使沒有新消息你也要定期問一次，會產生很多無用的請求。webhook 只在有東西時才推送。

### 1.4 結構化反饋循環六步驟

複雜任務時用這個流程：

| 步驟 | 做什麼 | 產出 | 時間 |
|---|---|---|---|
| 1 | 覆述需求 | Agent 用自己的話講一遍，你確認理解一致 | 2-3 分鐘 |
| 2 | 產計畫 | 用 DO NOT CODE prompt，拿到分解後的步驟清單 | 5-10 分鐘 |
| 3 | 審核計畫 | 你看有沒有遺漏、順序有沒有問題 | 2-3 分鐘 |
| 4 | 逐步實作 | 每完成一個步驟就停、驗證、commit | 主體時間 |
| 5 | 驗收 | 跑測試、看 exit code、手動測一遍 | 5-10 分鐘 |
| 6 | 回看 commit | 從 commit 訊息能說出你做了什麼 | 2-3 分鐘 |

**收益**：用 1 小時計畫省 3 小時返工。

有人說『計畫太浪費時間，我直接動手快多了』。但現實是：快速上手的十分鐘，換來後面四小時的返工。工程師最常做的事不是寫程式，是改前一個人的程式。所以先花五分鐘確認『我們要蓋什麼』，省的是五小時的推倒重來。

---

## 2. 階段一：CLI 骨架與計畫

### 2.1 初始化與 bin 設定

Node CLI 要能被 npm 全域安裝或 npx 直接執行，得靠 `package.json` 的 bin 欄位。

對 Agent 說：

> DO NOT CODE. 我要建立一個 npm package，讓使用者可以執行 `npx create-project-scaffold init my-app`。package.json 需要設定什麼，使得 bin/index.js（執行檔）能被綁成 scaffold 指令？

產出重點：

```json
{
  "name": "create-project-scaffold",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "scaffold": "./index.js"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

`index.js` 最上面要加 Shebang：

```javascript
#!/usr/bin/env node

// CLI 程式主體
```

Shebang `#!/usr/bin/env node` 讓 OS 知道這是 Node 腳本，npm link 或全域安裝後才能直接執行 `scaffold` 指令。

> 🔍 **名詞卡：Shebang**
> 白話：檔案開頭的咒語，告訴作業系統「用什麼程式打開這個檔案」。比喻：信封上寫「親愛的郵差」，郵差知道這是給他的信；shebang 就是檔案上寫的「用 Node 打開我」。
>
> 🔍 **名詞卡：npm link**
> 白話：在你電腦的全域 Node 目錄建立一個指向、讓本地開發中的套件也能當全域指令執行。像在廚房開發食譜時，不用等出版社印製、直接在自家廚房試做。

**驗收**：`npm link` 後 `scaffold --version` 有反應。

✅ **預期看到**：
```
$ npm link
added 45 packages, and audited 46 packages in 2s
/Users/kevin/.nvm/versions/node/v20.10.0/bin/scaffold -> /path/to/cli/index.js

$ scaffold --version
0.1.0
```

🧯 **卡住的話**：
- 權限錯誤 (`EACCES: permission denied`)：**不要用 `sudo npm link`**，改用 nvm 管理 Node 版本。遇到這個錯誤表示你的 Node 用了系統權限安裝，改用 nvm 自己裝的 Node。
- 指令名找不到：檢查 package.json 的 `bin` 欄位對應 `index.js`；如果寫的是 `"bin": { "scaffold": "./bin/index.js" }`，檔案卻在根目錄，就找不到。

### 2.2 Commander 解析指令與參數

Commander 處理指令樹、子指令、flag、--help。

對 Agent 說（用 DO NOT CODE）：

> DO NOT CODE. 我要用 commander 建立一個 CLI，有以下結構：
> - 主指令：scaffold
> - 子指令：init（對應 `scaffold init <project-name>`）
> - init 支援 flag：--template（可選，預設 next-app）
> - 每個指令都有說明，--help 要顯示清楚
>
> 步驟清單應該包括：1. 建立 Program 物件 2. 定義子指令與參數 3. 描述與 --help 設定 4. 解析 process.argv

產出重點：

```javascript
import { Command } from 'commander';

const program = new Command();

program
  .name('scaffold')
  .description('快速產生專案腳手架')
  .version('0.1.0');

program
  .command('init <projectName>')
  .description('建立新專案')
  .option('--template <type>', '選擇模板 (next-app, express-api)', 'next-app')
  .action((projectName, options) => {
    console.log(`建立專案: ${projectName}, 模板: ${options.template}`);
  });

program.parse(process.argv);
```

> 🔍 **名詞卡：Commander**
> 白話：Node.js 的「指令解析工廠」。你告訴它「我的指令叫 init、要一個 projectName 參數、有個 --template flag」，它自動幫你檢查輸入、產生 --help、組織子指令。比喻：KTV 點歌系統，你說「我要唱『老鼠愛大米』，字幕要英文」，點歌系統自動理解「歌曲名 = 老鼠愛大米、語言 flag = english」。

**驗收**：
```bash
scaffold --help              # 看到子指令與說明
scaffold init --help         # 看到 init 的選項
scaffold init my-app         # 執行 init 並看到輸出
```

✅ **預期看到**：
```
$ scaffold init --help
Usage: scaffold init [options] <projectName>

建立新專案

Options:
  --template <type>  選擇模板 (next-app, express-api) (default: "next-app")
  -h, --help         display help for command

$ scaffold init my-app
建立專案: my-app, 模板: next-app
```

### 2.3 Inquirer 互動提問

Inquirer 提供下拉選單、文字輸入、確認框，讓 CLI 更友善。

對 Agent 說：

> DO NOT CODE. 產出步驟計畫：用 inquirer 在 init 的 action 內新增三個互動：
> 1. 確認專案名稱（若命令列沒傳，或讓使用者確認）
> 2. 從下拉選單選擇模板（next-app / express-api）
> 3. 確認建立（yes/no）
>
> 步驟應包括 inquirer 的三種問題型態、迴圈驗證、回傳 answers 物件。

產出重點：

```javascript
import inquirer from 'inquirer';

const answers = await inquirer.prompt([
  {
    type: 'input',
    name: 'projectName',
    message: '專案名稱',
    default: 'my-project',
    validate: (input) => /^[a-z0-9-]+$/.test(input) || '只接受英文字母、數字、連字號'
  },
  {
    type: 'list',
    name: 'template',
    message: '選擇模板',
    choices: ['next-app', 'express-api']
  },
  {
    type: 'confirm',
    name: 'proceed',
    message: '確認建立？'
  }
]);

if (!answers.proceed) {
  console.log('操作已取消');
  process.exit(0);
}

console.log(`建立 ${answers.projectName}，使用模板 ${answers.template}`);
```

> 🔍 **名詞卡：Inquirer**
> 白話：讓 CLI 變得「友善」的工具，會問你問題、讓你用上下鍵選、按 Enter 確認。比喻：銀行 ATM 的選單——不是讓你手打 `withraw 500 usd`，而是「請問要提款嗎？要提多少？」逐步引導。

**驗收**：執行 `scaffold init` 後能用上下鍵選選單、輸入名稱、確認建立。

✅ **預期看到**：
```
? 專案名稱 (my-project) my-awesome-app
? 選擇模板 (Use arrow keys)
❯ next-app
  express-api
? 確認建立？ (Y/n) Y
```

🧯 **卡住的話**：如果 Inquirer 提問沒跳出來（黑屏一片），通常是 async/await 寫錯或者遺漏了 action 的 async 修飾。記住：`inquirer.prompt()` 回傳 Promise，要用 await 等結果。

### 2.4 本地測試：npm link ⭐ 一定要親自試的一幕

`npm link` 在你的 Node.js 全域 bin 目錄建立符號連結，讓 CLI 指令可直接執行。

```bash
cd cli
npm link
# 輸出類似：
# added 45 packages, and audited 46 packages in 2s
# /Users/kevin/.nvm/versions/node/v20.10.0/bin/scaffold -> /path/to/cli/index.js

# 此刻任何地方都能執行 scaffold 指令
scaffold init my-app
```

現在來測試神奇的一刻。在終端機隨便哪裡，輸入 `scaffold init test-app`——看，它直接從你本地開發中的程式跑起來了。這就是 npm link 的威力：不用發佈到 npm 伺服器，就能讓你的 CLI 像正式產品一樣執行。

✅ **預期看到**：
```
$ which scaffold
/Users/kevin/.nvm/versions/node/v20.10.0/bin/scaffold

$ scaffold --help
Usage: scaffold [options] [command]

...

$ scaffold init new-project
? 專案名稱 (my-project) new-project
? 選擇模板 next-app
? 確認建立？ Yes
✓ 專案已建立: /Users/kevin/new-project
```

🧯 **卡住的話**：
- 權限錯誤 (`EACCES`)：不要用 `sudo npm link`，改用 nvm 管理 Node 版本。
- 指令名找不到：確認 package.json 的 `bin` 欄位對應 `index.js`。
- 修改後沒生效：npm link 只是符號連結，修改檔案立刻生效；若還是沒反應，重新 `npm link`。

---

## 3. 階段二：模板系統與複製邏輯

### 3.1 模板資料夾結構

建立 `cli/templates/` 存放模板：

```
cli/
├── templates/
│   ├── next-app/
│   │   ├── package.json
│   │   └── ...（其他檔案）
│   └── express-api/
│       ├── package.json
│       └── ...（其他檔案）
└── index.js
```

對 Agent 說（DO NOT CODE）：

> 我要建立兩個模板骨架：next-app（Next.js 最小應用）、express-api（Express 伺服器）。
> 各模板的 package.json 的 name 欄位應該是什麼？為什麼不能寫死為「next-app」或「express-api」？
> 產出步驟清單：1. 兩個模板各含什麼檔案 2. package.json 的 name 用什麼佔位符 3. 複製時怎麼替換

產出重點：每個模板的 `package.json` 用佔位符：

```json
{
  "name": "{{projectName}}",
  "version": "1.0.0"
}
```

複製時用字串替換把 `{{projectName}}` 換成使用者輸入的名稱。

> 🔍 **名詞卡：樣板（template）/ 佔位符（placeholder）**
> 白話：樣板是「半成品藍圖」，佔位符是藍圖上的「空白欄位」，複製時填進去真實資料。比喻：婚禮邀請卡是樣板，「親愛的 {{姓名}}，誠摯邀請您蒞臨…」，郵差複製時把 {{姓名}} 替換成「王美玉」、「李大明」各一份。

### 3.2 複製邏輯

對 Agent 說：

> 寫 lib/copyTemplate.js，實作以下功能：
> 1. 接收 templateName（'next-app' 或 'express-api'）與 targetPath
> 2. 遍歷 templates/{templateName} 所有檔案
> 3. 對 package.json 做字串替換（{{projectName}} → 使用者名稱）
> 4. 其他檔案直接複製
> 5. 失敗要 throw Error

產出重點：

```javascript
// lib/copyTemplate.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export async function copyTemplate(templateName, projectName, targetPath) {
  const templatePath = path.join(__dirname, '..', 'templates', templateName);
  
  if (!fs.existsSync(templatePath)) {
    throw new Error(`模板不存在: ${templateName}`);
  }

  fs.mkdirSync(targetPath, { recursive: true });

  const files = fs.readdirSync(templatePath);
  for (const file of files) {
    const src = path.join(templatePath, file);
    const dest = path.join(targetPath, file);

    if (fs.statSync(src).isDirectory()) {
      copyTemplate(templateName, projectName, dest);  // 遞迴
    } else {
      let content = fs.readFileSync(src, 'utf-8');
      if (file === 'package.json') {
        content = content.replace(/\{\{projectName\}\}/g, projectName);
      }
      fs.writeFileSync(dest, content);
    }
  }
}
```

✅ **預期看到**：複製後 `cat ./my-app/package.json | grep name` 看到正確的專案名稱。

```
$ scaffold init my-awesome-app
✓ 專案已建立: /Users/kevin/my-awesome-app

$ cat ./my-awesome-app/package.json | grep name
  "name": "my-awesome-app",
```

### 3.3 整合到 init action

對 Agent 說：

> 修改 index.js 的 init action，整合：
> 1. inquirer 提問
> 2. 驗證專案資料夾不存在
> 3. 呼叫 copyTemplate
> 4. 失敗時設 process.exitCode = 1
> 5. 成功時設 process.exit(0)

產出重點（重視 exit code）：

```javascript
import { copyTemplate } from './lib/copyTemplate.js';

program
  .command('init <projectName>')
  .action(async (projectName) => {
    try {
      const answers = await inquirer.prompt([
        // ... inquirer 邏輯
      ]);

      if (!answers.proceed) {
        console.log('操作已取消');
        process.exit(0);
      }

      const targetPath = path.join(process.cwd(), projectName);
      if (fs.existsSync(targetPath)) {
        throw new Error(`資料夾已存在: ${targetPath}`);
      }

      await copyTemplate(answers.template, projectName, targetPath);
      console.log(`✓ 專案已建立: ${targetPath}`);
      console.log('執行以下指令開始開發：');
      console.log(`  cd ${projectName} && npm install && npm start`);

      process.exit(0);  // ✓ 明確成功
    } catch (error) {
      console.error(`✗ 建立失敗: ${error.message}`);
      process.exitCode = 1;  // ✓ 明確失敗
    }
  });
```

**驗收**：執行 `scaffold init test-app; echo $?` → 0（成功）；`scaffold init test-app; echo $?` → 1（資料夾已存在，失敗）。

✅ **預期看到**：
```
$ scaffold init test-app; echo $?
? 專案名稱 (my-project) test-app
? 選擇模板 next-app
? 確認建立？ Yes
✓ 專案已建立: /Users/kevin/test-app
執行以下指令開始開發：
  cd test-app && npm install && npm start
0

$ scaffold init test-app; echo $?
? 專案名稱 (my-project) test-app
? 選擇模板 next-app
? 確認建立？ Yes
✗ 建立失敗: 資料夾已存在: /Users/kevin/test-app
1
```

🧯 **卡住的話**：exit code 永遠是 0——說明沒有明確設 `process.exitCode` 或 `process.exit()`。快速修法：把失敗路徑加上 `process.exitCode = 1`；成功路徑加上 `process.exit(0)`。修改後重試，就能看到 exit code 的威力。

> ❓ **想一想**：如果 CLI 不設 exit code，CI 腳本會發生什麼？
>
> **答案**：CI 無法分辨這個步驟成功還是失敗，會誤認為成功並繼續下一步，導致整個 pipeline 爆炸。

---

## 4. 階段三：發佈到 npm

### 4.1 測試發佈流程

發佈前的最後驗證步驟。

```bash
cd cli

# 1. 測試全域安裝（模擬最終使用者）
npm link
scaffold init final-test
cd final-test && npm install && npm start
cd ..

# 2. 檢查 package.json 版本
npm pkg get version

# 3. 執行 exit code 驗證
scaffold init final-test; echo $?       # 失敗 → 1
scaffold init new-project; echo $?      # 成功 → 0
```

### 4.2 npm registry 帳號與發佈

```bash
# 登入 npm（無帳號先去 npmjs.com 註冊）
npm login

# 發佈（--access public 讓包公開可下載）
npm publish --access public

# 驗證發佈成功
npm search create-project-scaffold
npm view create-project-scaffold versions   # 看版本列表
```

> 🔍 **名詞卡：npm registry**
> 白話：npm 套件的「中央超市」。你的 CLI 發佈到這裡，全世界的開發者都可以 `npx` 直接執行，不用安裝。比喻：Apple App Store，開發者上傳 App，用戶直接下載用。

**發佈後的驗證**（在完全不同的資料夾測試）：

```bash
cd /tmp
npx create-project-scaffold init real-world-test
# 若 npm registry 延遲同步（通常 5-10 分鐘），可能要稍等
```

✅ **預期看到**：
```
$ npx create-project-scaffold init real-world-test
need to install the following packages:
 create-project-scaffold
ok to proceed? (y) y

? 專案名稱 (my-project) real-world-test
? 選擇模板 next-app
? 確認建立？ Yes
✓ 專案已建立: /tmp/real-world-test
```

---

## 5. 階段四：Telegram Bot 核心

### 5.1 取得 Token 與設定 .env

Telegram Bot 需要 token 與 chat id。

```bash
# 在 Telegram 找 @BotFather
/start → /newbot → 輸入 Bot 名稱 → BotFather 回傳 token

# bot/ 資料夾建立 .env
echo "TOKEN=<your_bot_token>" > .env
echo ".env" >> .gitignore   # 勿提交機密
```

> 🔍 **名詞卡：Telegram Bot API**
> 白話：Telegram 提供的「遙控器」，讓你用程式操控一個 Bot 帳號。比喻：你買一台電視，遙控器就是 TV 的 API——按鍵對應「換台、調音量」等指令。
>
> 🔍 **名詞卡：Token**
> 白話：Bot 的「身分證」，用來證明「我是這個 Bot」。別人看到你的 token 就能冒充你的 Bot，所以要藏在 .env 裡、不能提交到 Git。比喻：你家鑰匙，遺失就換鎖。

### 5.2 最小 Bot：CommandHandler

對 Agent 說（DO NOT CODE）：

> 我要用 python-telegram-bot 建立最小 Bot：
> 1. 讀取 .env 的 TOKEN
> 2. 啟動 polling 模式（本地測試用）
> 3. 實作 /start 與 /note 指令的 handler
> 4. handler 內用 logging 印出接收到什麼
>
> 步驟清單應包括：建立 Application、註冊 handler、run_polling() 的錯誤處理

產出重點：

```python
# main.py
import logging
from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv('TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('歡迎！發送 /note 選擇音名')

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('按鈕功能開發中...')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('note', note))
    
    app.run_polling()
```

> 🔍 **名詞卡：polling（輪詢）**
> 白話：Bot 每隔一段時間去 Telegram 伺服器問「有沒有新訊息給我」。比喻：你每隔 5 秒去信箱看有沒有新信，而不是等郵差按門鈴。

**驗收**：
```bash
python main.py
# 在 Telegram 搜尋你的 Bot 帳號 → /start → 收到訊息
# /note → 收到「按鈕功能開發中...」
```

✅ **預期看到**：
```
$ python main.py
INFO:telegram.ext.Application:Application started

# Telegram 上看到：
> /start
< 歡迎！發送 /note 選擇音名

> /note
< 按鈕功能開發中...
```

🧯 **卡住的話**：
- Token 有誤：重新去 BotFather 確認 token（不是 Bot 帳號名，是長串亂碼）。
- polling 卡住：通常是 Token 錯或網路連不到 Telegram。先檢查 .env，再 `python main.py --verbose` 看詳細日誌。

### 5.3 按鈕互動：InlineKeyboardButton + CallbackQueryHandler ⭐ 一定要親自試的一幕

按鈕的 callback_data 是觸發點，handler 用 pattern 接住。

對 Agent 說：

> DO NOT CODE. 改進 /note handler：
> 1. 建立一排音名按鈕（C, D, E, F, G, A, B）用 InlineKeyboardButton
> 2. 按鈕的 callback_data 帶著音名（例如 'note_C'）
> 3. 實作 CallbackQueryHandler，pattern 用正則 r'note_.*'
> 4. handler 內先 query.answer() 清圈，再回傳「選中 C」的訊息
>
> 步驟清單包括：InlineKeyboardMarkup、按鈕陣列、pattern 正則、callback handler 結構

產出重點：

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(note, callback_data=f'note_{note}') 
         for note in ['C', 'D', 'E', 'F', 'G', 'A', 'B']]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('選擇音名:', reply_markup=keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # ✓ 立刻答，清圈
    
    note_name = query.data.split('_')[1]  # 'note_C' → 'C'
    # 存到 context.user_data
    context.user_data['last_note'] = note_name
    
    await query.edit_message_text(f'你選了 {note_name}')

# 主程式
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('note', note))
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r'note_.*'))
    
    app.run_polling()
```

> 🔍 **名詞卡：InlineKeyboardButton**
> 白話：Telegram 訊息裡的「可點擊按鈕」，點擊時會把 callback_data 送回 Bot。比喻：電影購票網站的「選座位」介面，你點一個座位，它立刻回傳「座位 A12」。
>
> 🔍 **名詞卡：pattern（模式）/ 正則表達式**
> 白話：用來比對文字的「萬用字符」。`r'note_.*'` 的意思是「任何以 note_ 開頭的字串都符合」。比喻：郵件過濾規則「主旨包含『促銷』的都送進垃圾信箱」。

**按鈕點擊的最精彩之處**：看 handler 怎麼做。一上來就先呼叫 `query.answer()`，告訴 Telegram『我收到了』，然後再慢慢產圖。這個『先答、再做』的順序，就是好的 UX 的一半。用戶點按鈕後立刻看到轉圈消失，訊息在更新，而不是卡著等。

**驗收**：點按鈕後立刻看到訊息更新（不轉圈）、訊息改成「你選了 C」。

✅ **預期看到**：Telegram 上：
```
> /note
< 選擇音名:
  [C] [D] [E] [F] [G] [A] [B]

# 點 C 後（無轉圈）
< 你選了 C
```

🧯 **卡住的話**：
- 點按鈕一直轉圈：handler 漏了 `await query.answer()`。快速修法：加上那一行。改好後再測，看修前修後的差異——「看，加一行改變了整個體感」。
- pattern 匹配不到：檢查 callback_data 格式是否真的是 'note_X' 的形式，pattern 正則是否寫對。

> ❓ **想一想**：為什麼一定要先 `query.answer()` 再更新訊息？
>
> **答案**：Telegram 用戶端看到按鈕被點後會轉圈，等著 handler 的回應。如果不呼叫 query.answer()，用戶會以為鈕壞了、一直點，最後逾時關閉。先 answer() 清掉轉圈，再慢慢做事，用戶不會焦慮。

### 5.4 圖片生成：Pillow

Telegram Bot 最常見的進階功能。

對 Agent 說（DO NOT CODE）：

> 寫 utils/image.py，實作 generate_fretboard_image(note_name) 函式：
> 1. 用 Pillow 建立 300x400 的白色背景
> 2. 畫一個 6 弦 12 品的指板網格（線條）
> 3. 標記出 note_name（例如 'C'）在指板上的所有位置（紅點）
> 4. 加上弦號與品號的標籤
> 5. 回傳 PIL Image 物件，由 caller 存成檔案
>
> 步驟清單包括：Image.new()、draw 物件、座標計算、文字標籤

產出重點：

```python
# utils/image.py
from PIL import Image, ImageDraw

def generate_fretboard_image(note_name: str) -> Image.Image:
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 指板參數
    num_strings = 6
    num_frets = 12
    start_x, start_y = 50, 50
    fret_width = (width - 100) / num_frets
    string_height = (height - 100) / (num_strings - 1)
    
    # 畫弦（豎線）
    for fret in range(num_frets + 1):
        x = start_x + fret * fret_width
        draw.line([(x, start_y), (x, start_y + (num_strings - 1) * string_height)], fill='black', width=1)
    
    # 畫弦（橫線）
    for string in range(num_strings):
        y = start_y + string * string_height
        draw.line([(start_x, y), (start_x + num_frets * fret_width, y)], fill='black', width=1)
    
    # 標記音名位置（簡化版：假設 note_name 在特定位置）
    if note_name in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
        circle_x = start_x + 30
        circle_y = start_y + 50
        draw.ellipse(
            [(circle_x - 5, circle_y - 5), (circle_x + 5, circle_y + 5)],
            fill='red'
        )
    
    return img
```

> 🔍 **名詞卡：Pillow / PIL**
> 白話：Python 的「畫圖工具庫」。用程式碼畫線、寫字、標記點位，而不用手打開 Photoshop。比喻：Excel 的「插入圖表」功能——告訴它數據，它自動畫出圖表。

### 5.5 整合到 callback handler

```python
from io import BytesIO
from telegram import InputMediaPhoto
from utils.image import generate_fretboard_image

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # ✓ 先清圈
    
    note_name = query.data.split('_')[1]
    context.user_data['last_note'] = note_name
    
    # 產生圖片
    img = generate_fretboard_image(note_name)
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    
    # 回傳圖片
    await query.edit_message_media(
        media=InputMediaPhoto(media=bio, caption=f'音名: {note_name}')
    )
```

**驗收**：點按鈕後看到指板圖片、圖片上標示了選中的音名。

✅ **預期看到**：Telegram 上看到一張指板圖，上面有紅點標記音名位置。

🧯 **卡住的話**：
- 圖片顯示失敗：BytesIO 沒 `seek(0)` 或格式錯誤。快速修法：確認 `bio.seek(0)` 在 save 之後；確認圖片格式是 PNG 或 JPG。
- 訊息仍是文字沒變成圖片：`edit_message_media` 和文字訊息的操作不同，要用 `InputMediaPhoto` 包裝。

---

## 6. 階段五：部署與生產化

### 6.1 Polling vs Webhook

| 特性 | Polling | Webhook |
|---|---|---|
| 工作原理 | Bot 定期拉取更新 | Telegram 主動推送更新 |
| 部署 | 本地或任何伺服器 | 需要公開 HTTPS URL |
| 延遲 | 高（取決於輪詢間隔） | 低（立刻推送） |
| 成本 | 低（無伺服器） | 需要伺服器 + SSL 憑證 |
| 本地開發 | ✓ 推薦 | ✗ 困難 |
| 生產環境 | 可用（低流量） | ✓ 推薦（高流量） |

**互斥性**（重點）：啟用 polling 與 webhook 會導致 API 重複返回更新，應該只用其中一種。

> 🔍 **名詞卡：webhook**
> 白話：你在 Telegram 設定一個「回調 URL」，每當有訊息時 Telegram 自動向你的伺服器 POST 一個請求。比喻：訂閱制——不是你每天去雜誌社問「新號出了嗎」，而是雜誌社一出新號就寄給訂戶。

**polling 和 webhook 的選擇**：polling 和 webhook 是同一件事的兩種做法——都是『怎麼把新訊息送給 Bot』。polling 像你每隔 5 秒去信箱看一次，webhook 像郵差直接按門鈴。本地開發用 polling 快速測試；正式上線用 webhook 才不會浪費資源。但千萬不能同時用兩個，會搶訊息。

### 6.2 本地開發：Polling

已在 5.2 實作。執行 `python main.py` 即可。

### 6.3 部署到 fly.io（Webhook）

對 Agent 說：

> DO NOT CODE. 我要把 Telegram Bot 部署到 fly.io 用 webhook 模式，步驟包括：
> 1. 在 Fly.io 建立帳號與 app
> 2. 在 main.py 加 webhook server 端點（用 Quart 或 FastAPI）
> 3. 建立 Dockerfile 與 fly.toml
> 4. 用 flyctl deploy 部署
> 5. 設定 Telegram webhook URL 為部署後的公開 URL
>
> 產出步驟清單

產出重點（簡化版，用 Quart）：

```python
# main.py with webhook
from quart import Quart, request

app_quart = Quart(__name__)

@app_quart.route('/webhook', methods=['POST'])
async def webhook():
    json_data = await request.get_json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    return 'ok'

# 啟動邏輯
async def main():
    await application.bot.set_webhook_url(f'https://{FLY_APP_NAME}.fly.dev/webhook')
    await app_quart.run(host='0.0.0.0', port=8080)
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
# 部署
flyctl launch              # 建立 fly.toml
flyctl secrets set TOKEN=<your_token>
flyctl deploy              # 部署
flyctl logs                # 看日誌
```

✅ **預期看到**：
```
$ flyctl deploy
Deploying app...
...
App deployed successfully! https://your-app.fly.dev

$ curl https://your-app.fly.dev/webhook -X POST
200 OK
```

---

## 7. 情境演練：點按鈕產生指板圖片

原文情境完整對應。

**場景**：使用者發送 `/note`，想用按鈕選音名而不是手動輸入文字。

| 步驟 | 怎麼做 | 會看到什麼 |
|---|---|---|
| 1 | 用 InlineKeyboardButton 產生一排音名按鈕，帶 callback_data | ✓ 點擊任一按鈕，Bot 回傳標示該音名所有位置的圖片 |
| 2 | CallbackQueryHandler 用 pattern 接住點擊事件 | ✓ 沒呼叫 query.answer() 會讓用戶端一直轉圈逾時 |
| 3 | handler 內先呼叫 query.answer() 再回傳指板圖片 | ✓ context.user_data 記住使用者上一次選擇的音名 |

**程式碼流程**：

1. `/note` → note handler 建立按鈕 → `InlineKeyboardButton('C', callback_data='note_C')`
2. 使用者點 C → Telegram 送 callback_query
3. button_callback 收到 → `query.answer()` 立刻清圈 → 產生圖片 → `query.edit_message_media()` 更新訊息
4. 訊息變成指板圖片，使用者體感速度快（不轉圈）

> ❓ **想一想**：假設畫指板圖片要花 2 秒，不加 query.answer() 和加 query.answer() 時，使用者的體感差異在哪裡？
>
> **答案**：不加時，用戶要等 2 秒轉圈才看到圖；加了時，轉圈立刻消失，再等 2 秒看圖，但圖一出現就停止等待。前者感覺「我被卡住了」，後者感覺「機器在工作，我不用糾結」。

---

## 8. 驗收清單

### CLI 部分

- [ ] npm link 成功，`scaffold --help` 有反應
- [ ] `scaffold init my-app` 產生資料夾並建立檔案
- [ ] 產生的 package.json 名稱是 `my-app` 而非模板名稱
- [ ] `scaffold init existing-folder; echo $?` → 1（資料夾已存在，exit code 正確）
- [ ] `scaffold init new-folder; echo $?` → 0（成功，exit code 正確）
- [ ] 使用者按 Ctrl+C 取消，exit code 是 0（不算錯誤）
- [ ] npm publish 成功，npm registry 可查到
- [ ] 在新資料夾執行 `npx create-project-scaffold init test-app` 成功

### Bot 部分

- [ ] `python main.py` 啟動，Telegram Bot 有反應
- [ ] `/start` 指令正常回應
- [ ] `/note` 顯示一排音名按鈕
- [ ] 點按鈕後立刻看到訊息更新（不轉圈）
- [ ] 訊息變成指板圖片，圖片上標示了選中的音名
- [ ] 用兩個帳號各點不同按鈕，context.user_data 各自獨立（不互相看到）
- [ ] .env 已加 .gitignore，不會提交
- [ ] Fly.io 部署成功，機器人在生產環境有反應

---

## 9. 常見坑排錯速查表

根據原文表格，加上擴充。

| 問題 | 常見原因 | 解法 |
|---|---|---|
| **npm link 權限錯誤** | 全域安裝目錄權限給管理者 | 改用 nvm，不要用 sudo；`nvm install 20` → `nvm use 20` |
| **scaffold 指令找不到** | package.json 的 bin 欄位錯誤 或 shebang 缺少 | 檢查 bin.scaffold 對應 ./index.js；index.js 最上面加 `#!/usr/bin/env node` |
| **Exit code 永遠是 0** | 漏了 process.exit() 或 exitCode 設定 | 失敗路徑明確設 `process.exitCode = 1`；成功路徑設 `process.exit(0)` |
| **按鈕點了一直轉圈** | handler 漏了 query.answer() | callback handler 開頭先呼叫 `await query.answer()`；不管後續邏輯多耗時，先答 |
| **Bot 部署後沒反應** | polling 與 webhook 同時啟用 | 統一只用 `run_polling()`（本地）或完整 webhook server（生產），勿混用 |
| **Token 外洩** | .env 加 gitignore 前已提交 | 立刻到 BotFather 撤銷重發；commit 歷史改不了，新 token 保護好 |
| **圖片顯示失敗** | BytesIO 沒 seek(0) 或格式錯誤 | 產生圖片後一定 `bio.seek(0)`；Telegram 支援 PNG、JPG，確認格式 |
| **複製模板後文件亂碼** | 字串替換沒用 utf-8 | readFileSync/writeFileSync 加 `'utf-8'` 編碼 |
| **Webhook 部署後還是 polling** | 程式碼內同時有 run_polling 與 webhook | 刪掉 run_polling()；改成 webhook server + application.run() |

---

## 10. 帶走的三句話

如果整份教學只能記住三件事，就這三句：

1. **CLI 核心體驗來自参數解析、互動提問、正確 exit code 三者缺一不可**——漏了 exit code 會讓 CI 判斷錯誤；npm link 是發佈前用真實指令名稱測試的最後一關，遇權限問題改用 nvm。exit code 不是選配項，是必修課。

2. **DO NOT CODE 逼它先計畫再寫程式，用 5 分鐘產計畫省 3 小時返工**——結構化反饋循環六步驟（覆述→計畫→審核→實作→驗收→回看）顯著降低複雜任務的遺漏；Checkpoints 不能取代 Git，每個邏輯步驟留一個 commit。計畫不是官僚程序，是打仗前看一次地圖。

3. **Callback handler 一定要呼叫 query.answer()，否則按鈕一直轉圈；Telegram Bot 的 run_polling 與 webhook 互斥，部署時只能啟用一種**——體感速度是產品體驗的關鍵，先答再做是 Bot 開發的鐵律。轉圈三秒以上用戶就開始懷疑機器壞了；互斥選擇錯誤則會導致訊息重複或遺漏。

**最後一件事**：這份教學本質上教的不是『怎麼寫 CLI』或『怎麼寫 Bot』，而是『怎麼在 AI 時代讓 Agent 替你把事情做好』。核心就三個：先計畫、守邊界、驗每個步驟。這套邏輯不只適用於 CLI 和 Bot，適用於任何你要交給 Agent 的工作。記住這個流程，下一次碰到陌生的工具，不用怕——先問 Agent 計畫，再驗證，再動手。這就是我們這個時代最重要的技能。
