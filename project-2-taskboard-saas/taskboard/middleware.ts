import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * 站在整棟大樓入口的警衛：任何人要進任何頁面，都先經過他。
 * 沒帶房卡（未登入）→ 一律請去櫃檯 /login。
 *
 * 注意：middleware 只是「體驗」上的保護（避免看到空白頁），
 * 真正的安全邊界在資料庫的 RLS——就算有人繞過整個 Next.js，也讀不到別團隊的資料。
 */
export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          for (const { name, value } of cookiesToSet) request.cookies.set(name, value);
          response = NextResponse.next({ request });
          for (const { name, value, options } of cookiesToSet) {
            response.cookies.set(name, value, options);
          }
        },
      },
    }
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  // 排除 /login 本身與靜態資源，否則導向 /login 的請求又被攔 → 無限重導
  matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"],
};
