// scripts/rls-switch.mjs —— 課堂上的「漏洞版 ⇄ 正確版」切換開關。
//   npm run demo:break  → 換上 supabase/migrations-broken/002_rls_INSECURE.sql（using (true)）
//   npm run demo:fix    → 換回 supabase/migrations/002_rls.sql + 003_join_team_policy.sql
// 資料不會動，只換政策——這樣「同一批資料、同一支攻擊腳本」，前後對照才乾淨。
import { connectDb, readSql, c, die } from "./lib.mjs";

const mode = process.argv[2];
if (!["break", "fix"].includes(mode)) die("用法：node scripts/rls-switch.mjs break|fix");

const db = await connectDb();
try {
  // 先把 public schema 底下所有政策清掉（不動資料、不動 enable RLS 的狀態）
  const { rows: existing } = await db.query(
    `select schemaname, tablename, policyname from pg_policies where schemaname = 'public'`
  );
  for (const p of existing) {
    await db.query(`drop policy ${JSON.stringify(p.policyname)} on public.${p.tablename}`);
  }

  const files =
    mode === "break"
      ? ["supabase/migrations-broken/002_rls_INSECURE.sql"]
      : ["supabase/migrations/002_rls.sql", "supabase/migrations/003_join_team_policy.sql"];

  for (const f of files) {
    await db.query(readSql(f));
    console.log(c.gray(`  已套用 ${f}`));
  }

  const { rows } = await db.query(
    `select tablename, policyname, coalesce(qual, 'n/a') as using_expr,
            coalesce(with_check, 'n/a') as check_expr
     from pg_policies where schemaname = 'public' order by tablename, policyname`
  );

  if (mode === "break") {
    console.log("\n" + c.redbg(" ⚠ 現在跑的是漏洞版 RLS：政策條件全部是 true ") + "\n");
    console.log(c.yellow("  注意：五張表的 RLS 依然是 Enabled，Dashboard 上還是綠色標籤，"));
    console.log(c.yellow("        security advisor 也不會警告——但門把誰都轉得開。\n"));
  } else {
    console.log("\n" + c.greenbg(" ✓ 已換回正確版 RLS：每一條政策都用 auth.uid() 劃界 ") + "\n");
  }

  console.log(c.bold("  目前 tasks 表的政策："));
  for (const r of rows.filter((r) => r.tablename === "tasks")) {
    const expr = r.using_expr !== "n/a" ? r.using_expr : r.check_expr;
    const paint = expr.trim() === "true" ? c.red : c.green;
    console.log(`    ${r.policyname.padEnd(28)} → ${paint(expr)}`);
  }
  console.log(
    "\n  " + c.blue(`下一步：npm run demo:attack（看同一支攻擊腳本這次的下場）`) + "\n"
  );
} catch (e) {
  die(`切換失敗：${e.message}\n救援：npm run db:push 重建資料庫後再試一次`);
} finally {
  await db.end();
}
