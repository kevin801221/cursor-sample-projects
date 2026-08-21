/**
 * tests/rls.test.ts —— 規則 6：新增政策一律補一個 test:rls 案例，證明跨團隊讀不到。
 *
 * 為什麼一定要測試？因為 RLS 寫錯**不會報錯**——它只會安靜地全放行，或安靜地全擋掉。
 * `USING (true)` 的表在自己的畫面上看起來完全正常，因為你本來就只查自己的資料。
 * 只有讓兩個不同的人互相試探，謊言才會被拆穿。
 *
 * 佈景：用 service_role 佈測資（它繞過 RLS），再用 anon key + signInWithPassword
 *       分別以 A、B、C 的身份去撬鎖。八個案例，五個類別。
 *
 * 執行：npm run test:rls
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { loadEnv, c } from "../scripts/lib.mjs";

const env = loadEnv();
const admin = createClient(env.url, env.serviceKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const PASSWORD = "rls-test-123456";
const stamp = Date.now();
const email = (who: string) => `rls-${who}-${stamp}@taskboard.test`;

// 佈景裡的角色
let userA = "", userB = "", userC = "";
let team1 = "", team2 = "";
let A: SupabaseClient, B: SupabaseClient, anon: SupabaseClient;
const CODE_OK = `INV-OK-${stamp}`;
const CODE_EXPIRED = `INV-OLD-${stamp}`;

// ── 極簡測試框架（不架 vitest 的排場，40 行就夠）──────────────
type Case = { group: string; name: string; fn: () => Promise<void> };
const cases: Case[] = [];
const test = (group: string, name: string, fn: () => Promise<void>) =>
  cases.push({ group, name, fn });
function assert(cond: unknown, msg: string): asserts cond {
  if (!cond) throw new Error(msg);
}

// ── 佈景 ────────────────────────────────────────────────────
async function signIn(mail: string) {
  const client = createClient(env.url, env.anonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const { error } = await client.auth.signInWithPassword({ email: mail, password: PASSWORD });
  if (error) throw new Error(`登入 ${mail} 失敗：${error.message}`);
  return client;
}

async function setup() {
  const mk = async (who: string) => {
    const { data, error } = await admin.auth.admin.createUser({
      email: email(who),
      password: PASSWORD,
      email_confirm: true,
    });
    if (error) throw new Error(`建立測試帳號失敗：${error.message}`);
    return data.user.id;
  };
  userA = await mk("a");
  userB = await mk("b");
  userC = await mk("c");

  const { data: teams, error: tErr } = await admin
    .from("teams")
    .insert([
      { name: `RLS 測試團隊 1 (${stamp})`, owner_id: userA },
      { name: `RLS 測試團隊 2 (${stamp})`, owner_id: userC },
    ])
    .select();
  if (tErr) throw new Error(`建立團隊失敗：${tErr.message}`);
  team1 = teams[0].id;
  team2 = teams[1].id;

  // A 是團隊 1 的 owner；團隊 2 的 owner 是 C，B 只是團隊 2 的 member
  await admin.from("team_members").insert([
    { team_id: team1, user_id: userA, role: "owner" },
    { team_id: team2, user_id: userC, role: "owner" },
    { team_id: team2, user_id: userB, role: "member" },
  ]);

  await admin.from("tasks").insert([
    { team_id: team1, title: "團隊 1 的任務甲", created_by: userA },
    { team_id: team1, title: "團隊 1 的任務乙", created_by: userA },
    { team_id: team2, title: "團隊 2 的任務甲", created_by: userC },
    { team_id: team2, title: "團隊 2 的任務乙", created_by: userC },
  ]);

  const hour = 60 * 60 * 1000;
  await admin.from("invites").insert([
    { code: CODE_OK, team_id: team1, expires_at: new Date(Date.now() + hour).toISOString() },
    { code: CODE_EXPIRED, team_id: team1, expires_at: new Date(Date.now() - hour).toISOString() },
  ]);

  A = await signIn(email("a"));
  B = await signIn(email("b"));
  anon = createClient(env.url, env.anonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

async function teardown() {
  await admin.from("teams").delete().in("id", [team1, team2]); // cascade 帶走成員／任務／邀請碼
  for (const id of [userA, userB, userC]) if (id) await admin.auth.admin.deleteUser(id);
}

// ── 1. 跨團隊讀取 ────────────────────────────────────────────
test("跨團隊讀取", "A 查 tasks 只看得到團隊 1 的任務", async () => {
  const { data, error } = await A.from("tasks").select("*"); // 連 where 都不加
  assert(!error, `查詢出錯：${error?.message}`);
  const mine = data!.filter((t) => t.team_id === team1);
  const others = data!.filter((t) => t.team_id === team2);
  assert(mine.length === 2, `A 應該看得到團隊 1 的 2 筆，實際 ${mine.length} 筆`);
  assert(others.length === 0, `A 竟然看得到團隊 2 的 ${others.length} 筆任務——資料外洩！`);
});

test("跨團隊讀取", "B 查 tasks 只看得到團隊 2 的任務", async () => {
  const { data, error } = await B.from("tasks").select("*");
  assert(!error, `查詢出錯：${error?.message}`);
  const leaked = data!.filter((t) => t.team_id === team1);
  assert(leaked.length === 0, `B 竟然看得到團隊 1 的 ${leaked.length} 筆任務——資料外洩！`);
});

// ── 2. 跨團隊寫入 ────────────────────────────────────────────
test("跨團隊寫入", "A 無法 insert 任務到團隊 2", async () => {
  const { error } = await A.from("tasks").insert({
    team_id: team2,
    title: "A 硬塞進團隊 2 的任務",
    created_by: userA,
  });
  assert(error, "A 竟然寫得進團隊 2——with check 政策沒擋住！");
});

// ── 3. 成員管理 ──────────────────────────────────────────────
test("成員管理", "B（member）無法把別人加進團隊 2", async () => {
  const { error } = await B.from("team_members").insert({
    team_id: team2,
    user_id: userA,
    role: "member",
  });
  assert(error, "非 owner 竟然加得了人——003 的 insert 政策沒擋住！");
});

test("成員管理", "A（owner）可以加人進團隊 1", async () => {
  const { error } = await A.from("team_members").insert({
    team_id: team1,
    user_id: userC,
    role: "member",
  });
  assert(!error, `owner 應該加得了人，卻被擋下：${error?.message}`);
});

// ── 4. 邀請碼 ────────────────────────────────────────────────
test("邀請碼", "過期／偽造的邀請碼加入被拒", async () => {
  const fake = await B.rpc("join_team", { invite_code: "NOT-A-REAL-CODE", target_team: team1 });
  assert(fake.error, "偽造邀請碼竟然加得進去！");
  const expired = await B.rpc("join_team", { invite_code: CODE_EXPIRED, target_team: team1 });
  assert(expired.error, "過期邀請碼竟然還能用！");
});

test("邀請碼", "有效邀請碼可以成功加入", async () => {
  const { error } = await B.rpc("join_team", { invite_code: CODE_OK, target_team: team1 });
  assert(!error, `有效邀請碼應該成功，卻失敗：${error?.message}`);
  const { data } = await admin
    .from("team_members")
    .select("*")
    .eq("team_id", team1)
    .eq("user_id", userB);
  assert(data!.length === 1, "邀請碼沒報錯，但名冊上查不到這筆");
});

// ── 5. 未登入 ────────────────────────────────────────────────
test("未登入", "純 anon key 查 tasks 回傳空陣列", async () => {
  const { data, error } = await anon.from("tasks").select("*");
  assert(!error, `查詢出錯：${error?.message}`);
  assert(data!.length === 0, `未登入竟然撈到 ${data!.length} 筆任務——RLS 形同虛設！`);
});

// ── 跑起來 ──────────────────────────────────────────────────
async function main() {
  console.log(c.bold("\nRLS 隔離測試（tests/rls.test.ts）\n"));
  await setup();

  let passed = 0;
  const failures: { name: string; message: string }[] = [];
  let lastGroup = "";

  for (const t of cases) {
    if (t.group !== lastGroup) {
      console.log(c.gray(`  ── ${t.group} ──`));
      lastGroup = t.group;
    }
    try {
      await t.fn();
      passed++;
      console.log(`  ${c.green("✓")} ${t.name}`);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      failures.push({ name: t.name, message });
      console.log(`  ${c.red("✗")} ${t.name}`);
      console.log(`      ${c.red(message)}`);
    }
  }

  await teardown();

  console.log("");
  if (failures.length === 0) {
    console.log(c.green(`${passed} passed`) + "\n");
    process.exit(0);
  }
  console.log(c.red(`${failures.length} failed`) + c.gray(`, ${passed} passed`));
  console.log(
    c.yellow(
      "\n救援：常見是 infinite recursion detected in policy（政策子查詢了自己那張表，\n" +
        "      改用 security definer helper，見 walkthrough 4.2）。\n" +
        "      如果剛剛跑過 npm run demo:break，這裡紅掉是正常的——那正是這一幕要演的。\n"
    )
  );
  process.exit(1);
}

main().catch(async (e) => {
  console.error(c.red(`\n測試佈景失敗：${e.message}`));
  console.error(c.yellow("救援：確認 npx supabase status 是 running，且已跑過 npm run db:push\n"));
  await teardown().catch(() => {});
  process.exit(1);
});
