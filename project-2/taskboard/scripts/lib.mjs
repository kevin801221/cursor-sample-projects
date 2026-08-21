// scripts/lib.mjs —— demo 腳本共用的小工具（讀 .env.local、連本地 Postgres、上色）
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// 本地 Supabase 的 Postgres 連線字串（npx supabase start 固定用 54322）
export const LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres";

/** 讀 .env.local 並塞進 process.env（沒有依賴，12 行就夠了） */
export function loadEnv() {
  const file = path.join(ROOT, ".env.local");
  if (!existsSync(file)) {
    die(`找不到 ${file}\n救援：先跑 ./demo.sh 0（會自動啟動 Supabase 並產生 .env.local）`);
  }
  for (const line of readFileSync(file, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)$/);
    // 行尾的 `   # 註解` 要拿掉（跟 dotenv 一樣的規則）——
    // 忘了拿掉的話，註解會被當成金鑰的一部分塞進 HTTP header，
    // 中文字直接炸成 "Cannot convert argument to a ByteString"。
    if (m) process.env[m[1]] ??= m[2].replace(/\s+#.*$/, "").trim().replace(/^["']|["']$/g, "");
  }
  const need = ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"];
  for (const k of need) if (!process.env[k]) die(`.env.local 缺少 ${k}`);
  return {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    serviceKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  };
}

/** 連上本地 Postgres 跑 SQL。回傳一個已連線的 pg client。 */
export async function connectDb() {
  const { default: pg } = await import("pg");
  const client = new pg.Client({ connectionString: LOCAL_DB_URL });
  try {
    await client.connect();
  } catch (e) {
    die(`連不上本地 Supabase 資料庫（${LOCAL_DB_URL}）\n原因：${e.message}\n救援：npx supabase start（或 ./demo.sh 0）`);
  }
  return client;
}

export function readSql(relPath) {
  return readFileSync(path.join(ROOT, relPath), "utf8");
}

// ── 上色（課堂投影要看得清楚）────────────────────────────────
const on = process.stdout.isTTY || process.env.FORCE_COLOR === "1";
const wrap = (code) => (s) => (on ? `\x1b[${code}m${s}\x1b[0m` : s);
export const c = {
  red: wrap("1;31"),
  green: wrap("1;32"),
  yellow: wrap("1;33"),
  blue: wrap("1;36"),
  gray: wrap("90"),
  bold: wrap("1"),
  redbg: wrap("1;37;41"),
  greenbg: wrap("1;37;42"),
};

export function die(msg) {
  console.error("\n" + c.red("✗ " + msg) + "\n");
  process.exit(1);
}
