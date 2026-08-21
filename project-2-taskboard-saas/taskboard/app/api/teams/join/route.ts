import { createServerClient } from "@/lib/supabase/server";

// app/api/teams/join/route.ts —— 驗證不在這裡做，with check 政策會做
export async function POST(req: Request) {
  const { code, teamId } = await req.json();
  const supabase = await createServerClient(); // 帶著使用者 JWT，受 RLS 管
  const { error } = await supabase.rpc("join_team", { invite_code: code, target_team: teamId });
  if (error) return Response.json({ error: "邀請碼無效或已過期" }, { status: 403 });
  return Response.json({ ok: true });
}
