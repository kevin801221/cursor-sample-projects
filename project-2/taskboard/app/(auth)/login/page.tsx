import { login, signup } from "./actions";

export default function LoginPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-2xl font-bold">TaskBoard</h1>
      <p className="mt-1 text-sm opacity-60">多租戶任務板 — 隔離做在資料庫層</p>

      <form className="mt-8 space-y-3">
        <input
          name="email"
          type="email"
          required
          placeholder="you@example.com"
          className="w-full rounded-lg border border-black/10 bg-white/70 px-3 py-2 text-sm dark:border-white/15 dark:bg-white/5"
        />
        <input
          name="password"
          type="password"
          required
          minLength={6}
          placeholder="密碼（至少 6 碼）"
          className="w-full rounded-lg border border-black/10 bg-white/70 px-3 py-2 text-sm dark:border-white/15 dark:bg-white/5"
        />

        {searchParams.error && (
          <p className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-600">
            {searchParams.error}
          </p>
        )}

        <div className="flex gap-2">
          <button
            formAction={login}
            className="flex-1 rounded-lg bg-black px-3 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
          >
            登入
          </button>
          <button
            formAction={signup}
            className="flex-1 rounded-lg border border-black/15 px-3 py-2 text-sm font-medium dark:border-white/20"
          >
            註冊
          </button>
        </div>
      </form>

      <p className="mt-6 text-xs opacity-50">
        課堂測試帳號（跑過 npm run demo:seed 之後）：
        <br />
        alice@taskboard.test / taskboard123
        <br />
        bob@taskboard.test / taskboard123
      </p>
    </main>
  );
}
