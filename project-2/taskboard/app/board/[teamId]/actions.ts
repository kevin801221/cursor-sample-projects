"use server";

import { revalidatePath } from "next/cache";
import { createServerClient } from "@/lib/supabase/server";

export type ActionResult = { error?: string };

/**
 * 所有寫入都走 Server Action（nextjs.mdc 規則），而且用的都是使用者自己的 session。
 * 沒有任何一個 action 需要「先檢查你是不是這個團隊的人」——
 * tasks 的四條政策已經在資料庫層把界劃好了。寫錯了頂多失敗，不會寫進別人的團隊。
 */

export async function addTask(teamId: string, title: string): Promise<ActionResult> {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { error: "請先登入" };

  // 政策 "tasks: member can insert"：team_id 必須在我的團隊裡，且 created_by 必須是我
  const { error } = await supabase.from("tasks").insert({ team_id: teamId, title, created_by: user.id });
  revalidatePath(`/board/${teamId}`);
  return error ? { error: error.message } : {};
}

export async function moveTask(taskId: string, status: string, teamId: string): Promise<ActionResult> {
  const supabase = await createServerClient();
  const { error } = await supabase.from("tasks").update({ status }).eq("id", taskId);
  revalidatePath(`/board/${teamId}`);
  return error ? { error: error.message } : {};
}

export async function renameTask(taskId: string, title: string, teamId: string): Promise<ActionResult> {
  const supabase = await createServerClient();
  const { error } = await supabase.from("tasks").update({ title }).eq("id", taskId);
  revalidatePath(`/board/${teamId}`);
  return error ? { error: error.message } : {};
}

export async function deleteTask(taskId: string, teamId: string): Promise<ActionResult> {
  const supabase = await createServerClient();
  const { error } = await supabase.from("tasks").delete().eq("id", taskId);
  revalidatePath(`/board/${teamId}`);
  return error ? { error: error.message } : {};
}
