# Walkthrough：在 Cursor 上把 TaskBoard 金流與部署一步一步做出來

> 這份文件帶你從 TaskBoard 基礎上，串接 Stripe 訂閱付款，完成測試模式的驗證、切成正式模式並部署上線——你會親手證明一件事：**不驗簽的 webhook 等於任何人都能自己幫自己升級方案，所以驗簽這一步不能跳。**
> 你會學到三件事：webhook 驗簽怎麼寫才真的擋得住偽造、測試模式與正式模式的金鑰為什麼要同步切換、額度限制為什麼一定要寫在伺服器端。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（這六件事先做，避免動手時卡住）

1. **申請 Stripe 測試帳號**——[stripe.com](https://stripe.com) 註冊自動進測試模式。建一個 Pro Plan 產品（$29/month recurring），記下 Price ID（`price_test_xxxxx`）。
2. **裝好 Stripe CLI**——`npm install -g @stripe/cli`，這樣才能本機測試 webhook 轉發：`stripe listen --forward-to localhost:3000/api/webhooks/stripe`。
3. **先準備好測試卡號清單**：4242 4242 4242 4242（成功）、4000 0025 0000 0002（拒絕）。
4. **Vercel 帳號準備好**——建議先綁好 GitHub，讓 `git push` 自動觸發部署。
5. **逐一瀏覽文中所有「✅ 預期看到」與「🧯 卡住的話」**，知道正常畫面長怎樣，判斷能力才快。
6. **提前跑一遍第 2 節 Webhook 驗簽的程式碼、第 4 節 Vercel 環境變數設定、以及 Stripe Dashboard Webhooks 事件通過的過程**，把成功的畫面截圖存起來。之後如果網路或 Stripe 突然出事，至少能靠截圖講清楚核心概念。

## 🗺️ 學習地圖（建議 3–4 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 25 分 | 閱讀理解（銀行電話比喻是核心，慢慢讀） |
| 第 0.1–0.3 節準備（環境變數、安裝 SDK） | 15 分 | 動手做（速度快） |
| 第 2 節付款鏈路完整演練 | 60 分 | 動手做（定價頁 → Checkout → webhook 驗簽，親自試這一幕最重要） |
| 第 3 節產品功能（同步方案、額度限制） | 30 分 | 閱讀理解 + 動手做（後端檢查方案的邏輯重要） |
| 第 4 節上線把關（Vercel 部署、正式環境金鑰切換） | 30 分 | 動手做（切環境變數、驗證 webhook） |
| 第 8 節動手練習（選做） | 30 分 | 動手做 |
| 第 9 節帶走的三句話 | 10 分 | 閱讀理解 |

---

## 🎬 開場故事：銀行打電話怎麼驗身分

想像一個場景：你開了一個線上收費服務。有人在你的網站上按『付款』，一秒鐘後，你接到一通電話。對方說『嗨，我是銀行，剛剛有個客戶付了 29 塊美金訂購 Pro 方案，你把他的帳號改成付費會員吧。』

現在有三個問題。第一：你怎麼知道這通電話真的來自銀行，而不是隔壁班的同學幫他朋友打來的？第二：假設你相信了，直接改了資料庫，會發生什麼？第三：怎麼才能防止冒充？

答案叫『驗簽』（signature verification）——就像銀行通知你前先會念出一串只有銀行和你知道的暗號。這份文件要教的就是一件事：**怎麼在程式碼裡寫出『驗暗號』的邏輯，確保假電話打不進來。**

webhook 和銀行電話的對照表：

| 旅館故事 | Stripe 金流 |
|---|---|
| 銀行打來的電話 | webhook 事件（customer.subscription.updated） |
| 銀行身份（誰在講話） | Stripe 的私密簽章（只有 Stripe 和你知道） |
| 你核對的暗號 | `STRIPE_WEBHOOK_SECRET`（環境變數裡的秘密） |
| 驗暗號的行為 | `stripe.webhooks.constructEvent` 函式 |
| 沒驗就改帳號 | 任何人都能用 curl 偽造付款事件→全崩 |
| 驗了才改帳號 | 假電話被擋下，資料庫安全 |

---

## 0. 課前準備

- 已完成第 22 章（TaskBoard 多租戶基礎）
- Stripe 測試帳號（[stripe.com](https://stripe.com) 註冊，自動進測試模式）
- Vercel 帳號（部署用）
- Node 20+、Cursor Pro

> 🔍 **名詞卡：Stripe**
> 白話：一個雲端付款公司。你的網站不用自己處理信用卡訊息（很危險，法律規範也嚴），把「收錢」這件事交給 Stripe，它幫你刷卡、處理退款、出帳單。你只需要會用 Stripe API。
> 比喻：你在便利商店開收銀機，但真正插卡刷卡的事轉包給專業的金流商。

> 🔍 **名詞卡：API Key（sk_test_ / pk_test_）**
> 白話：Stripe 發給你的兩把鑰匙。`sk_test_` 是「秘密金鑰」（你的伺服器用），`pk_test_` 是「公開金鑰」（前端可以看）。重點：secret key（sk）絕對不能洩露，public key（pk）隨便放。測試模式（test）和正式模式（live）各有一套。

### 0.1 Stripe 測試帳號設置

開 [Stripe Dashboard](https://dashboard.stripe.com)，左上角確認已切到 **Test mode**：

```
Test mode: [ON/OFF 開關]
```

建立一個 **Products and Prices**：

```
Product name: Pro Plan
Price: $29 / month（recurring）
Price ID: price_xxxxx（記下來）
```

再建一個測試用卡號清單（等一下測試會用）：

| 卡號 | 說明 |
|---|---|
| 4242 4242 4242 4242 | 成功 |
| 4000 0025 0000 0002 | 拒絕 |

✅ **預期看到**：Stripe Dashboard 左上角 **Test mode** 開關亮著；Products → 看得到剛建的「Pro Plan」；Webhooks 區塊暫時是空的（等等建立本機 listener 才會出現）。

🧯 **卡住的話**：Test mode 沒開（切到 Live 了），金鑰會是 `sk_live_` 開頭——**絕對停下來重新切回 Test**。真實卡號測試會是大麻煩。

### 0.2 環境變數（test mode）

`.env.local`（延續第 22 章的設定，新增 Stripe 部分）：

```bash
# 延續第 22 章的 Supabase 設定
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Stripe (Test mode，都是 sk_test_ 與 pk_test_ 開頭)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
NEXT_PUBLIC_STRIPE_PRICE_ID=price_test_xxxxx

# Webhook secret（稍後在 Stripe Dashboard → Webhooks 拿，現在留空）
STRIPE_WEBHOOK_SECRET=whsec_xxxx
```

看這個環境變數列表，有幾個要特別注意。前面有 `NEXT_PUBLIC_` 的——例如 `pk_test_` 這把鑰匙——是『公開鑰匙』，放在前端沒關係，所以加了前綴表示『會被打包進瀏覽器』。沒有 `NEXT_PUBLIC_` 的——例如 `sk_test_` 和 `STRIPE_WEBHOOK_SECRET`——是『秘密』，只有伺服器才能讀。

> 🔍 **名詞卡：環境變數（Environment Variable）**
> 白話：寫在「程式外面」、程式跑起來才讀的設定。好處：不用把祕密硬寫在程式碼裡（不然上傳 GitHub 就完蛋了），改環境就改設定值。

### 0.3 安裝 Stripe SDK

```bash
npm install stripe @stripe/stripe-js
```

✅ **預期看到**：`npm install` 完畢，`package.json` 新增了 `stripe` 和 `@stripe/stripe-js` 兩個 dependency。

---

## 1. 先懂概念：Webhook 驗簽是唯一的安全邊界

### 1.1 訂閱金流的完整往返路徑

我們先不碰程式碼，畫出整條路：使用者在網頁上按下『升級到 Pro』，會經過七個站點，每個站點會發生一件事。

```
站點一：使用者按「升級到 Pro」
  ↓
站點二：開 Stripe Checkout（一個 Stripe 自己的付款頁面）
  ↓
站點三：使用者輸入信用卡 → Stripe 處理付款
  ↓
站點四：付款成功 → Stripe 送 webhook 事件到你的 /api/webhooks/stripe（就像銀行打電話）
  ↓
站點五：你的伺服器收到事件，**驗簽**，確認真的是 Stripe 送的（驗暗號）
  ↓
站點六：信任 event.data，讀訂閱狀態，寫回資料庫（改 profiles.plan = 'pro'）
  ↓
站點七：UI 重新整理，方案升級✅
```

最容易掉的那一步就是**站點五：驗簽**。沒驗簽，任何人（包括黑客）都能偽造一條 webhook，假裝是 Stripe 送來的訂閱成功事件，把自己的 plan 字段改成 pro。

> ❓ **想一想**：如果跳過『驗簽』這一步，直接信任 webhook 的內容，最壞會發生什麼？
>
> **答案**：任何人都能用 curl 或代碼偽造一筆付款事件，自己幫自己升級成 Pro，公司一毛錢都收不到。

### 1.2 Webhook 驗簽三步驟（必背）

驗簽有三個步驟，一個都不能少。我們把銀行電話比喻對到程式碼上。

**第一步**：用 `req.text()` 保留原始 body 字串——不能先 JSON.parse。

```typescript
const body = await req.text();   // ← 重點：原始字串，不是 JSON object
```

為什麼？因為 Stripe 簽的是這串原始字節。一旦 parse 成 JSON 又序列化回去，空格／換行微小差異都會讓簽名驗不過。

> 🔍 **名詞卡：簽名（Signature）**
> 白話：用「只有你倆知道的暗碼」對一段訊息做數學運算，產出一個指紋。對方收到訊息後，用同一個暗碼重算一次，指紋若相同代表訊息沒被改過、也證明了是對方寄來的。郵局寄信時貼的封蠟就是古代的簽名。

**第二步**：呼叫 `stripe.webhooks.constructEvent`，把原始 body、簽名、webhook secret 都丟進去。

```typescript
const signature = req.headers.get("stripe-signature");
let event: Stripe.Event;
try {
  event = stripe.webhooks.constructEvent(
    body,                    // 原始字串
    signature!,              // Stripe 簽名（header 裡）
    webhookSecret            // 你的 webhook secret
  );
} catch (err) {
  // 驗簽失敗 → 直接回 400，不處理事件內容
  return NextResponse.json(
    { error: "Invalid signature" }, 
    { status: 400 }
  );
}
```

驗簽失敗 → 直接回 400，**不要嘗試從 body 裡掰出資料繼續處理**。

> 🔍 **名詞卡：constructEvent**
> 白話：Stripe SDK 裡驗簽的函式。它把 body、signature、secret 三樣輸入，內部用暗碼重算一遍簽名，對得上就 return event；對不上就 throw error。

**第三步**：只有驗簽通過，才能信任 `event.data` 裡的欄位。

```typescript
// 這一刻，event 才是真的來自 Stripe
if (event.type === 'customer.subscription.updated') {
  const subscription = event.data.object;
  // 信任 subscription.customer_id 與 subscription.status，寫回資料庫
}
```

注意程式碼的三層樓梯：第一層拿原始字串，第二層用暗碼驗，第三層才處理資料。少掉任何一層，驗簽就不成立。一個都不能跳。

### 1.3 Webhook 驗簽對照表

| ✗ 危險寫法 | ✓ 正確寫法 |
|---|---|
| 直接 `JSON.parse(body)` 取資料，跳過 Stripe SDK | `stripe.webhooks.constructEvent` 驗簽，SDK 內部會檢查 |
| 不檢查 `stripe-signature` header | 缺少 signature 直接回 400 |
| 用 `req.json()` 而非 `req.text()` | 用 `req.text()` 保留原始 body 字串 |

✅ **預期看到**：程式碼裡 `/api/webhooks/stripe` 路由最上面三行——`req.text()`、`headers.get('stripe-signature')`、`constructEvent`——全部都在。

🧯 **卡住的話**：如果想「為什麼不直接 `req.json()` 省一步？」——答案是 JSON.parse 的空格差異會讓簽名驗不過。用 `req.json()` 的話會收到 signature mismatch 的錯誤。

### 1.4 訂閱狀態的真實來源

一個重要的架構原則：**Stripe 是訂閱狀態的唯一真實來源，資料庫只是快取。**

不要讓前端查一次資料庫的 plan 欄位就判斷能不能用 Pro 功能。如果中間 webhook 沒處理好、或者使用者取消訂閱還沒同步回來，前端會看到過期的資料。

> 🔍 **名詞卡：快取（Cache）**
> 白話：存一份『昨天的新聞』在本地，查快一點。但『今天』有新聞時，快取還沒更新，讀到的就是舊的。金融相關一定要走正式來源（Stripe），不能靠快取（資料庫）判斷有沒有錢。

這也是為什麼第 22 章規則 6 強調「額度限制要寫在 Server Action」——Server Action 在讀取資料時是「即時」的，而且後面會補上 RLS 驗證；前端隱藏按鈕只是體驗，不是安全。

> ❓ **想一想**：假設 webhook 事件來了，但你的程式碼忘記更新資料庫的 plan 欄位。使用者重新整理頁面看到 plan 還是 free。這個時候，Stripe Dashboard 那邊的訂閱狀態其實是 active。誰才是真的真實來源？
>
> **答案**：Stripe。資料庫只是鏡像，out of sync 的時候不能信。

---

## 2. 階段一：付款鏈路（定價頁 → Checkout → Webhook 驗簽）⭐ 一定要親自試的一幕

### 2.1 資料庫：加 subscription 欄位

Supabase 裡，profiles 表要加欄位：

```sql
alter table profiles add column stripe_customer_id text;
alter table profiles add column stripe_subscription_id text;
alter table profiles add column plan text default 'free';  -- 'free' | 'pro'
alter table profiles add column plan_expires_at timestamptz;
```

對 Agent 說：

> 建立 supabase/migrations/004_stripe_columns.sql，在 profiles 表加 stripe_customer_id、stripe_subscription_id、plan、plan_expires_at 欄位。

現在我們在資料庫加四個欄位。最重要的是 `plan` 和 `stripe_subscription_id`——`plan` 存『當下展示給用戶的方案』，`stripe_subscription_id` 存『Stripe 那邊的訂閱單號』，這樣 webhook 來的時候知道要改誰。

### 2.2 定價頁

對 Agent 說：

> 在 app/pricing 新增定價頁面，展示 Free 與 Pro 方案，Pro 方案有個「升級」按鈕。點擊後開啟 Stripe Checkout。UI 用 shadcn/ui Button。

```typescript
// app/pricing/page.tsx 骨架
'use client';

import { useRouter } from 'next/navigation';

export default function Pricing() {
  const router = useRouter();

  const handleCheckout = async () => {
    // 稍後實作：呼叫 Server Action 建立 checkout session
  };

  return (
    <div className="grid grid-cols-2 gap-8">
      {/* Free plan card */}
      {/* Pro plan card with checkout button */}
    </div>
  );
}
```

✅ **預期看到**：`/pricing` 頁面打開，Free 和 Pro 兩張卡片並排，Pro 卡上有個「升級」按鈕（現在點還沒反應，因為還沒接 API）。

### 2.3 建立 Checkout Session 的 Server Action

對 Agent 說：

> 寫 app/actions/checkout.ts，Server Action `createCheckoutSession`：讀取登入使用者的 stripe_customer_id（沒有就先建），建立 Stripe Checkout session，回傳 checkout URL。使用者點擊會導到 Stripe 付款頁。

重點：

```typescript
'use server';
import Stripe from 'stripe';
import { createServerClient } from '@/utils/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function createCheckoutSession() {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('Not authenticated');

  // 查 profiles 拿 stripe_customer_id
  const { data: profile } = await supabase
    .from('profiles')
    .select('stripe_customer_id')
    .eq('id', user.id)
    .single();

  let customerId = profile?.stripe_customer_id;

  // 沒有 customer 就先建（Stripe 那邊建客戶檔）
  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email,
      metadata: { userId: user.id },
    });
    customerId = customer.id;

    // 寫回資料庫
    await supabase
      .from('profiles')
      .update({ stripe_customer_id: customerId })
      .eq('id', user.id);
  }

  // 建 checkout session
  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    mode: 'subscription',
    line_items: [
      {
        price: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID!,  // Pro plan price
        quantity: 1,
      },
    ],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
  });

  return session.url;
}
```

**補充**：實務上這裡容易踩的坑：`NEXT_PUBLIC_STRIPE_PRICE_ID` 要記錄下來，之後正式模式切換時會是另一個 ID；`success_url` 的 `{CHECKOUT_SESSION_ID}` 要用大括號，Stripe 會填實際值。

> 🔍 **名詞卡：Checkout Session**
> 白話：一個 Stripe 幫你準備的「交易單」。每一次使用者點「升級」，你就建一個 session，裡面記錄了「誰要付錢、付多少、付什麼產品」。使用者按下這個 session 的 URL，就被導到 Stripe 的付款頁面。

> 🔍 **名詞卡：Customer（客戶檔）**
> 白話：Stripe 對每個使用者的檔案。裡面存了「信用卡綁定了沒」、「歷史訂閱」、「聯絡信箱」等。建立好 customer 後，Stripe 才能在這個客戶上面綁訂閱。

✅ **預期看到**：點擊定價頁「升級」按鈕後，網址跳到 Stripe 的 Checkout（網域變成 `checkout.stripe.com` 或 `checkout-test.stripe.com`），看得到產品名稱 Pro Plan、金額 $29。

🧯 **卡住的話**：點擊按鈕沒反應——檢查 `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` 有沒有設定；錯誤訊息說 Price 不存在——檢查 `NEXT_PUBLIC_STRIPE_PRICE_ID` 指向的 Price 是否真的在 Stripe Dashboard 建立；Checkout 打不開——通常是 SDK 初始化失敗，先 reload 一次。

### 2.4 Webhook 驗簽——真正的安全邊界

建立 `/api/webhooks/stripe` 路由。**這是整個安全的關鍵。**

對 Agent 說：

> 寫 app/api/webhooks/stripe/route.ts，POST 端點。收到 webhook，先用 stripe.webhooks.constructEvent 驗簽，驗簽失敗回 400。驗簽通過後，如果是 customer.subscription.updated 事件，從 event.data.object 拿 subscription ID 與狀態，更新 profiles 的 stripe_subscription_id、plan 欄位。使用 service_role key 更新資料庫（只有 webhook 這個合法場景可以用 service_role）。

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@supabase/supabase-js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = req.headers.get('stripe-signature');

  // 第一步：驗簽
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature!, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  // 第二步：只有驗簽通過才處理事件
  if (event.type === 'customer.subscription.updated') {
    const subscription = event.data.object as Stripe.Subscription;

    // 查 Stripe customer 身上的 metadata.userId，找回 profile
    const customer = await stripe.customers.retrieve(
      subscription.customer as string
    );
    const userId = (customer.metadata as any)?.userId;

    if (!userId) {
      console.warn('Subscription event has no userId');
      return NextResponse.json({ received: true });
    }

    // 用 service_role 更新 profiles（只有 webhook 場景合法）
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    const plan = subscription.status === 'active' ? 'pro' : 'free';
    await supabase
      .from('profiles')
      .update({
        stripe_subscription_id: subscription.id,
        plan: plan,
        plan_expires_at: new Date(subscription.current_period_end * 1000),
      })
      .eq('id', userId);

    console.log(`Updated user ${userId} to plan: ${plan}`);
  }

  // 第三步：回 200 告訴 Stripe 事件已收到
  return NextResponse.json({ received: true });
}
```

**這是整章最重要的一段**：`constructEvent` 驗簽不能跳過。

現在看這個路由，它做三件事。第一，拿原始 body；第二，用 `constructEvent` 驗暗號；第三，只有驗過才讀裡面的資料。銀行打電話時，第一個動作就要驗身份。

> 🔍 **名詞卡：Service Role Key**
> 白話：Supabase 發給後端的『萬能鑰匙』，能繞過所有 RLS 政策。**絕對不能放進前端**（沒有 `NEXT_PUBLIC_` 前綴的就是伺服器專用）。只有伺服器端的『背景工作』（例如 webhook）才能用它，因為這些工作不是使用者代辦，是系統自動代辦。

#### 測試本機 Webhook（用 Stripe CLI）

開一個新的終端機視窗，跑 Stripe CLI：

```bash
stripe login
# 會開瀏覽器讓你登入 Stripe 帳號
stripe listen --forward-to localhost:3000/api/webhooks/stripe
# 終端機印出 webhook secret：whsec_test_xxxxx
```

複製那個 secret，貼進 `.env.local`：

```bash
STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
```

重啟 dev server（`npm run dev`）。

✅ **預期看到**：
1. `stripe listen` 終端機顯示 `Listening for events...`
2. 回到定價頁，點「升級」→ Stripe Checkout 打開
3. 輸入測試卡 4242 4242 4242 4242（卡有效期隨便填，CVC 任意三碼）
4. 按「Subscribe」→ 頁面重導回 dashboard
5. 最重要：**stripe listen 那個終端機應該列印出 `> webhook received: customer.subscription.updated`**——代表 webhook 真的送過來了，而且驗簽通過
6. 查資料庫（或 dashboard 頁面），profiles.plan 應該變成 `pro`

🧯 **卡住的話**：
- `stripe listen` 沒印出 webhook——代表驗簽失敗（通常是 secret 貼錯）。重新貼一次，重啟 dev server。
- webhook 印出來了但資料庫 plan 沒改——檢查 console 有沒有 error；檢查 customer metadata 裡有沒有 userId；檢查 Supabase 那邊 RLS 有沒有擋住 service_role 的更新（正常情況下不會）。如果還是不動，靠預先存好的「通過」截圖來說明核心概念就好。

---

## 3. 階段二：產品功能（同步訂閱、額度限制、Portal）

### 3.1 前端讀取用戶方案

Server Component 裡讀 profile 的 plan：

```typescript
// app/dashboard/page.tsx
const { data: profile } = await supabase
  .from('profiles')
  .select('plan')
  .eq('id', user.id)
  .single();

// 傳給 Client Component 或直接渲染
const isPro = profile?.plan === 'pro';
```

這邊很簡單：Server Component 讀資料庫，直接知道使用者是 free 還是 pro。重點在下一個段落。

### 3.2 額度限制在 Server Action 層

假設要加一個 Pro 專屬功能「匯出 CSV」。

對 Agent 說：

> 做一個 Pro 專屬的匯出 CSV 功能。前端有 Pro Badge，非 Pro 點擊導向 /pricing。Server Action 最開頭檢查使用者方案，非 pro 回傳 { success: false, error: 'PLAN_REQUIRED' }。不能只靠前端隱藏按鈕。

```typescript
// app/actions/export-csv.ts
'use server';

export async function exportTasksCSV(teamId: string) {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) throw new Error('Not authenticated');

  // ← 這裡一定要做：檢查方案
  const { data: profile } = await supabase
    .from('profiles')
    .select('plan')
    .eq('id', user.id)
    .single();

  if (profile?.plan !== 'pro') {
    return { success: false, error: 'PLAN_REQUIRED' };
  }

  // 才能執行 Pro 功能
  const { data: tasks } = await supabase
    .from('tasks')
    .select('*')
    .eq('team_id', teamId);

  // 產生 CSV...
  return { success: true, csv: csvData };
}
```

前端：

```typescript
const handleExport = async () => {
  const result = await exportTasksCSV(teamId);
  if (!result.success) {
    if (result.error === 'PLAN_REQUIRED') {
      router.push('/pricing');
    }
    return;
  }
  // 下載 CSV
};
```

第 22 章學過：『前端隱藏按鈕不是安全』。這裡示範怎麼做才是安全——Server Action 最前面第一句就檢查 plan，免費帳號根本進不了後面的邏輯。

> 🔍 **名詞卡：額度限制（Entitlement）**
> 白話：『這個功能你有沒有權利用』的檢查。分兩層：前端檢查（快，但可繞過）、後端檢查（慢，但鎖死）。必須後端有。

> ❓ **想一想**：假設用 DevTools 把前端的 Pro Badge 改成顯示，然後按下『匯出』按鈕。後端會怎樣？
>
> **答案**：Server Action 一樣檢查 plan，發現是 free，直接回 `error: 'PLAN_REQUIRED'`。修改前端 UI 改不了後端邏輯，所以是安全的。

✅ **預期看到**：用 free 帳號點「匯出 CSV」→ 被導回 /pricing；升級到 pro 後再點 → 成功匯出（或至少沒有被擋）。

### 3.3 Customer Portal（用戶管理訂閱）

Stripe Customer Portal 讓使用者自己管理付款方式、下載發票、取消訂閱。

對 Agent 說：

> 在 /api/stripe-portal 新增 Server Action 或 API Route，用 stripe.billingPortal.sessions.create 建立 portal session，重導使用者到 Stripe 管理頁。

```typescript
// app/api/stripe-portal/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createServerClient } from '@/utils/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: NextRequest) {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  // 查 stripe_customer_id
  const { data: profile } = await supabase
    .from('profiles')
    .select('stripe_customer_id')
    .eq('id', user.id)
    .single();

  if (!profile?.stripe_customer_id) {
    return NextResponse.json(
      { error: 'No Stripe customer found' },
      { status: 400 }
    );
  }

  // 建 portal session
  const portalSession = await stripe.billingPortal.sessions.create({
    customer: profile.stripe_customer_id,
    return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard`,
  });

  return NextResponse.json({ url: portalSession.url });
}
```

> 🔍 **名詞卡：Billing Portal**
> 白話：Stripe 為你準備的「使用者自助後台」。你不用自己寫「更改信用卡」、「下載發票」、「取消訂閱」的功能，Stripe 都做好了。使用者點一個連結就被導進去。

✅ **預期看到**：Pro 使用者帳號頁面有「管理訂閱」按鈕，點擊後跳到 Stripe 的 portal 頁面，能看到訂閱狀態、信用卡、發票清單、取消訂閱按鈕等。

---

## 4. 階段三：上線把關（部署 Vercel、正式 webhook、Review）

### 4.1 測試模式與正式模式的獨立性

Stripe 的測試模式（test）與正式模式（live）**完全獨立**，有各自的：

- API key（`sk_test_` vs `sk_live_`、`pk_test_` vs `pk_live_`）
- Products & Prices（test 模式的 Price ID vs live 模式的 Price ID）
- Webhooks（test mode webhook vs live mode webhook）

**常見坑**：切到正式模式時只改了 `STRIPE_SECRET_KEY`，忘了改 Price ID 和 webhook secret，結果金鑰對不上、webhook 驗簽永遠失敗。

想像 Stripe 是兩個世界：test 世界和 live 世界。test 世界裡所有東西都是假的——假卡號 4242...，假 secret key，假 products。live 世界才連真的金流。當你要上線時，不是『切一個開關』，而是『把三樣全部切過去』：金鑰、Price、webhook。任何一樣留在 test 世界，整個就聯動失敗。

> 🔍 **名詞卡：測試模式 vs 正式模式**
> 白話：測試模式：全是假錢，卡號 4242... 永遠成功，你可以試玩。正式模式：連真錢，會真的扣使用者的信用卡。除非確定完全測好，否則絕對不要切正式模式。

### 4.2 上線前檢查清單

切到正式模式前，逐條確認：

| 檢查項目 | 確認方式 |
|---|---|
| 金鑰是否為正式模式 | `STRIPE_SECRET_KEY` 與 `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` 都是 `sk_live_` 與 `pk_live_` 開頭 |
| Webhook 是否驗簽 | 檢查 `/api/webhooks/stripe` 內有 `constructEvent`，沒有 `JSON.parse(body)` |
| 額度限制在伺服器端 | Server Action 層有方案檢查，不是只靠前端隱藏按鈕 |
| 測試卡都測過 | 4242... 成功、4000...0002 拒絕，各測過一次 |
| Price ID 已更新 | `NEXT_PUBLIC_STRIPE_PRICE_ID` 指向正式模式的 Price ID（不同於 test mode） |
| Webhook endpoint 已建 | Stripe Dashboard → Webhooks → 正式模式有新的 endpoint，secret 與環境變數對上 |

上線前這六項逐條過。特別是後三項——金鑰、Price、webhook——最容易漏。漏了一項，正式環境金流就不通。

✅ **預期看到**：逐項確認後，清單六個打勾。

🧯 **卡住的話**：某一項確認不了（例如 Price ID 記不起來）——回 Stripe Dashboard 查；webhook endpoint 沒建——建一個（照著流程走即可）。

### 4.3 部署到 Vercel

```bash
git add .
git commit -m "Stripe integration"
git push
```

Vercel Dashboard → Environment Variables，新增（對應正式模式）：

```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
NEXT_PUBLIC_STRIPE_PRICE_ID=price_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_live_xxxxx
```

部署後驗證：

```bash
npm run build      # 本地 build 一次，確認 env 都有
curl https://your-domain.vercel.app/health  # 簡單的 health check
```

✅ **預期看到**：Vercel Dashboard 顯示「Deploy successful」綠燈；`npm run build` 成功完畢（沒有環境變數缺失的錯誤）。

🧯 **卡住的話**：build 失敗說環境變數缺失——檢查 Vercel Dashboard 有沒有真的設定；部署成功但 API 回 500——檢查 webhook 驗簽的 secret 有沒有改成正式模式的。

### 4.4 Webhook 指向正式環境

Stripe Dashboard（正式模式）→ Webhooks → Add endpoint：

```
Endpoint URL: https://your-domain.vercel.app/api/webhooks/stripe
Event types: customer.subscription.updated, customer.subscription.deleted
```

記下產生的 Webhook Secret（`whsec_live_`），貼進 Vercel 環境變數 `STRIPE_WEBHOOK_SECRET`。

重點：每一次切模式（test → live），webhook secret 也要新建。拿著舊的 test secret 去 live 環境，驗簽會永遠失敗。

✅ **預期看到**：Stripe Dashboard Webhooks 區塊，正式模式那邊有一個新的 endpoint（網域指向 Vercel），Status 顯示綠色（表示有通訊）。

### 4.5 測試正式環境的付款

用實際信用卡或 Stripe 提供的測試卡，完整走一遍：

1. 訪問正式環境的 /pricing
2. 點「升級」→ Stripe Checkout
3. 輸入卡號（測試卡也可以）→ 付款
4. 回到 dashboard，plan 欄位應已變成 `pro`
5. 檢查 Stripe Dashboard 的 Webhooks → Events，應看到 `customer.subscription.updated` 事件且 status 200

✅ **預期看到**：Stripe Checkout 能打開、卡號能刷、回頁面後 plan 變 pro、Webhook Events 列表顯示 status 200。

🧯 **卡住的話**：Checkout 打不開（金鑰錯誤或 Price 不存在）、webhook 事件回 400（驗簽失敗，通常是 secret 對不上）、plan 沒改（可能 webhook handler 邏輯有 bug）。先看 Stripe Dashboard Events 的 response 狀態碼定位問題。

---

## 5. 情境演練：付了錢方案沒更新

**情境**：上線後第一位付費使用者回報，Stripe 說付款成功了，但 dashboard 裡 plan 還是 `free`。

**排錯步驟**：現在真的卡關了。使用者說他付錢了，Stripe 後台確認收到了，但資料庫沒反應。怎麼查？

1. **先去 Stripe Dashboard 的 Webhooks 查事件記錄**：
   - Events → 看 `customer.subscription.updated` 的 response status
   - 如果回 **400**，代表驗簽掛了（最常見）
   - 如果回 **200**，代表收到了，要查資料庫

2. **驗簽掛的常見原因**：
   - `.env.local` 的 `STRIPE_WEBHOOK_SECRET` 複製錯誤
   - 切到正式模式後沒建新的 webhook endpoint（拿了測試模式的 secret）
   - 程式碼用了 `req.json()` 而不是 `req.text()`

3. **如果回 200 但資料庫沒更新**：
   - 查 webhook handler 有沒有吃到 event 裡的 userId
   - `stripe.customers.retrieve(customer_id)` 是否回傳了正確的 metadata
   - 資料庫是否有 RLS 政策擋住更新（用 service_role key 才能更新）

4. **最終檢查**：
   - Stripe Dashboard → 該 customer 的 subscription status 是 `active`
   - 資料庫 profiles → 該使用者的 plan 欄位是 `pro`

如果都 200 了還是改不了，通常是上面某一步環境變數對不上。

> 🔍 **名詞卡：冪等性（Idempotency）**（如原文有相關內容）
> 白話：「做一次和做十次結果一樣」。在金流裡很重要——假設同一筆訂閱事件 webhook 被傳了兩次（網路重試），你不想使用者被扣兩次錢。所以後端檢查「這個 subscription_id 我之前改過沒」，改過就跳過。

---

## 6. 驗收清單

- [ ] `.env.local` 有 Stripe test mode 的 key 與 webhook secret
- [ ] profiles 表新增了 stripe_customer_id、stripe_subscription_id、plan、plan_expires_at 欄位
- [ ] /pricing 頁面顯示 Free 與 Pro 方案，Pro 有「升級」按鈕
- [ ] 點「升級」能開啟 Stripe Checkout（test mode 卡號 4242... 能走到成功頁）
- [ ] `stripe listen` 跑著時，完整走過一遍付款流程，終端機看得到 webhook 事件
- [ ] `/api/webhooks/stripe` 用 `constructEvent` 驗簽，驗簽失敗回 400
- [ ] 付款成功後 webhook 事件被正確處理，profiles 的 plan 變成 `pro`
- [ ] Pro 專屬功能的 Server Action 最開頭有方案檢查，免費帳號繞過失敗
- [ ] Vercel 環境變數已設正式模式的 key（`pk_live_`、`sk_live_`）
- [ ] Stripe Dashboard 正式模式已建 webhook endpoint，指向 Vercel URL
- [ ] 正式環境用真實（或測試）卡號完整測過一遍付款流程
- [ ] Stripe Webhooks Events 的正式環境事件回 status 200

---

## 7. 常見坑排錯速查

| 問題 | 排錯方式 |
|---|---|
| Checkout 點了沒反應 | 檢查 `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` 有沒有設、有沒有 `NEXT_PUBLIC_` 前綴 |
| Checkout 能開但付款失敗 | 檢查 `NEXT_PUBLIC_STRIPE_PRICE_ID` 指向的 price 是否真的存在（test mode vs live mode） |
| 付款成功但 plan 沒改 | Stripe Dashboard Webhooks 查 event status；如果 400 就是驗簽掛了；如果 200 查資料庫有沒有 RLS 擋住 |
| Webhook 驗簽永遠 400 | 檢查 `STRIPE_WEBHOOK_SECRET` 複製無誤、檢查程式碼有沒有用 `req.text()` 而不是 `req.json()` |
| 切到正式模式後什麼都不動 | 金鑰、Price ID、webhook secret 三者必須全部換成正式模式的；任何一個是 test 都會聯動失敗 |
| 前端改個 DOM 就能用 Pro 功能 | Server Action 層沒有做方案檢查，只靠前端隱藏按鈕 |
| 正式環境金流還是往 test mode 發送 | 環境變數設了 test key，Vercel build 沒有重新部署，old key 還在用 |
| Customer 找不到 | 建 checkout session 時沒有建 customer，或者 customer metadata 沒有 userId |

---

## 8. 動手練習

### 練習 1：拆掉 webhook 驗簽，用 curl 偽造一筆付款（約 25 分 · 中級）

**目的**：親手證明沒驗簽的 webhook 等於開放任何人幫自己升級成 Pro。

#### 怎麼做

1. **先 commit 一次**，確保等一下改得回來
   ```bash
   git add .
   git commit -m "Before webhook security test"
   ```

2. **把 `constructEvent` 換成 `JSON.parse(body)`**

   找到 `/api/webhooks/stripe` 路由，改成：
   ```typescript
   let event: Stripe.Event;
   try {
     const parsed = JSON.parse(body);  // ← 危險寫法
     event = parsed;
   } catch (err) {
     return NextResponse.json(
       { error: "Invalid JSON" },
       { status: 400 }
     );
   }
   ```

3. **用 curl 送一段假的訂閱事件**

   替換 `YOUR_USER_ID` 與本機 URL：
   ```bash
   curl -X POST http://localhost:3000/api/webhooks/stripe \
     -H "Content-Type: application/json" \
     -d '{
       "type": "customer.subscription.updated",
       "data": {
         "object": {
           "id": "sub_fake123",
           "customer": "cus_fake456",
           "status": "active",
           "current_period_end": 9999999999
         }
       }
     }'
   ```

   查看資料庫，該使用者的 plan 應該變成 `pro`。

4. **把驗簽加回去**

   改回 `stripe.webhooks.constructEvent`。

5. **重送同一段 curl**

   這次應該回傳 **400 Invalid signature**，資料庫的 plan 不會被改。

#### 完成標準

- [ ] 能貼出成功（plan 變 pro）與 400（驗簽失敗）兩種回應
- [ ] 能說明驗簽擋在 `constructEvent` 這一步
- [ ] 驗簽已經加回去，`.env.local` 或生產環境都沒有危險寫法

#### Prompt 範本

```
給我一段 curl 指令，對本機的 /api/webhooks/stripe 送出一個假的 customer.subscription.updated 事件，
內容要能讓程式把某個使用者的 plan 改成 pro。同時說明加回 stripe.webhooks.constructEvent 之後，
這段 curl 會在哪一行被擋下、回傳什麼狀態碼。
```

---

### 練習 2：做一個 Pro 專屬功能，並在後端也擋住（約 30 分 · 中級）

**目的**：重點不是那個功能，是「前端隱藏按鈕不算限制」這件事要做到 Server Action。

#### 怎麼做

1. **挑一個小功能當 Pro 專屬**，例如「匯出 CSV」、「團隊分析」、「批量標籤」等
   - 範圍要小，讓一節課做得完
   - 最好是現有頁面能輕易加上去的

2. **前端加 Pro Badge**

   ```typescript
   {isPro ? (
     <Button onClick={handleExport}>匯出 CSV</Button>
   ) : (
     <Button
       disabled
       onClick={() => router.push('/pricing')}
       className="opacity-50"
     >
       匯出 CSV（Pro 專屬）
     </Button>
   )}
   ```

3. **Server Action 最開頭檢查方案**

   ```typescript
   export async function exportCSV(teamId: string) {
     const supabase = await createServerClient();
     const { data: { user } } = await supabase.auth.getUser();

     // ← 第一行：檢查方案
     const { data: profile } = await supabase
       .from('profiles')
       .select('plan')
       .eq('id', user.id)
       .single();

     if (profile?.plan !== 'pro') {
       return { success: false, error: 'PLAN_REQUIRED' };
     }

     // 才能執行功能
     // ...
   }
   ```

4. **用免費帳號直接呼叫該 Server Action 驗證**

   在瀏覽器 DevTools Console 或寫一個測試：
   ```typescript
   const result = await exportCSV('team-id-here');
   console.log(result);  // { success: false, error: 'PLAN_REQUIRED' }
   ```

   應該回傳錯誤，**不是成功執行**。

#### 完成標準

- [ ] 前端有 Pro Badge 或清楚的標示
- [ ] Server Action 有方案檢查（不是只靠前端 disabled 按鈕）
- [ ] 免費帳號繞過失敗（直接呼叫 Server Action 被拒）

#### Prompt 範本

```
幫我把「匯出 CSV」做成 Pro 專屬功能。前端要有 Pro Badge，非 Pro 使用者點擊導向 /pricing；
同時在對應的 Server Action 最前面檢查使用者方案，不是 pro 就回傳 { success: false, error: 'PLAN_REQUIRED' }。
最後告訴我怎麼用免費帳號直接呼叫這個 Server Action 來驗證後端真的擋得住。
```

---

### 練習 3：用 stripe trigger 模擬取消訂閱並驗證降級（約 20 分 · 入門）

**目的**：練的是把整條鏈路跑一次：Stripe 事件 → webhook → 資料庫 → 畫面。

#### 怎麼做

1. **開 stripe listen，把事件轉發到本機**

   ```bash
   stripe listen --forward-to localhost:3000/api/webhooks/stripe
   ```

   終端機會印出一個 webhook secret（`whsec_test_`），複製起來。

2. **貼進 `.env.local`**

   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
   ```

   重啟 dev server。

3. **跑 stripe trigger 模擬取消訂閱事件**

   ```bash
   stripe trigger customer.subscription.deleted
   ```

   應該看到 stripe listen 的終端機裡顯示事件送達。

4. **查資料庫確認 plan 已降回 free**

   ```sql
   select id, plan, plan_expires_at from profiles order by created_at desc limit 1;
   ```

   plan 欄位應該變成 `free`（或看 webhook handler 怎麼實作）。

5. **重新整理頁面確認 UI 同步**

   Pro 功能應該被收回，回到 Free 狀態。

#### 完成標準

- [ ] 終端機看得到事件（`stripe listen` 顯示 Webhook received）
- [ ] 資料庫 plan 變 free（subscription.deleted 事件被正確處理）
- [ ] 畫面同步收回權限（重新整理後 Pro 功能消失或被 disabled）

#### Prompt 範本

```
教我用 Stripe CLI 完成三件事：把事件轉發到本機的 webhook 端點、觸發一次
customer.subscription.deleted、確認我的程式有處理這個事件型別。如果我的 webhook 只處理了
customer.subscription.updated，請告訴我要補哪一段。
```

---

## 9. 帶走的三句話

如果今天只能記住三件事，就這三句。

1. **Webhook 一定要用 `constructEvent` 驗簽，且用原始 body**——沒驗簽任何人都能偽造付費事件；先 `JSON.parse` 再簽名會因字節差異驗不過；`req.text()` 拿原始字串是前置條件。銀行打電話時，第一個動作就要驗身份。

2. **訂閱狀態的唯一真實來源是 Stripe，資料庫只是快取**——Server Action 要即時查方案而不是信任前端傳來的資料；額度限制要寫在伺服器端，前端隱藏按鈕只是體驗，不是安全。Stripe Dashboard 記錄的狀態才是黃金版本。

3. **測試模式與正式模式的金鑰、Price ID、webhook 完全獨立**——切到正式上線時要同步切三樣（API key、Price ID、webhook secret），任何一個落在測試模式都會聯動失敗。上線前用檢查清單逐條確認，再用 Agent Review 做一次 Deep 安全掃描。
