import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { Board, type Task } from "./board";

export const dynamic = "force-dynamic";

export default async function BoardPage({ params }: { params: { teamId: string } }) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  // 不是這個團隊的成員？RLS 讓這一列「不存在」，回來就是 null——不是 403，是查不到。
  const { data: team } = await supabase
    .from("teams")
    .select("*")
    .eq("id", params.teamId)
    .maybeSingle();
  if (!team) notFound();

  // 這個 .eq("team_id") 是為了「只顯示這一個看板」，不是為了安全。
  // 安全那層已經由 RLS 做掉了：把 .eq 拿掉，回來的也只會是自己團隊的任務。
  const { data: tasks } = await supabase
    .from("tasks")
    .select("*")
    .eq("team_id", params.teamId)
    .order("created_at");

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <div>
          <Link href="/dashboard" className="text-sm opacity-60 hover:opacity-100">
            ← 我的團隊
          </Link>
          <h1 className="mt-1 text-2xl font-bold">{team.name}</h1>
        </div>
        <span className="font-mono text-xs opacity-40">{team.id}</span>
      </header>

      <Board teamId={params.teamId} initialTasks={(tasks ?? []) as Task[]} />
    </main>
  );
}
