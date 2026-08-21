-- 001_schema.sql
-- 規則 4：每張新表建立時，同一個 migration 內就要 enable row level security。
-- 此刻五張表全部 RLS Enabled 且「零政策 = 全擋」——所有房門都裝了鎖，但還沒發任何鑰匙。

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url text
);
alter table profiles enable row level security;   -- 規則 4：建表與開 RLS 在同一個 migration

create table teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid not null references profiles(id),
  created_at timestamptz not null default now()
);
alter table teams enable row level security;

create table team_members (
  team_id uuid not null references teams(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  role text not null default 'member' check (role in ('owner','member')),
  primary key (team_id, user_id)
);
alter table team_members enable row level security;

create table tasks (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null references teams(id) on delete cascade,
  title text not null,
  status text not null default 'todo' check (status in ('todo','in_progress','done')),
  assignee_id uuid references profiles(id),
  created_by uuid references profiles(id),
  created_at timestamptz not null default now()
);
alter table tasks enable row level security;

create table invites (
  code text primary key,
  team_id uuid not null references teams(id) on delete cascade,
  expires_at timestamptz not null
);
alter table invites enable row level security;

-- 註冊自動建 profile（沒有這個 trigger，登入後 profiles 會是空的——常見坑）
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public
as $$
begin
  insert into profiles (id, display_name) values (new.id, new.email);
  return new;
end;
$$;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
