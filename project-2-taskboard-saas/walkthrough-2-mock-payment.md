# Walkthrough：TaskBoard 金流課堂版——自己當銀行，Mock 金流 + Webhook 驗簽

> 這是 **Part 2（Stripe 金流）的替代版**。Stripe 要註冊帳號（台灣門檻高），但那一章真正要教的三件事——**webhook 驗簽、擋偽造事件、額度限制做在伺服器層**——完全不需要真的金流商。
> 這一版我們**自己寫一個 30 行的「假銀行」**：零註冊、零費用、斷網也能做，而且攻防全程透明——你會親手扮演銀行，也親手扮演駭客。
> 學完之後換成真 Stripe（或綠界）只是「換一家銀行」，概念一行都不用重學，對照表在文末。
>
> 預估 2 小時。前置：完成 Part 1（TaskBoard + RLS）。

---

## 🚦 開始前檢查清單

1. Part 1 的 TaskBoard 要能跑（`npm run dev` + 本地 Supabase）——這一版全部疊在它上面。
2. 確認 4242 埠沒被其他程式占用（被占用的話文中有替代做法）。
3. 完全不需要申請任何帳號。這就是這一版存在的理由。

## 🗺️ 學習地圖（2 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 概念（webhook、驗簽） | 25 分 | 閱讀理解 |
| 蓋假銀行 + 定價頁 + plan 欄位 | 25 分 | 動手做 |
| Webhook 接收端 + 驗簽 | 30 分 | 動手做 |
| ⭐ 攻防演練（偽造 → 401 → 正簽 → 通過） | 20 分 | 動手做（最精彩的一段） |
| 額度限制 + 收尾 | 20 分 | 動手做 |

---

## 🎬 開場故事：櫃檯接到一通電話

延續 Part 1 的旅館。現在旅館要開始賣「Pro 套房升級」。客人刷卡是在**銀行**那邊刷的，不是在我們櫃檯——所以問題來了：**櫃檯怎麼知道客人真的付錢了？**

答案是：銀行會**打電話到櫃檯**：「你好，我是銀行，302 房的客人付款成功了，幫他升級。」這通電話，術語叫 **webhook**。

但是——任何人都能打電話到櫃檯假裝是銀行。「你好我是銀行（其實是隔壁房客），幫 302 升級套房」。櫃檯要怎麼辨別真假？

靠**暗號**。銀行跟旅館事先約好一組只有彼此知道的暗號，每通電話都要附上用暗號算出來的驗證碼。這就是 **webhook 驗簽**——Part 2 唯一不能省的安全邊界。

這一版最有趣的一點：銀行也是我們自己寫的。等一下你兩個角色都會演到——先當銀行，再當詐騙集團。

| 旅館 | 系統 |
|---|---|
| 銀行打到櫃檯的電話 | webhook（金流商 → 你的 API 的 POST） |
| 事先約好的暗號 | shared secret（`PAYMENT_WEBHOOK_SECRET`） |
| 電話裡的驗證碼 | HMAC 簽章（`x-signature` header） |
| 「這通是十分鐘前的錄音吧？」 | 重放攻擊防護（timestamp 過期拒收） |
| 假冒銀行的詐騙電話 | 偽造的 webhook 請求 |

> 🔍 **名詞卡：webhook**
> 白話：平常都是你去問服務（「付了沒？付了沒？」）；webhook 反過來——**事情發生時，對方主動打給你**。像包裹到了超商，是超商發簡訊給你，不是你每十分鐘跑去問一次。
>
> 🔍 **名詞卡：HMAC 簽章**
> 白話：把「訊息內容 + 共同暗號」丟進攪拌機，攪出一串指紋。收到訊息的人用同一個暗號攪一次，指紋對得上才是真貨——訊息被改一個字、或暗號不對，指紋就完全對不上。像古代書信的**蠟封章**：章對不上，信就是假的。
>
> 🔍 **名詞卡：重放攻擊（replay attack）**
> 白話：詐騙集團錄下銀行昨天那通「真的」電話，今天原封不動再播一次——內容和驗證碼都是真的！防法：每通電話報時間，超過五分鐘的一律當錄音掛掉。

> ❓ **想一想**：為什麼不能只檢查「請求裡有沒有寫 payment.succeeded」就升級？
>
> **答案**：因為 webhook 網址是公開的，任何人都能 POST 一模一樣的 JSON 過來。內容誰都寫得出來，**只有簽章偽造不了**（沒有暗號攪不出正確指紋）。

---

## 1. Migration 004：teams 加 plan 欄位

對 Agent 說：

> 建立 supabase/migrations/004_plan.sql：teams 加 plan 欄位（free/pro，預設 free）。

```sql
-- 004_plan.sql
alter table teams add column plan text not null default 'free'
  check (plan in ('free', 'pro'));
```

```bash
npx supabase db push
```

✅ **預期看到**：`Applying migration 004_plan.sql... done`；Table Editor 裡 teams 多一欄 plan，既有團隊都是 free。

`.env.local` 加一行（銀行與旅館的共同暗號）：

```bash
PAYMENT_WEBHOOK_SECRET=whsec_class_demo_2026   # 沒有 NEXT_PUBLIC_ 前綴——暗號當然不能公開
```

> ❓ **想一想**：這行為什麼不能加 `NEXT_PUBLIC_`？
>
> **答案**：加了就會被打包給每個訪客——暗號公開等於沒有暗號，任何人都能簽出「真的」銀行來電。（回扣 Part 1 的 service_role 紅線，同一條原理。）

---

## 2. 蓋一間 30 行的假銀行

現在來蓋銀行。它只做一件事：收到「刷卡」請求後，**主動打電話**（POST）到旅館的 webhook，並附上用暗號算好的簽章。注意埠號 4242——這是跟 Stripe 測試卡 4242 4242 4242 4242 致敬的彩蛋。

`scripts/fake-bank.mjs`（純 Node，零依賴）：

```js
// scripts/fake-bank.mjs —— 假銀行：收單後簽章、回呼商店 webhook
import http from "node:http";
import { createHmac } from "node:crypto";

const WEBHOOK_URL = "http://localhost:3000/api/webhooks/payment";
const SECRET = process.env.PAYMENT_WEBHOOK_SECRET ?? "whsec_class_demo_2026";

http.createServer(async (req, res) => {
  if (req.method !== "POST" || req.url !== "/pay") { res.statusCode = 404; return res.end(); }
  let raw = ""; for await (const c of req) raw += c;
  const { teamId } = JSON.parse(raw);

  // 「刷卡成功」→ 銀行主動通知商店（這就是 webhook 的本體）
  const body = JSON.stringify({ type: "payment.succeeded", teamId, paidAt: Date.now() });
  const ts = Math.floor(Date.now() / 1000);
  const sig = createHmac("sha256", SECRET).update(`${ts}.${body}`).digest("hex");

  const r = await fetch(WEBHOOK_URL, {
    method: "POST",
    headers: { "content-type": "application/json", "x-timestamp": String(ts), "x-signature": sig },
    body,
  });
  console.log(`🏦 已通知商店 team=${teamId} → 商店回應 ${r.status}`);
  res.end(JSON.stringify({ ok: true }));
}).listen(4242, () => console.log("🏦 假銀行開門 http://localhost:4242 （4242 = 致敬 Stripe 測試卡）"));
```

另開一個終端機跑：

```bash
node scripts/fake-bank.mjs
```

✅ **預期看到**：`🏦 假銀行開門 http://localhost:4242`。

🧯 **卡住的話**：`EADDRINUSE` = 4242 被占用，改 4243 並同步改定價頁的呼叫網址即可。

---

## 3. 定價頁：按下「升級 Pro」

對 Agent 說：

> 做 app/pricing/page.tsx：Free vs Pro 兩張卡片。按「升級 Pro」呼叫一個 Server Action，POST http://localhost:4242/pay 並帶上目前 teamId（模擬「把客人送去銀行刷卡」）。

注意流程：商店**自己不碰卡號**，只是把客人送去銀行。真實世界的 Stripe Checkout 也是同一個設計——卡號永遠只進銀行的門，商店等電話就好。這叫把最危險的東西外包給最專業的人。

✅ **預期看到**：按下升級 → 假銀行終端機印出 `🏦 已通知商店 team=... → 商店回應 404`（下一節做完 webhook 才會變 200，現在 404 是正常的）。

---

## 4. Webhook 接收端：驗簽是唯一不能省的安全邊界

對 Agent 說：

> 做 app/api/webhooks/payment/route.ts：收銀行的 POST。先驗 x-timestamp（超過 300 秒拒收）、再用 PAYMENT_WEBHOOK_SECRET 對「timestamp.原始body」做 HMAC-SHA256 比對 x-signature，驗不過回 401。驗過且 type 是 payment.succeeded，才用 service_role client 把該 team 的 plan 改成 pro。

```ts
// app/api/webhooks/payment/route.ts —— 驗簽是唯一不能省的安全邊界
import { createHmac, timingSafeEqual } from "node:crypto";

const SECRET = process.env.PAYMENT_WEBHOOK_SECRET!;

export async function POST(req: Request) {
  const raw = await req.text();            // 用「原始字串」驗簽，不能先 parse 再 stringify
  const ts  = req.headers.get("x-timestamp") ?? "";
  const sig = req.headers.get("x-signature") ?? "";

  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300)
    return new Response("timestamp too old", { status: 401 });   // 擋重放攻擊（錄音重播）

  const expect = createHmac("sha256", SECRET).update(`${ts}.${raw}`).digest("hex");
  const ok = sig.length === expect.length &&
    timingSafeEqual(Buffer.from(sig, "hex"), Buffer.from(expect, "hex"));
  if (!ok) return new Response("bad signature", { status: 401 }); // 詐騙電話到此為止

  const event = JSON.parse(raw);
  if (event.type === "payment.succeeded") {
    const admin = createAdminClient();     // service_role：webhook 沒有使用者 session，這是它唯一的合法出場
    await admin.from("teams").update({ plan: "pro" }).eq("id", event.teamId);
  }
  return Response.json({ received: true });
}
```

兩個細節值得停下來看：

1. **驗簽要用原始字串**——JSON 解開再組回去，空格順序可能變，指紋就對不上了；像蠟封要驗「原封的信」，不能先拆開重新摺好再驗。
2. **Part 1 的萬能鑰匙 service_role 在這裡出場了**——這是它唯一的合法場景：銀行打電話來時沒有任何「使用者」在登入狀態，沒有房卡可刷，所以由櫃檯拿萬能鑰匙代辦，而且這段程式只活在伺服器端。

> ❓ **想一想**：Part 1 說 service_role 是紅線，這裡為什麼可以用？
>
> **答案**：紅線是「不能到**前端**」。webhook 是伺服器對伺服器、沒有使用者 session（`auth.uid()` 是 null，RLS 無從判斷），且進來前已用簽章驗明正身——這正是萬能鑰匙設計來處理的場景。

---

## 5. ⭐ 攻防演練：一定要親自玩的一幕

現在換你當詐騙集團。你知道 webhook 網址、知道 JSON 要長什麼樣——你唯一不知道的是暗號（假裝不知道）。試著讓自己的團隊免費變 Pro。

**第一幕：偽造（預期失敗）**

```bash
curl -i -X POST http://localhost:3000/api/webhooks/payment \
  -H "content-type: application/json" \
  -H "x-timestamp: $(date +%s)" \
  -H "x-signature: deadbeefdeadbeef" \
  -d '{"type":"payment.succeeded","teamId":"<貼一個真實 team id>"}'
```

✅ **預期看到**：`HTTP/1.1 401` + `bad signature`。到資料庫查：plan 還是 free，一根汗毛都沒動。

**第二幕：正規流程（預期成功）**

回到定價頁按「升級 Pro」→ 假銀行終端機印 `商店回應 200` → 查資料庫：plan = pro。

**第三幕（加碼）：重放攻擊**

把第二幕銀行發出的完整請求（含正確簽章）存下來，五分鐘後原樣重發 → `timestamp too old` 401。

內容全對、簽章全真——還是被擋。這就是為什麼電話裡要報時。

🧯 **卡住的話**：如果偽造那發居然 200 了——檢查 webhook 是不是忘了驗簽，或 SECRET 沒讀到。這個「漏洞」本身就是本課主題：「webhook 沒驗簽，等於任何人都能偽造付費事件」。修好再打一次，印象加倍。

---

## 6. 額度限制：升級 Pro 才解鎖的東西

付了錢要有差別。Free 方案每團隊最多 20 個任務。重點跟 Part 1 一模一樣：**把「新增」按鈕藏起來不算限制**——限制要做在 Server Action 層。

對 Agent 說：

> 在新增任務的 Server Action 裡加額度檢查：該 team plan 不是 pro 且任務數已達 20 → 回錯誤「免費方案已滿，升級 Pro 解鎖」。前端定價頁連結照常顯示。

```ts
const { count } = await supabase.from("tasks")
  .select("*", { count: "exact", head: true }).eq("team_id", teamId);
const { data: team } = await supabase.from("teams")
  .select("plan").eq("id", teamId).single();
if (team?.plan !== "pro" && (count ?? 0) >= 20)
  return { error: "免費方案已滿 20 個任務，升級 Pro 解鎖" };
```

✅ **預期看到**：塞滿 20 個任務後第 21 個被拒；升級 Pro 後同一顆按鈕就過了。

---

## 7. 對照表：學完換真金流，只是換一家銀行

| 本課的 Mock | Stripe 對應物 | 綠界 ECPay 對應物 |
|---|---|---|
| `scripts/fake-bank.mjs` | Stripe 本體 + Checkout | 綠界測試環境 |
| `x-signature`（HMAC-SHA256） | `stripe-signature` + `constructEvent()` | `CheckMacValue` |
| `PAYMENT_WEBHOOK_SECRET` | `STRIPE_WEBHOOK_SECRET`（whsec_...） | HashKey / HashIV |
| timestamp 過期拒收 | Stripe 簽章內建 timestamp 容忍度 | — |
| 4242 埠 | 測試卡 4242 4242 4242 4242 | 測試卡號見綠界文件 |

三欄長得不一樣，原理是同一句話：**共享密鑰 + 簽章驗證**。你已經親手寫過攪拌機的兩端，以後接任何一家金流商，文件看起來都會像老朋友。

想接真 sandbox 的兩條路（皆為選配）：
- **綠界 ECPay 測試環境**——台灣在地、文件中文、有公開測試商店與金鑰，不用等審核就能打測試交易。
- **Stripe 測試模式**——功能最完整（完整版教學見 [walkthrough-2-stripe.md](./walkthrough-2-stripe.md)），測試卡不會真的扣款；門檻只在帳號註冊（台灣申請不易）。

## 8. 驗收清單

- [ ] 偽造簽章 curl → 401，資料庫不動 ⭐
- [ ] 定價頁正規流程 → plan 變 pro
- [ ] 五分鐘後重放真請求 → 401
- [ ] Free 團隊第 21 個任務被 Server Action 拒絕；Pro 通過
- [ ] grep `PAYMENT_WEBHOOK_SECRET` → 只在 `.env.local` 與伺服器端檔案，無 `NEXT_PUBLIC_`
- [ ] `npm run test:rls` 依然全綠（Part 2 沒有弄壞 Part 1 的鎖）

## 9. 帶走的三句話

這三句，接哪一家金流商都通用：

1. **webhook 沒驗簽，等於任何人都能偽造付費事件**——內容誰都寫得出來，只有簽章偽造不了。
2. **付費差別要做在伺服器層**——藏按鈕不是限制，Server Action 裡的那個 if 才是。
3. **金流商可以換，原理不會換**——共享密鑰 + 簽章驗證 + 時間戳；你自己當過銀行，以後看誰的文件都不怕。
