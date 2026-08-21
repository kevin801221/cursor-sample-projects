"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

/**
 * 邀請碼加入。呼叫的是 app/api/teams/join/route.ts，
 * 但真正決定「能不能加進去」的是資料庫裡 003 的 with check 政策——
 * 這個表單就算被竄改成別人的 teamId，也一樣過不了。
 */
export function JoinForm() {
  const router = useRouter();
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [pending, startTransition] = useTransition();

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch("/api/teams/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: form.get("code"), teamId: form.get("teamId") }),
    });
    const body = await res.json().catch(() => ({}));
    if (res.ok) {
      setMsg({ ok: true, text: "加入成功" });
      startTransition(() => router.refresh());
    } else {
      setMsg({ ok: false, text: body.error ?? "加入失敗" });
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2">
      <input
        name="code"
        required
        placeholder="邀請碼（例：BETA-2026）"
        className="w-full rounded-lg border border-black/10 bg-white/70 px-3 py-2 text-sm dark:border-white/15 dark:bg-white/5"
      />
      <input
        name="teamId"
        required
        placeholder="團隊 id（demo:seed 會印出來）"
        className="w-full rounded-lg border border-black/10 bg-white/70 px-3 py-2 font-mono text-xs dark:border-white/15 dark:bg-white/5"
      />
      <button
        disabled={pending}
        className="w-full rounded-lg border border-black/15 px-3 py-2 text-sm font-medium disabled:opacity-50 dark:border-white/20"
      >
        用邀請碼加入
      </button>
      {msg && (
        <p className={`text-sm ${msg.ok ? "text-emerald-600" : "text-red-600"}`}>{msg.text}</p>
      )}
    </form>
  );
}
