# 🐳 Docker 預載服務清單與架構解析（給學生的環境指南）

> **這份文件的目的**：向同學白話解釋「為什麼課程要用 Docker？」、「Docker 裡面到底裝了什麼東西？」以及「這些服務分別在哪幾門課會用到？」。

---

## 🍱 1. 為什麼我們要用 Docker？（生活比喻）

在過去，如果要學習一個全端專案，你的電腦需要安裝：
PostgreSQL 資料庫、Node.js 伺服器、Redis 快取、身分驗證伺服器、郵件測試工具……
這樣做會產生兩個巨大痛點：
1. **環境污染**：電腦被裝了一堆背景軟體，刪不乾淨又吃記憶體。
2. **「在我電腦上明明可以」**：因為每個人的作業系統、版本相依性不同，常常卡在「為什麼你的裝得起來，我的跳錯誤？」。

**Docker 就像是一個「乾淨的便當盒」**。
所有的資料庫和伺服器都被打包在這個便當盒裡，盒內互不干擾，也不會弄髒你的個人電腦。課程結束後只要把便當盒收掉，電腦依然乾乾淨淨！

---

## 📦 2. 課程中 Docker 安裝了哪些服務？

在我們的實戰課程中，Docker 主要提供兩大核心生態系統：**Supabase 本地全端套裝** 與 **Neo4j 知識圖譜資料庫**。

### 🅰️ Supabase 本地全端服務群（[Project 2 多租戶任務板](../project-2-taskboard-saas/README.md) 使用）

Supabase 是一個開源的 Firebase / 後端替代方案。在本地啟動時，Docker 會一次幫你跑起以下 8 個緊密配合的微服務容器：

| 容器映像檔 (Image) | 角色比喻 | 做什麼用？ | 本機存取埠 (Port) |
|---|---|---|---|
| **`supabase/postgres:17`** | **保險庫本體** | 核心 PostgreSQL 17 資料庫，存放會員、團隊、看板任務，並執行 RLS（Row-Level Security）行級資料安全隔離。 | `localhost:54322` |
| **`supabase/studio`** | **視覺化管理櫃台** | 瀏覽器網頁後台（類似 PgAdmin），讓你能用滑鼠直接檢視資料表、編輯 RLS 政策與監控日誌。 | [http://localhost:54323](http://localhost:54323) |
| **`supabase/gotrue`** | **門禁身分檢查員** | 身分驗證系統（Auth），負責處理使用者註冊、登入、密碼加密與簽發 JWT 安全權杖。 | 內部通訊 |
| **`supabase/kong`** | **大樓接待總機** | API Gateway，統一對外入口，將前端的請求正確轉發給資料庫、Auth 或 Storage。 | `http://localhost:54321` |
| **`supabase/postgrest`** | **自動翻譯官** | 自動將 PostgreSQL 表格轉換成標準 RESTful API，讓前端能直接以 JSON 格式讀寫資料。 | 內部通訊 |
| **`supabase/storage-api`** | **檔案置物櫃** | 物件儲存服務，負責處理圖片上傳（例如使用者頭像、任務附件檔案）。 | `http://localhost:54321/storage` |
| **`supabase/realtime`** | **即時廣播電台** | WebSocket 服務，當看板上的任務被其他人拖曳或修改時，畫面會即時同步跳動。 | 內部通訊 |
| **`supabase/mailpit`** | **本機測試郵筒** | 本地郵件攔截器。當你在練習註冊收到驗證信時，信件會直接被抓到此網頁中，不用真的發送 Email。 | [http://localhost:54324](http://localhost:54324) |

---

### 🅱️ Neo4j 圖形資料庫（[Project 14 GraphRAG 知識圖譜問答](../project-14-graphrag-chatbot/README.md) 使用）

| 容器映像檔 (Image) | 角色比喻 | 做什麼用？ | 本機存取埠 (Port) |
|---|---|---|---|
| **`neo4j:5`** | **偵探案情紅線板** | 專門儲存「實體（人/事/物）」與「關聯（誰牽連誰）」的圖形資料庫。在 Project 14 中用來實現比純向量檢索更聰明的 GraphRAG 多跳推理。 | [http://localhost:7474](http://localhost:7474) (Web 介面)<br>`bolt://localhost:7687` (API 協議) |

---

## 🕹️ 3. 常用操作與指令速查

平時課堂遙控器（`./demo.sh`）會自動幫你管理容器，但如果你想手動操作，可以記住這三組指令：

### 1. 查看目前 Docker 有哪些服務正在跑
```bash
docker ps
```
> **預期畫面**：看到 `supabase_*` 或 `neo4j` 的容器標示為 `Up (healthy)`。

### 2. 手動啟動 / 查看 / 停止 Project 2 本地 Supabase
```bash
cd project-2-taskboard-saas/taskboard

# 啟動所有 Supabase 容器（第一次啟動約需 1-2 分鐘）
npx supabase start

# 查看連線網址與 API 金鑰
npx supabase status

# 課後不用時停止服務（釋放電腦記憶體）
npx supabase stop
```

---

## 🧯 4. 常見問題與備援指南 (FAQ)

#### Q1：我的電腦記憶體較小，跑 Docker 會不會卡？
> **解答**：不會。平時若沒有在上課，只要執行 `npx supabase stop`，容器就會完全停止，不佔用任何 CPU 與記憶體。

#### Q2：公司筆電資安限制，無法安裝 Docker 怎麼辦？
> **解答**：別擔心！所有涉及 Docker 的專案都有**「零安裝雲端備援方案」**：
> - **Project 2**：可以直接到 [Supabase 官網](https://supabase.com) 註冊免費雲端專案，把 `.env.local` 指向雲端網址即可。
> - **Project 14**：可以直接使用 [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/) 免費雲端圖資料庫。
