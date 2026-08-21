# Company Knowledge & Tickets MCP Server

> Cursor 課程 Project 10（第 31 章）：自建 MCP Server。
> 一句話：**自己寫工具讓 Agent 呼叫，而不是只靠內建能力**——Agent 不只能看、還能主動觸發你設計的動作。

## 專案規格

| | |
|---|---|
| **最終成果** | 公司知識庫搜尋、工單建立與查詢的 Tools，加上工單清單的 Resource；透過 MCP Protocol 暴露給 Cursor |
| **技術棧** | Node.js 20+、TypeScript、@modelcontextprotocol/sdk、Zod |
| **預估時間** | 5–7 小時，先做 stdio 版本再升級遠端 HTTP |
| **前置需求** | 熟悉 TypeScript 基本語法、Cursor 3.11 以上版本 |

## 這個 MCP Server 提供什麼

MCP 三大能力，各司其職：

| 能力 | 用途 | 本專案實作 |
|---|---|---|
| **Tools** | 模型主動呼叫、會有副作用的動作 | `search_knowledge_base`、`create_ticket`：搜尋與建立工單 |
| **Resources** | 模型可讀取的靜態資料 | `tickets://all`：工單清單 JSON，Cursor 侧欄可查看 |
| **Prompts** | 預先寫好的多步驟指引 | `triage_ticket`：決策流程（先查知識庫再決定要不要開票） |

**關鍵差異**：Tools 是「Agent 決定什麼時候呼叫」（事件驅動），Resources 是「Agent 主動探索」（靜態查閱），Prompts 是「人選擇套用」（命令列表）。

## 架構

```
Cursor（MCP Client）
  ↕ JSON-RPC via stdio
MCP Server（Node.js + TypeScript）
  ↕ 檔案系統 + 外部 API
知識庫（data/knowledge.json）、工單庫（data/tickets.json）、外部 Ticket API
```

**設計重點**：
- stdout 唯一合法輸出是 JSON-RPC 訊息；所有除錯訊息必須改成 `console.error` 寫 stderr，否則協定直接壞掉
- Zod 驗證參數，拒絕格式不符的請求，模型無法隨意竄改
- 外部 API 呼叫必須加逾時控制（AbortController），讓模型知道發生了什麼而不是卡住

## 五階段開發流程

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 初始化 | npm init 裝 SDK 與 Zod；建 src/ 與 data/ 資料夾 | 專案結構就緒，無 npm error |
| 2. 寫 Tools | 用 Zod 定義 `search_knowledge_base` 與 `create_ticket` 參數、註冊工具 | MCP Inspector 能呼叫兩個工具 |
| 3. 寫 Resources | 讀取 JSON 檔暴露 `tickets://all` 資源 | `tickets://all` 可在 Cursor 讀取 |
| 4. 測試 | 跑 MCP Inspector 逐一測試 Tools 與 Resources | 全部工具回應正常、無 JSON 解析錯誤 |
| 5. 接進 Cursor | 寫 `.cursor/mcp.json`，用絕對路徑註冊 server | Cursor 側欄顯示 Connected |

## 專案結構

```
company-mcp-server/
├── src/
│   ├── index.ts                 # 主程式：server 初始化、工具註冊
│   ├── tools/
│   │   ├── search.ts            # search_knowledge_base 實作（Zod + 分頁）
│   │   └── tickets.ts           # create_ticket 實作（AbortController 逾時）
│   └── resources/
│       └── tickets-resource.ts  # tickets://all 資源提供者
├── data/
│   ├── knowledge.json           # 知識庫（tag、content）
│   └── tickets.json             # 工單庫（持久化）
├── package.json
├── tsconfig.json
└── walkthrough.md               # 完整逐步教學
```

## 三條鐵律（本課核心）

1. **先驗後接**——用 MCP Inspector 逐工具測好再接進 Cursor，否則出問題時分不清是誰的錯。
2. **回傳精簡、錯誤可讀**——一工具回 240KB 原始 JSON 縮到 8KB 精選欄位，品質反而變好；stack trace 沒人看，自然語言說明怎麼處理才有用。
3. **絕不 console.log**——stdio server 唯一合法的輸出通道是 stdout 上的 JSON-RPC 訊息，任何混進去的文字會讓 Cursor 端 JSON 解析失敗、server 直接斷線。

## 快速開始

```bash
# 初始化與安裝
npm install
npm run build

# 用 MCP Inspector 測試（Cursor 內建或獨立運行）
npx mcp-inspector

# 整合進 Cursor：編輯 ~/.cursor/mcp.json（macOS/Linux）或 %APPDATA%\cursor\mcp.json（Windows）
```

### Cursor 設定範例

編輯 Cursor Settings → Features → MCP 或直接編輯 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "company-knowledge": {
      "command": "node",
      "args": ["/absolute/path/to/project-10/dist/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "https://api.company.com",
        "KNOWLEDGE_API_KEY": "<your-api-key>"
      }
    }
  }
}
```

**重點**：
- `args` 必須是**絕對路徑**，相對路徑 Cursor 會解析不了
- 敏感資訊（API Key）存在 `env` 欄位，圖形介面 Cursor 才能正確讀取
- 本地測試可用 `ts-node` 直接跑 `src/index.ts`，正式環境改成編譯後的 `dist/`

重啟 Cursor 後側欄應顯示「company-knowledge Connected」，即代表接通。

---

完整建置步驟、反模式教學、五個開發階段的逐步指南，見 **[walkthrough.md](./walkthrough.md)**。
