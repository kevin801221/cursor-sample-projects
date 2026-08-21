# Claude Code、Codex、Antigravity、Gemini CLI 可攜性說明

最後核對：2026-08-21。

## 結論

這 17 個專案的**核心程式碼、測試、資料、`README.md`、`walkthrough.md` 與 `demo.sh` 都可以共用**，不需要複製成四套程式碼。

需要分平台處理的是 agent 的外掛層：專案指令、skills、slash commands、hooks、MCP 設定、權限與審批流程。最穩的做法是「一套核心專案 + 各平台的薄轉接層」，而不是維護四個會逐漸分岔的 fork。

## 哪些可以直接共用

- 應用程式原始碼、測試與 lockfile
- `demo.sh` 與不依賴特定 agent 的檢查腳本
- MCP server 本身；MCP 是共通協議，但每個 client 的註冊設定位置不同
- 以開放 Agent Skills 格式撰寫的 `SKILL.md` 主體
- 課程需求、驗收條件、排錯流程與離線 fallback

## 哪些需要平台轉接

- **Claude Code**：常駐指令用 `CLAUDE.md`，skills 放 `.claude/skills/<name>/SKILL.md`，MCP 通常用專案根目錄 `.mcp.json`，hooks 放 Claude Code settings。Claude Code 官方也明確說 skills 採 Agent Skills 開放標準，但另有自己的 invocation 與 subagent 擴充。[Claude Code skills](https://code.claude.com/docs/en/slash-commands) · [Claude Code extension overview](https://code.claude.com/docs/en/features-overview)
- **Codex**：常駐指令用 `AGENTS.md`，repo skills 放 `.agents/skills/<name>/SKILL.md`；MCP、hooks 或 plugin 依 Codex 的設定與發佈方式接入。官方文件確認 Codex 會分層讀取 `AGENTS.md`，且 skills 使用開放 Agent Skills 標準。[OpenAI `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md) · [OpenAI skills](https://developers.openai.com/codex/skills)
- **Gemini CLI**：常駐指令用 `GEMINI.md`，skills 可放 `.gemini/skills/<name>/SKILL.md`；MCP、commands、hooks 與 context 也能包成 extension。[Gemini CLI extensions](https://geminicli.com/docs/extensions/writing-extensions/) · [Gemini CLI skills](https://geminicli.com/docs/cli/tutorials/skills-getting-started/)
- **Antigravity**：目前官方流程可從 `.agents/skills/<name>/SKILL.md` 載入本地 skills，也支援 local／remote MCP；IDE、CLI 的設定與工作流仍要用 Antigravity 的格式驗證。[Antigravity skills](https://codelabs.developers.google.com/antigravity/how-to-create-agent-skills-for-antigravity-cli) · [Antigravity MCP](https://codelabs.developers.google.com/getting-started-google-antigravity)

## 課程版的完成定義

某個專案只有同時通過以下條件，才能標成該平台的「課堂可用版」：

1. 從該專案指定目錄啟動 agent，能載入正確的專案規則或 skill。
2. README 的安裝指令可以在乾淨環境執行，且不依賴老師電腦的絕對路徑。
3. 不需要 MCP 的核心 demo 可先離線完成；需要 MCP 時，連線狀態與 fallback 都有明確提示。
4. 專案自己的 lint、build、test 與 smoke test 全部通過。
5. 至少實際用該平台跑過一次指定 prompt，保存輸入、預期結果與失敗救援步驟。
6. API key、帳號、Docker、瀏覽器或手機模擬器等外部條件，必須在課前檢查，不把「agent 支援」誤當成「環境一定可用」。

## 授課建議

目前這份教材仍以 Cursor walkthrough 為主。移植時先挑 1 個純前端專案、1 個 Python 專案、1 個 MCP 專案做四平台 smoke test，確認轉接模板後再批次套到其他專案。這能把平台差異集中在少量設定檔，也保留所有專案共用同一套可驗證的程式碼。

「可移植」不等於「同一個 prompt 在四個 agent 會產生逐字相同結果」。課堂應保證的是固定版本、固定輸入、固定驗收與可用的救援路徑，而不是模型輸出的完全一致。
