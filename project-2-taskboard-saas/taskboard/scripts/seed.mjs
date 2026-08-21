// scripts/seed.mjs —— 用 service_role 佈好課堂測資：兩個帳號、兩個團隊、各自的任務與邀請碼。
// service_role 會繞過所有 RLS，所以它只能活在這種伺服器端腳本裡（規則 1、3）。
import { writeFileSync } from "node:fs";
import path from "node:path";
import { createClient } from "@supabase/supabase-js";
import { ROOT, loadEnv, c, die } from "./lib.mjs";

const env = loadEnv();
const admin = createClient(env.url, env.serviceKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const PASSWORD = "taskboard123";
const USERS = [
  { key: "alice", email: "alice@taskboard.test", name: "Alice（Alpha 行銷團隊 owner）" },
  { key: "bob", email: "bob@taskboard.test", name: "Bob（Beta 工程團隊 owner）" },
];
const TEAMS = {
  alpha: "Alpha 行銷團隊",
  beta: "Beta 工程團隊",
};

const check = ({ error }, what) => {
  if (error) die(`${what} 失敗：${error.message}`);
};

async function main() {
  console.log(c.bold("\n用 service_role 佈置課堂測資…\n"));

  // 1) 找出舊的示範帳號，先清掉他們的團隊（cascade 會一起帶走 team_members / tasks / invites），
  //    再刪帳號——順序不能反，因為 teams.owner_id 指向 profiles。
  const { data: list, error: listErr } = await admin.auth.admin.listUsers({ perPage: 1000 });
  if (listErr) die(`列出使用者失敗：${listErr.message}`);
  const oldIds = USERS.map((u) => list.users.find((x) => x.email === u.email)?.id).filter(Boolean);
  if (oldIds.length) check(await admin.from("teams").delete().in("owner_id", oldIds), "清除舊團隊");

  // 2) 重建兩個示範帳號
  const ids = {};
  for (const u of USERS) {
    const old = list.users.find((x) => x.email === u.email);
    if (old) await admin.auth.admin.deleteUser(old.id);
    const { data, error } = await admin.auth.admin.createUser({
      email: u.email,
      password: PASSWORD,
      email_confirm: true,
    });
    if (error) die(`建立 ${u.email} 失敗：${error.message}`);
    ids[u.key] = data.user.id;
    // profiles 由 001 的 on_auth_user_created trigger 自動建立，這裡只補顯示名稱
    check(await admin.from("profiles").update({ display_name: u.name }).eq("id", data.user.id), "更新 profile");
    console.log(`  ${c.green("✓")} 建立帳號 ${u.email}`);
  }

  // 3) 兩個團隊 + 各自的 owner
  const { data: teams, error: tErr } = await admin
    .from("teams")
    .insert([
      { name: TEAMS.alpha, owner_id: ids.alice },
      { name: TEAMS.beta, owner_id: ids.bob },
    ])
    .select();
  if (tErr) die(`建立團隊失敗：${tErr.message}`);
  const alpha = teams.find((t) => t.name === TEAMS.alpha);
  const beta = teams.find((t) => t.name === TEAMS.beta);

  check(
    await admin.from("team_members").insert([
      { team_id: alpha.id, user_id: ids.alice, role: "owner" },
      { team_id: beta.id, user_id: ids.bob, role: "owner" },
    ]),
    "建立團隊成員"
  );
  console.log(`  ${c.green("✓")} 建立團隊 ${TEAMS.alpha} / ${TEAMS.beta}`);

  // 4) 各塞三張任務。Beta 的刻意寫得很機密——等一下漏出來時，全班會有感覺。
  check(
    await admin.from("tasks").insert([
      { team_id: alpha.id, title: "設計新版首頁 banner", status: "todo", created_by: ids.alice },
      { team_id: alpha.id, title: "整理 Q3 廣告成效報告", status: "in_progress", created_by: ids.alice },
      { team_id: alpha.id, title: "客戶提案簡報定稿", status: "done", created_by: ids.alice },
      { team_id: beta.id, title: "🔒 併購案技術盡職調查報告", status: "todo", created_by: ids.bob },
      { team_id: beta.id, title: "🔒 資安漏洞 CVE-2026-1337 熱修", status: "in_progress", created_by: ids.bob },
      { team_id: beta.id, title: "🔒 明年度薪資調整名單", status: "done", created_by: ids.bob },
    ]),
    "建立任務"
  );
  console.log(`  ${c.green("✓")} 每個團隊各三張任務（Beta 的是機密內容）`);

  // 5) 邀請碼：一個有效、一個過期
  const day = 24 * 60 * 60 * 1000;
  check(
    await admin.from("invites").insert([
      { code: "BETA-2026", team_id: beta.id, expires_at: new Date(Date.now() + 7 * day).toISOString() },
      { code: "OLD-2025", team_id: beta.id, expires_at: new Date(Date.now() - day).toISOString() },
    ]),
    "建立邀請碼"
  );
  console.log(`  ${c.green("✓")} 邀請碼 BETA-2026（有效）、OLD-2025（已過期）\n`);

  // 6) 把 id 存起來給 attack.mjs 用
  const state = {
    password: PASSWORD,
    alice: { id: ids.alice, email: USERS[0].email, teamId: alpha.id, teamName: TEAMS.alpha },
    bob: { id: ids.bob, email: USERS[1].email, teamId: beta.id, teamName: TEAMS.beta },
    invites: { valid: "BETA-2026", expired: "OLD-2025" },
  };
  writeFileSync(path.join(ROOT, ".demo-seed.json"), JSON.stringify(state, null, 2));

  const line = "═".repeat(62);
  console.log(c.blue(line));
  console.log(c.bold("  課堂帳號（開兩個瀏覽器視窗，各登入一個）"));
  console.log(c.blue(line));
  console.log(`  A：${c.bold("alice@taskboard.test")} / ${c.bold(PASSWORD)}   → ${TEAMS.alpha}`);
  console.log(`  B：${c.bold("bob@taskboard.test")}   / ${c.bold(PASSWORD)}   → ${TEAMS.beta}`);
  console.log(c.blue(line));
  console.log(`  登入頁：http://localhost:3000/login`);
  console.log(`  Beta 團隊 id（等下攻擊腳本要硬塞的就是它）：${c.yellow(beta.id)}`);
  console.log(c.blue(line) + "\n");
}

main();
