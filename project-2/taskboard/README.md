# TaskBoard

Next.js 14 App Router + Supabase 多租戶任務板。課程 Project 2（第 22 章）的完整實作。

一句話：**多租戶隔離要做在資料庫層（RLS），不是前端。**

## 快速開始

```bash
npm install
npx supabase start     # 本地 Supabase（需 Docker，第一次拉映像檔 5–10 分鐘）
npm run env:init       # 從 supabase status 產生 .env.local
npm run db:push        # 套用 001/002/003 三個 migration
npm run demo:seed      # 佈課堂測資，印出 alice / bob 兩組帳密
npm run dev            # http://localhost:3000
npm run test:rls       # 8 passed
```

## 課堂用指令

| 指令 | 做什麼 |
|---|---|
| `npm run demo:break` | 把 RLS 換成漏洞版（`using (true)`） |
| `npm run demo:attack` | 模擬駭客拿 anon key 直接打 REST API |
| `npm run demo:fix` | 換回正確版 RLS |
| `npm run test:rls` | 五類八個 RLS 隔離測試 |

課堂放映請用上一層的 `../demo.sh`（`./demo.sh` 列出所有幕，`./demo.sh 5` 跑第 5 幕）。

逐步教學見 [walkthrough.md](./walkthrough.md)。
