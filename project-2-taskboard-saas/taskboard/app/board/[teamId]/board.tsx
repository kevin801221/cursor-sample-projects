"use client";

import { useState, useTransition } from "react";
import { addTask, deleteTask, moveTask, renameTask } from "./actions";

export type Task = {
  id: string;
  team_id: string;
  title: string;
  status: "todo" | "in_progress" | "done";
  created_at: string;
};

const COLUMNS: { key: Task["status"]; label: string; tint: string }[] = [
  { key: "todo", label: "待辦", tint: "bg-slate-500/10" },
  { key: "in_progress", label: "進行中", tint: "bg-amber-500/10" },
  { key: "done", label: "完成", tint: "bg-emerald-500/10" },
];

export function Board({ teamId, initialTasks }: { teamId: string; initialTasks: Task[] }) {
  const [tasks, setTasks] = useState(initialTasks);
  const [error, setError] = useState<string | null>(null);
  const [, startTransition] = useTransition();

  /**
   * 樂觀更新：畫面先動，伺服器的確認晚點才到；失敗就把狀態退回去。
   * 就算這裡寫出 bug，也只是畫面短暫不同步——寫不進別人的團隊，因為門鎖跟畫面無關。
   */
  function optimistic(next: Task[], run: () => Promise<{ error?: string }>) {
    const snapshot = tasks;
    setTasks(next);
    setError(null);
    startTransition(async () => {
      const res = await run();
      if (res?.error) {
        setTasks(snapshot); // 退回
        setError(res.error);
      }
    });
  }

  function onDrop(status: Task["status"], id: string) {
    const task = tasks.find((t) => t.id === id);
    if (!task || task.status === status) return;
    optimistic(
      tasks.map((t) => (t.id === id ? { ...t, status } : t)),
      () => moveTask(id, status, teamId)
    );
  }

  async function onAdd(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const title = String(new FormData(form).get("title") ?? "").trim();
    if (!title) return;
    form.reset();
    const temp: Task = {
      id: `temp-${Date.now()}`,
      team_id: teamId,
      title,
      status: "todo",
      created_at: new Date().toISOString(),
    };
    optimistic([...tasks, temp], () => addTask(teamId, title));
  }

  return (
    <div>
      <form onSubmit={onAdd} className="flex gap-2">
        <input
          name="title"
          placeholder="新增任務…"
          className="flex-1 rounded-lg border border-black/10 bg-white/70 px-3 py-2 text-sm dark:border-white/15 dark:bg-white/5"
        />
        <button className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black">
          新增
        </button>
      </form>

      {error && (
        <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-600">
          資料庫拒絕了這個操作：{error}
        </p>
      )}

      {/* RWD：手機單欄，桌機三欄 */}
      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        {COLUMNS.map((col) => {
          const items = tasks.filter((t) => t.status === col.key);
          return (
            <section
              key={col.key}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => onDrop(col.key, e.dataTransfer.getData("text/plain"))}
              className={`rounded-xl border border-black/10 p-3 dark:border-white/10 ${col.tint}`}
            >
              <h2 className="flex items-center justify-between text-sm font-semibold">
                {col.label}
                <span className="rounded-full bg-black/10 px-2 text-xs dark:bg-white/10">
                  {items.length}
                </span>
              </h2>

              <ul className="mt-3 space-y-2 min-h-16">
                {items.map((t) => (
                  <li
                    key={t.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("text/plain", t.id)}
                    className="group cursor-grab rounded-lg border border-black/10 bg-white px-3 py-2 text-sm shadow-sm active:cursor-grabbing dark:border-white/10 dark:bg-black/40"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span>{t.title}</span>
                      <span className="flex shrink-0 gap-1 opacity-0 transition group-hover:opacity-60">
                        <button
                          aria-label="編輯"
                          onClick={() => {
                            const title = window.prompt("改成：", t.title)?.trim();
                            if (!title || title === t.title) return;
                            optimistic(
                              tasks.map((x) => (x.id === t.id ? { ...x, title } : x)),
                              () => renameTask(t.id, title, teamId)
                            );
                          }}
                        >
                          ✎
                        </button>
                        <button
                          aria-label="刪除"
                          onClick={() =>
                            optimistic(
                              tasks.filter((x) => x.id !== t.id),
                              () => deleteTask(t.id, teamId)
                            )
                          }
                        >
                          ✕
                        </button>
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>

      <p className="mt-6 text-xs opacity-50">
        提示：卡片可以拖曳換欄；滑過卡片會出現 ✎ 編輯與 ✕ 刪除。
      </p>
    </div>
  );
}
