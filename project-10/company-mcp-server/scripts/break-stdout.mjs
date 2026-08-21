#!/usr/bin/env node
/**
 * 反面教材：console.log 如何一行毀掉整個 MCP server（鐵律 3）。
 *
 * 同一支 server 跑兩次，只差一個環境變數：
 *   MCP_DEMO_BREAK_STDOUT=1 → 啟動時往 stdout 寫一行 "[debug] server starting..."
 *                             （就是 console.log 做的事）
 *   不設                    → 除錯訊息走 stderr
 *
 * 兩次都送同一個 initialize 請求，然後把 server stdout 的第一行「原文」印出來，
 * 當場 JSON.parse 給學生看：壞的那次會爆，好的那次乾乾淨淨。
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SERVER = path.join(ROOT, "dist", "index.js");

const useColor = !process.env.NO_COLOR;
const c = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const red = (s) => c("31;1", s);
const green = (s) => c("32;1", s);
const dim = (s) => c("2", s);
const bold = (s) => c("1", s);

const INIT = {
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "break-stdout.mjs", version: "1.0.0" },
  },
};

/** 起一個 server、送一個 initialize、把 stdout 的第一行原文帶回來。 */
function probe(env) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [SERVER], {
      stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env, ...env },
    });
    let out = "";
    let err = "";
    const finish = () => {
      child.kill();
      const firstLine = out.split("\n").find((l) => l.trim().length > 0) ?? "(沒有輸出)";
      resolve({ firstLine, stderr: err.trim() });
    };
    const timer = setTimeout(finish, 3000);
    child.stdout.on("data", (chunk) => {
      out += chunk.toString();
      if (out.includes("\n")) {
        clearTimeout(timer);
        setTimeout(finish, 150); // 多等一下，讓後面的 JSON 也一起收進來
      }
    });
    child.stderr.on("data", (chunk) => {
      err += chunk.toString();
    });
    child.stdin.write(`${JSON.stringify(INIT)}\n`);
  });
}

function report(title, subtitle, { firstLine, stderr }, expectBroken) {
  const bar = "═".repeat(64);
  process.stdout.write(`\n${bold(bar)}\n${bold(` ${title}`)}\n ${subtitle}\n${bold(bar)}\n`);
  process.stdout.write(`\n  server stdout 的第一行原文：\n    ${JSON.stringify(firstLine)}\n`);
  try {
    const parsed = JSON.parse(firstLine);
    process.stdout.write(`\n  ${green("JSON.parse 成功 ✔")}`);
    process.stdout.write(
      ` 這是一則合法的 JSON-RPC 回應（serverInfo = ${parsed.result?.serverInfo?.name}）\n`,
    );
    if (expectBroken) process.stdout.write(red("\n  （意外：這次應該要壞掉才對）\n"));
    else
      process.stdout.write(
        `  ${green("→ Cursor 側欄顯示 Connected，工具全部可用。")}\n`,
      );
  } catch (e) {
    process.stdout.write(`\n  ${red("JSON.parse 失敗 ✗")} ${e.message}\n`);
    process.stdout.write(
      `  ${red("→ Cursor 端會直接判定這個 server 壞了：Failed to parse message / server disconnected。")}\n`,
    );
    process.stdout.write(
      `  ${red("→ 注意：後面那些 JSON 回應其實都送出來了，但通道已經髒了，client 不會再信任它。")}\n`,
    );
  }
  if (stderr) process.stdout.write(`\n  ${dim(`server stderr（安全的除錯通道）：${stderr}`)}\n`);
}

const broken = await probe({ MCP_DEMO_BREAK_STDOUT: "1" });
report(
  "【壞掉的版本】server 裡多了一行 console.log",
  'MCP_DEMO_BREAK_STDOUT=1 —— 啟動時往 stdout 印了 "[debug] server starting..."',
  broken,
  true,
);

const fixed = await probe({ MCP_DEMO_BREAK_STDOUT: "0" });
report("【修好的版本】同一支 server，除錯訊息改走 stderr", "只差那一行 console.log 被拿掉", fixed, false);

const bar = "─".repeat(64);
process.stdout.write(`\n${bar}\n`);
process.stdout.write(`${bold("結論：")}stdout 是紙條通道，不是聊天室。除錯訊息一律 console.error。\n`);
process.stdout.write(`檢查方式：${bold("grep -rn 'console.log' src/")} —— 一行都不該有。\n`);
