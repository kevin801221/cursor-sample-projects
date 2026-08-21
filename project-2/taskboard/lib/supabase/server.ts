import { createServerClient as createSSRClient } from "@supabase/ssr";
import { cookies } from "next/headers";

/**
 * Server Components / Server Actions / Route Handlers 專用。
 * 從 cookie 讀出使用者 session，每一條查詢都帶著使用者 JWT——
 * auth.uid() 才有值，RLS 才判斷得了。
 *
 * 這裡用的是 anon key（大廳門禁），不是 service_role（萬能鑰匙）。安全紅線第 3 條。
 */
export async function createServerClient() {
  const cookieStore = cookies();

  return createSSRClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // 從 Server Component 呼叫時不能寫 cookie，交給 middleware 續期即可
          }
        },
      },
    }
  );
}
