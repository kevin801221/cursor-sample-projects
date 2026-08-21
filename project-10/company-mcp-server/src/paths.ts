/**
 * 資料檔的絕對路徑解析。
 *
 * 為什麼不直接寫 "data/knowledge.json"？
 * 相對路徑是相對「行程的工作目錄（cwd）」，而 Cursor 啟動 MCP server 時
 * 的 cwd 幾乎不會是你的專案資料夾——結果就是 ENOENT 找不到檔案。
 * 這跟 .cursor/mcp.json 的 args 必須用絕對路徑，是同一條規則。
 */
import { fileURLToPath } from "node:url";
import * as path from "node:path";

// dist/paths.js → dist → 專案根目錄
const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function dataPath(fileName: string): string {
  return path.join(projectRoot, "data", fileName);
}
