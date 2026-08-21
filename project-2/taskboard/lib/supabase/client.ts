import { createBrowserClient } from "@supabase/ssr";

/**
 * 瀏覽器端 client。只拿得到 anon key 與使用者自己的 session，
 * 看不到任何伺服器機密——service_role 絕不會出現在這條路徑上（安全紅線第 1、3 條）。
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
