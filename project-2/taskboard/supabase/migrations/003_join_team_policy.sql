-- 003_join_team_policy.sql
-- 情境：任何登入者呼叫 API 硬塞 team_id，想加入不屬於自己的團隊。誰來擋？
-- 答案：team_members 的 insert 政策。前端有沒有那顆按鈕，完全不影響這道防線。

-- helper (1)：is_team_owner —— 解 4.2 講過的 infinite recursion。
-- 政策裡若直接寫 exists (select 1 from team_members ...)，等於「查名冊要先過名冊自己的鎖」，
-- 資料庫會報 infinite recursion detected in policy。包成 security definer 就斬斷遞迴。
create or replace function is_team_owner(target_team uuid)
returns boolean language sql security definer stable
set search_path = public
as $$
  select exists (
    select 1 from team_members tm
    where tm.team_id = target_team
      and tm.user_id = auth.uid()
      and tm.role = 'owner'
  )
$$;

-- helper (2)：invite_is_valid —— 同一個理由的另一種版本。
-- invites 開了 RLS 卻「零 select 政策」（刻意的：邀請碼不可枚舉），
-- 所以政策裡直接子查詢 invites 會被 invites 自己的鎖擋成 false，任何人都加不進來。
-- 包成 security definer 讓這一次比對繞過 invites 的鎖，
-- 驗證依然 100% 發生在資料庫層，而且 invites 對前端仍然完全查不到。
create or replace function invite_is_valid(target_team uuid)
returns boolean language sql security definer stable
set search_path = public
as $$
  select exists (
    select 1 from invites
    where code = current_setting('request.invite_code', true)
      and team_id = target_team
      and expires_at > now()
  )
$$;

-- (a) owner 加人：申請者本人必須已是該團隊的 owner
create policy "team_members: owner can add members"
  on public.team_members for insert
  with check ( is_team_owner(team_members.team_id) );

-- (b) bootstrap：建團隊的人可以把「自己」加成第一個 owner
--     解雞生蛋問題：owner 才能加人，但團隊剛成立時一個人都沒有，誰來加第一個 owner？
create policy "team_members: team creator bootstraps owner"
  on public.team_members for insert
  with check (
    user_id = auth.uid() and role = 'owner'
    and exists (select 1 from teams t
                where t.id = team_members.team_id and t.owner_id = auth.uid())
  );

-- (c) 邀請碼自助加入（規則 5：邀請碼要在資料庫層驗證）
create policy "team_members: join with valid invite"
  on public.team_members for insert
  with check (
    user_id = auth.uid() and role = 'member'
    and invite_is_valid(team_members.team_id)
  );

-- join_team 沒有 security definer：以呼叫者身份執行，insert 一樣要過 with check。
-- 就算有人繞過整個 Next.js 直接 insert，政策這關還是擋得住。
create or replace function join_team(invite_code text, target_team uuid)
returns void language plpgsql
as $$
begin
  perform set_config('request.invite_code', invite_code, true);  -- true = 僅本交易生效
  insert into team_members (team_id, user_id) values (target_team, auth.uid());
end;
$$;
