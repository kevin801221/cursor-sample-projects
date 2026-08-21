// scripts/env-init.mjs —— 從本地 Supabase 讀出網址與金鑰，寫成 .env.local。
// 課堂上不用手貼金鑰（貼錯是最常見的翻車點之一）。
import { execFileSync } from "node:child_process";
import { writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { ROOT, c, die } from "./lib.mjs";

let out = "";
try {
  out = execFileSync("npx", ["supabase", "status", "-o", "env"], {
    cwd: ROOT,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
} catch {
  die("本地 Supabase 沒有在跑。\n救援：npx supabase start（第一次會下載映像檔，5–10 分鐘）");
}

const pick = (key) => out.match(new RegExp(`^${key}="?([^"\\n]+)"?$`, "m"))?.[1];
const apiUrl = pick("API_URL");
const anon = pick("ANON_KEY");
const service = pick("SERVICE_ROLE_KEY");
if (!apiUrl || !anon || !service) die(`解析 supabase status 失敗：\n${out}`);

const body = `# 由 npm run env:init 產生（來源：npx supabase status）
NEXT_PUBLIC_SUPABASE_URL=${apiUrl}
NEXT_PUBLIC_SUPABASE_ANON_KEY=${anon}
SUPABASE_SERVICE_ROLE_KEY=${service}   # 沒有 NEXT_PUBLIC_ 前綴。只給測試腳本用
`;

const file = path.join(ROOT, ".env.local");
const existed = existsSync(file);
writeFileSync(file, body);
console.log(`  ${c.green("✓")} ${existed ? "更新" : "產生"} .env.local`);
console.log(c.gray("    前兩行有 NEXT_PUBLIC_（大廳門禁，本來就公開）；"));
console.log(c.gray("    第三行故意沒有——萬能鑰匙鎖在櫃檯後面。這個命名差異就是紅線本人。"));
