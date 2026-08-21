import Link from "next/link";
import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { logout } from "../(auth)/login/actions";
import { createTeam } from "./actions";
import { JoinForm } from "./join-form";

export const dynamic = "force-dynamic";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  // ★ 注意這一行：select("*") —— 連 where 都沒加。
  //   回來的自然只有「我有加入的團隊」，因為過濾發生在資料庫的 RLS 政策裡
  //   （teams: member can read → id in (select my_team_ids()) or owner_id = auth.uid()）。
  //   這就是 RLS 的紅利：安全不再依賴每個查詢點的自律。
  const { data: teams } = await supabase.from("teams").select("*").order("created_at");

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">我的團隊</h1>
          <p className="mt-1 text-sm opacity-60">{user.email}</p>
        </div>
        <form action={logout}>
          <button className="rounded-lg border border-black/15 px-3 py-1.5 text-sm dark:border-white/20">
            登出
          </button>
        </form>
      </header>

      {searchParams.error && (
        <p className="mt-6 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-600">
          {searchParams.error}
        </p>
      )}

      <ul className="mt-6 space-y-2">
        {(teams ?? []).map((team) => (
          <li key={team.id}>
            <Link
              href={`/board/${team.id}`}
              className="flex items-center justify-between rounded-xl border border-black/10 bg-white/70 px-4 py-3 hover:border-black/25 dark:border-white/10 dark:bg-white/5 dark:hover:border-white/25"
            >
              <span className="font-medium">{team.name}</span>
              <span className="font-mono text-xs opacity-40">{team.id.slice(0, 8)}…</span>
            </Link>
          </li>
        ))}
        {(teams ?? []).length === 0 && (
          <li className="rounded-xl border border-dashed border-black/15 px-4 py-6 text-center text-sm opacity-60 dark:border-white/15">
            還沒有團隊。建一個，或用邀請碼加入。
          </li>
        )}
      </ul>

      <section className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
          <h2 className="text-sm font-semibold">建立團隊</h2>
          <form action={createTeam} className="mt-3 space-y-2">
            <input
              name="name"
              required
              placeholder="團隊名稱"
              className="w-full rounded-lg border border-black/10 bg-white/70 px-3 py-2 text-sm dark:border-white/15 dark:bg-white/5"
            />
            <button className="w-full rounded-lg bg-black px-3 py-2 text-sm font-medium text-white dark:bg-white dark:text-black">
              建立
            </button>
          </form>
        </div>

        <div className="rounded-xl border border-black/10 p-4 dark:border-white/10">
          <h2 className="text-sm font-semibold">用邀請碼加入</h2>
          <div className="mt-3">
            <JoinForm />
          </div>
        </div>
      </section>
    </main>
  );
}
