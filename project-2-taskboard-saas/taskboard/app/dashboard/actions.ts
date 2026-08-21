"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createServerClient } from "@/lib/supabase/server";

/**
 * 建立團隊。兩個 insert 都是「受 RLS 管」的：
 *  1. teams   → 政策 "teams: create own"（with check owner_id = auth.uid()）：想幫別人開團隊？擋。
 *  2. team_members → 政策 (b) bootstrap：蓋這棟房子的人可以把自己放進去當第一個 owner。
 */
export async function createTeam(formData: FormData) {
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return;

  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: team, error } = await supabase
    .from("teams")
    .insert({ name, owner_id: user.id })
    .select()
    .single();
  if (error) redirect(`/dashboard?error=${encodeURIComponent(error.message)}`);

  const { error: memberError } = await supabase
    .from("team_members")
    .insert({ team_id: team.id, user_id: user.id, role: "owner" });
  if (memberError) redirect(`/dashboard?error=${encodeURIComponent(memberError.message)}`);

  revalidatePath("/dashboard");
  redirect(`/board/${team.id}`);
}
