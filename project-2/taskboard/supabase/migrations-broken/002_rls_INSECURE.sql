-- ⚠️⚠️⚠️ 002_rls_INSECURE.sql —— 這是「漏洞版」，課堂用的反面教材 ⚠️⚠️⚠️
--
-- 這個資料夾叫 migrations-broken，永遠不會被 npm run db:push 套用。
-- 它只會被 `npm run demo:break` 拿去投影，示範一個真實世界最常見的災難：
--
--   「我有開 RLS 啊！」——RLS 確實 Enabled，Dashboard 上也是綠色的「RLS enabled」標籤，
--   Supabase security advisor 也不會警告，看起來一切正常。
--   但政策條件寫成 using (true)，翻成中文就是「只要是 true 就放行」＝「永遠放行」。
--   跟完全沒開 RLS 幾乎沒有差別。
--
-- 這就是為什麼「開了 RLS」不等於「安全」：條件裡有沒有 auth.uid() 才是真正的鎖。
-- 對照 supabase/migrations/002_rls.sql 看差別。

-- profiles：想說「大家都看得到彼此的名字，方便嘛」——於是全世界的 profile 都露了
create policy "profiles: read all" on profiles for select using (true);
create policy "profiles: update all" on profiles for update using (true) with check (true);

-- teams：想說「反正前端只會查自己的團隊」——前端的 where 是禮貌，不是安全
create policy "teams: read all" on teams for select using (true);
create policy "teams: insert all" on teams for insert with check (true);

-- team_members：任何登入者都能把自己塞進任何團隊、也能把別人踢出任何團隊
create policy "team_members: read all" on team_members for select using (true);
create policy "team_members: insert all" on team_members for insert with check (true);
create policy "team_members: delete all" on team_members for delete using (true);

-- tasks：災情最慘的一張表。任何拿到 anon key 的人（按 F12 就撿得到）
-- 都能讀走、竄改、刪掉全公司每一個團隊的任務。
create policy "tasks: read all" on tasks for select using (true);
create policy "tasks: insert all" on tasks for insert with check (true);
create policy "tasks: update all" on tasks for update using (true) with check (true);
create policy "tasks: delete all" on tasks for delete using (true);

-- invites：連邀請碼都能整包撈走，等於所有團隊的門都開著
create policy "invites: read all" on invites for select using (true);
