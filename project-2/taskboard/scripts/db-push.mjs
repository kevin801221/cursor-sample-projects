// scripts/db-push.mjs —— 把 supabase/migrations/*.sql 依序套用到本地 Supabase。
//
// 為什麼不直接呼叫 `npx supabase db push`？
//   `supabase db push` 是推到「linked 的雲端專案」；本地 Docker 版的對應指令是 `supabase db reset`，
//   而且它只認 14 位數時間戳的檔名（20240101000000_xxx.sql），會直接略過 001_schema.sql 這種教學檔名。
//   課堂上要的是「檔名看得懂 + 一定套用得上」，所以這支腳本自己按檔名排序執行，
//   輸出訊息與 walkthrough 第 4.2 節的「✅ 預期看到」一致。
//   （之後接雲端專案時，把檔名換成時間戳並改用 npx supabase db push，流程完全一樣。）
import { readdirSync, rmSync } from "node:fs";
import path from "node:path";
import { ROOT, connectDb, readSql, c, die } from "./lib.mjs";

const RESET_PUBLIC = `
drop schema if exists public cascade;
create schema public;
grant usage on schema public to postgres, anon, authenticated, service_role;
grant all on all tables in schema public to postgres, anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to postgres, anon, authenticated, service_role;
alter default privileges in schema public grant all on functions to postgres, anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to postgres, anon, authenticated, service_role;
`;

const db = await connectDb();
try {
  // 重播式套用：先把 public schema 清成空的，再一張一張工程單跑過去。
  await db.query(RESET_PUBLIC);

  const dir = path.join(ROOT, "supabase/migrations");
  const files = readdirSync(dir).filter((f) => f.endsWith(".sql")).sort();
  if (files.length === 0) die("supabase/migrations 底下沒有任何 .sql");

  for (const f of files) {
    process.stdout.write(`Applying migration ${f}...`);
    await db.query(readSql(path.join("supabase/migrations", f)));
    console.log(c.green(" done"));
  }
  console.log(c.green("Finished supabase db push."));

  // 資料已經連同 public schema 一起被清空，舊的 .demo-seed.json 裡的 id 全部作廢。
  // 一定要刪掉：否則 demo.sh 的 need_seed 看到檔案還在就放行，
  // 第 5 幕會拿著失效的 id 去攻擊一個空資料庫，四項全部印成綠色的「擋下」——
  // 明明是還沒佈測資，看起來卻像 RLS 擋住了，課堂上最貴的一幕就這樣不聲不響地演砸。
  rmSync(path.join(ROOT, ".demo-seed.json"), { force: true });

  const { rows } = await db.query(`
    select relname as table_name, relrowsecurity as rls_enabled,
           (select count(*) from pg_policies p where p.tablename = c.relname and p.schemaname = 'public') as policies
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'r' order by relname`);
  console.log("\n" + c.bold("目前狀態（等同 Dashboard → Table Editor 的 RLS enabled 標籤）："));
  for (const r of rows) {
    const tag = r.rls_enabled ? c.green("RLS enabled") : c.red("RLS DISABLED");
    console.log(`  ${r.table_name.padEnd(14)} ${tag}   政策 ${r.policies} 條`);
  }
} catch (e) {
  die(`套用 migration 失敗：${e.message}\n救援：確認 npx supabase status 是 running，再重跑 npm run db:push`);
} finally {
  await db.end();
}
