#!/usr/bin/env node
/**
 * MCP Inspector 教學版 —— 直接用 stdio 跟 server 講 JSON-RPC，把往返的紙條印在終端機上。
 *
 * 為什麼不用官方 GUI Inspector？因為投影片上看不到「協定長什麼樣」。
 * 這支腳本做的事跟 Inspector 一模一樣：spawn server → 送 JSON-RPC → 收 JSON-RPC，
 * 差別只在它把每一張紙條原封不動印出來給學生看。
 *
 * 用法：
 *   node scripts/inspect.mjs                 跑全部步驟
 *   node scripts/inspect.mjs search zod      只跑指定步驟
 *   node scripts/inspect.mjs --list          列出所有步驟
 *   MCP_INSPECT_FULL=1 node scripts/inspect.mjs   不截斷長回應
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SERVER = path.join(ROOT, "dist", "index.js");

const useColor = !process.env.NO_COLOR;
const c = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const cyan = (s) => c("36", s);
const green = (s) => c("32", s);
const red = (s) => c("31;1", s);
const yellow = (s) => c("33", s);
const dim = (s) => c("2", s);
const bold = (s) => c("1", s);

// ── 步驟定義：一個 key = 課堂上的一個小節 ────────────────────────
const STEPS = {
  tools: {
    why: "問 server：你有哪些工具？（Cursor 開機時就是問這一句）",
    calls: [["tools/list", {}]],
  },
  search: {
    why: "呼叫 search_knowledge_base：回傳精簡欄位 + 200 字摘要（鐵律 2）",
    calls: [
      ["tools/call", { name: "search_knowledge_base", arguments: { query: "VPN", limit: 3 } }],
      [
        "tools/call",
        { name: "search_knowledge_base", arguments: { query: "密碼", tag: "security", limit: 2 } },
      ],
    ],
  },
  page: {
    why: "分頁：同一個 query 用 offset 翻第二頁，total 不變、內容不重複",
    calls: [
      ["tools/call", { name: "search_knowledge_base", arguments: { query: "工單", limit: 2, offset: 0 } }],
      ["tools/call", { name: "search_knowledge_base", arguments: { query: "工單", limit: 2, offset: 2 } }],
    ],
  },
  zod: {
    why: "壞紙條：空的 query、limit=100 —— Zod 擋下來並回人話",
    calls: [
      ["tools/call", { name: "search_knowledge_base", arguments: { query: "" } }],
      ["tools/call", { name: "search_knowledge_base", arguments: { query: "VPN", limit: 100 } }],
      ["tools/call", { name: "create_ticket", arguments: { title: "沒寫描述", priority: "urgent" } }],
    ],
  },
  ticket: {
    why: "呼叫 create_ticket：有副作用的動作，成功會回 TKT-XXXX",
    calls: [
      [
        "tools/call",
        {
          name: "create_ticket",
          arguments: {
            title: "VPN 連線逾時（知識庫查無解法）",
            description: "已查過 KB 關鍵字 VPN／逾時，改 TCP 模式仍然斷線。附件為客戶端 log。",
            priority: "medium",
          },
        },
      ],
    ],
  },
  timeout: {
    why: "逾時保護：外部 API 不回應時，AbortController 在 8 秒後中止並回人話（配合 DEMO_TICKET_DELAY_MS）",
    calls: [
      [
        "tools/call",
        {
          name: "create_ticket",
          arguments: {
            title: "測試：Ticket API 沒有回應",
            description: "示範 AbortController 逾時保護。",
            priority: "high",
          },
        },
      ],
    ],
  },
  fail: {
    why: "外部 API 回 5xx：工具不能裝沒事，要說清楚工單沒建成（配合 DEMO_TICKET_FAIL=1）",
    calls: [
      [
        "tools/call",
        {
          name: "create_ticket",
          arguments: {
            title: "測試：Ticket API 故障",
            description: "示範 API 回 503 時的錯誤訊息。",
            priority: "high",
          },
        },
      ],
    ],
  },
  resources: {
    why: "Resource tickets://all：唯讀清單，剛剛建立的工單會出現在最後一筆",
    calls: [
      ["resources/list", {}],
      ["resources/read", { uri: "tickets://all" }],
    ],
  },
  prompts: {
    why: "Prompt triage_ticket：把「先查後開票」的決策流程包成一鍵套用",
    calls: [
      ["prompts/list", {}],
      [
        "prompts/get",
        { name: "triage_ticket", arguments: { complaint: "VPN 一直斷線，改 TCP 也沒用", priority: "medium" } },
      ],
    ],
  },
};

const allKeys = Object.keys(STEPS);
// 不帶參數時跑的預設清單（timeout / fail 要等 8 秒或刻意失敗，只在指定時才跑）
const order = ["tools", "search", "page", "zod", "ticket", "resources", "prompts"];

const args = process.argv.slice(2);
if (args.includes("--list")) {
  process.stdout.write(`${bold("可用步驟：")}\n`);
  for (const k of allKeys) process.stdout.write(`  ${cyan(k.padEnd(10))} ${STEPS[k].why}\n`);
  process.exit(0);
}
const selected = args.filter((a) => allKeys.includes(a));
const steps = selected.length ? selected : order;
const unknown = args.filter((a) => !allKeys.includes(a));
if (unknown.length) {
  process.stdout.write(red(`不認得的步驟：${unknown.join(", ")}（用 --list 看可用步驟）\n`));
  process.exit(1);
}

// ── 起 server 子行程 ─────────────────────────────────────────
const child = spawn(process.execPath, [SERVER], { stdio: ["pipe", "pipe", "pipe"] });
const pending = new Map();
const pollution = [];
let buffer = "";
let nextId = 1;

child.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  let idx;
  while ((idx = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, idx).trim();
    buffer = buffer.slice(idx + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch (e) {
      // stdout 出現非 JSON 的東西 = 協定被污染（鐵律 3）
      pollution.push(line);
      process.stdout.write(
        `\n${red("✗ stdout 出現非 JSON-RPC 的內容，協定已被污染：")} ${JSON.stringify(line)}\n`,
      );
      continue;
    }
    const waiter = pending.get(msg.id);
    if (waiter) {
      pending.delete(msg.id);
      waiter(msg);
    }
  }
});

child.stderr.on("data", (chunk) => {
  for (const line of chunk.toString().split("\n")) {
    if (line.trim()) process.stdout.write(dim(`  [server stderr] ${line}\n`));
  }
});

function send(method, params) {
  const id = nextId++;
  const request = { jsonrpc: "2.0", id, method, params };
  const started = Date.now();
  const done = new Promise((resolve) => pending.set(id, resolve));
  child.stdin.write(`${JSON.stringify(request)}\n`);
  return { id, request, done, started };
}

function notify(method, params) {
  child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method, params })}\n`);
}

function pretty(obj) {
  const text = JSON.stringify(obj, null, 2);
  const lines = text.split("\n");
  const max = process.env.MCP_INSPECT_FULL === "1" ? Infinity : 34;
  const shown = lines.slice(0, max).map((l) => `  ${l}`);
  if (lines.length > max) shown.push(dim(`  … 還有 ${lines.length - max} 行（MCP_INSPECT_FULL=1 看全部）`));
  return shown.join("\n");
}

/** 把回應裡被字串化的 text 內容挖出來——JSON-RPC 原文太難讀，投影時需要這一段。 */
function extractTexts(response) {
  const r = response.result;
  if (!r) return [];
  if (Array.isArray(r.content)) return r.content.filter((c) => c.type === "text").map((c) => c.text);
  if (Array.isArray(r.contents)) return r.contents.map((c) => c.text).filter(Boolean);
  if (Array.isArray(r.messages)) return r.messages.map((m) => m.content?.text).filter(Boolean);
  return [];
}

function showDecoded(response) {
  const texts = extractTexts(response);
  if (texts.length === 0) return;
  process.stdout.write(`${dim("  ── 解出來的內容（把上面那串跳脫字元還原）──")}\n`);
  for (const text of texts) {
    let body;
    try {
      body = JSON.stringify(JSON.parse(text), null, 2);
    } catch {
      body = text;
    }
    for (const line of body.split("\n")) process.stdout.write(`  ${line}\n`);
  }
}

async function call(method, params, note) {
  const { request, done, started } = send(method, params);
  process.stdout.write(`\n${cyan("──▶ 送出 REQUEST")} ${dim(`(寫進 server 的 stdin)`)}\n`);
  process.stdout.write(`${pretty(request)}\n`);
  const response = await done;
  const ms = Date.now() - started;
  const isError = response.result?.isError || response.error;
  const tag = isError ? red("◀── 收到 RESPONSE（工具回報失敗）") : green("◀── 收到 RESPONSE");
  process.stdout.write(`${tag} ${dim(`(從 server 的 stdout 讀回，${ms} ms)`)}\n`);
  process.stdout.write(`${pretty(response)}\n`);
  showDecoded(response);
  if (note) process.stdout.write(`${yellow(`  👉 ${note}`)}\n`);
  return response;
}

function banner(title, why) {
  const bar = "═".repeat(64);
  process.stdout.write(`\n${bold(bar)}\n${bold(` ${title}`)}\n ${why}\n${bold(bar)}\n`);
}

async function main() {
  banner("步驟 0 · initialize —— 協定握手", "client 自報家門，server 回覆它有哪些能力");
  const init = await call(
    "initialize",
    {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "inspect.mjs（課堂教學版 Inspector）", version: "1.0.0" },
    },
    "握手成功後才可以呼叫 tools／resources／prompts。Cursor 側欄的 Connected 就是這一步的結果。",
  );
  notify("notifications/initialized", {});

  const serverInfo = init.result?.serverInfo;
  if (serverInfo) {
    process.stdout.write(`\n  ${green("✔")} 已連上 ${bold(`${serverInfo.name} v${serverInfo.version}`)}\n`);
  }

  for (const key of steps) {
    const step = STEPS[key];
    banner(`步驟 · ${key}`, step.why);
    for (const [method, params] of step.calls) {
      await call(method, params);
    }
  }

  const bar = "─".repeat(64);
  process.stdout.write(`\n${bar}\n`);
  if (pollution.length === 0) {
    process.stdout.write(
      `${green("✔ 全部回應都是合法 JSON —— stdout 乾淨，協定沒有被污染（鐵律 3）")}\n`,
    );
  } else {
    process.stdout.write(
      `${red(`✗ 有 ${pollution.length} 行垃圾混進 stdout —— Cursor 會在這裡斷線。去 grep console.log！`)}\n`,
    );
  }
  child.stdin.end();
  child.kill();
  process.exit(pollution.length === 0 ? 0 : 1);
}

const timeout = setTimeout(() => {
  process.stdout.write(red("\n✗ 超過 30 秒沒有回應，server 可能卡住或崩潰了。先跑 npm run build。\n"));
  child.kill();
  process.exit(1);
}, 30_000);
timeout.unref();

child.on("exit", (code) => {
  if (pending.size > 0) {
    process.stdout.write(red(`\n✗ server 提早結束（exit code ${code}），還有 ${pending.size} 個請求沒回應。\n`));
    process.exit(1);
  }
});

main().catch((error) => {
  process.stdout.write(red(`\n✗ inspect 失敗：${error.message}\n`));
  child.kill();
  process.exit(1);
});
