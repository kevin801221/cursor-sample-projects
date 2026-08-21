-- 002_rls.sql：每張表都用 auth.uid() 劃界

-- helper：查「我屬於哪些團隊」。包成 security definer 是因為 team_members
-- 的政策若直接子查詢 team_members 自己，會觸發 infinite recursion 錯誤；
-- security definer 讓函式以擁有者權限執行、跳過 RLS，斬斷遞迴。
create or replace function my_team_ids()
returns setof uuid language sql security definer stable
set search_path = public
as $$ select team_id from team_members where user_id = auth.uid() $$;

-- profiles：只能看到／更新自己的
create policy "profiles: read own"   on profiles for select using (auth.uid() = id);
create policy "profiles: update own" on profiles for update using (auth.uid() = id)
  with check (auth.uid() = id);

-- teams：只看得到自己加入的；任何登入者可建團隊（owner 必須是自己）
create policy "teams: member can read" on teams for select
  using (id in (select my_team_ids()) or owner_id = auth.uid());
create policy "teams: create own" on teams for insert
  with check (owner_id = auth.uid());

-- team_members：只看得到同團隊名單；insert 政策放 003（規則 5：要驗邀請碼）
create policy "team_members: member can read" on team_members for select
  using (team_id in (select my_team_ids()));

-- tasks：四條政策都以「是否為該 team 成員」為界
create policy "tasks: member can read"   on tasks for select
  using (team_id in (select my_team_ids()));
create policy "tasks: member can insert" on tasks for insert
  with check (team_id in (select my_team_ids()) and created_by = auth.uid());
create policy "tasks: member can update" on tasks for update
  using (team_id in (select my_team_ids()))
  with check (team_id in (select my_team_ids()));
create policy "tasks: member can delete" on tasks for delete
  using (team_id in (select my_team_ids()));

-- invites：不開 select，邀請碼不可枚舉；驗證只發生在 003 的 with check 子查詢裡
