-- =====================================================================
-- Fitness Bot — Supabase schema
-- Run this in the Supabase SQL Editor (one-shot setup).
-- =====================================================================

-- USERS ---------------------------------------------------------------
create table if not exists users (
  id              bigserial primary key,
  telegram_id     bigint unique not null,
  name            text,
  goal_weight_kg  numeric(5,2),
  daily_kcal      int default 1400,
  protein_g       int default 110,    -- ~1.8g/kg lean
  carbs_g         int default 140,
  fat_g           int default 45,
  timezone        text default 'Pacific/Auckland',
  settings        jsonb default '{}'::jsonb,
  created_at      timestamptz default now()
);

-- MEAL PRESETS (per-user, replaces hardcoded PRESETS list) -------------
create table if not exists meal_presets (
  id          bigserial primary key,
  user_id     bigint references users(id) on delete cascade,
  name        text not null,
  kcal        numeric(6,1) not null,
  protein_g   numeric(5,1) default 0,
  carbs_g     numeric(5,1) default 0,
  fat_g       numeric(5,1) default 0,
  emoji       text,
  sort_order  int default 0,
  archived    boolean default false
);

-- MEAL LOGS -----------------------------------------------------------
create table if not exists meals (
  id            bigserial primary key,
  user_id       bigint references users(id) on delete cascade,
  logged_at     timestamptz default now(),
  day           date not null default current_date,
  name          text not null,
  kcal          numeric(6,1) not null,
  protein_g     numeric(5,1) default 0,
  carbs_g       numeric(5,1) default 0,
  fat_g         numeric(5,1) default 0,
  source        text default 'text',     -- text | voice | photo | preset | ai
  photo_url     text,
  notes         text
);
create index if not exists meals_user_day_idx on meals(user_id, day);

-- WEIGHT LOGS ---------------------------------------------------------
create table if not exists weight_logs (
  id          bigserial primary key,
  user_id     bigint references users(id) on delete cascade,
  day         date not null default current_date,
  weight_kg   numeric(5,2) not null,
  photo_url   text,
  notes       text,
  created_at  timestamptz default now(),
  unique (user_id, day)
);

-- WORKOUTS, EXERCISES, SETS -------------------------------------------
create table if not exists workouts (
  id          bigserial primary key,
  user_id     bigint references users(id) on delete cascade,
  day         date not null default current_date,
  type        text,                          -- push / pull / legs / full / cardio
  status      text default 'planned',        -- planned | active | done | skipped
  started_at  timestamptz,
  finished_at timestamptz,
  notes       text
);
create index if not exists workouts_user_day_idx on workouts(user_id, day);

create table if not exists exercises (
  id              bigserial primary key,
  workout_id      bigint references workouts(id) on delete cascade,
  name            text not null,
  ord             int default 0,
  target_sets     int,
  target_reps     text,                       -- "8-12" or "5"
  target_weight   numeric(6,2),
  video_url       text,
  notes           text
);

create table if not exists sets (
  id            bigserial primary key,
  exercise_id   bigint references exercises(id) on delete cascade,
  set_num       int not null,
  reps          int,
  weight_kg     numeric(6,2),
  rpe           numeric(3,1),
  completed_at  timestamptz default now()
);

-- CARDIO LOGS ---------------------------------------------------------
create table if not exists cardio_logs (
  id            bigserial primary key,
  user_id       bigint references users(id) on delete cascade,
  day           date not null default current_date,
  type          text,                         -- run / walk / bike / swim / row
  duration_min numeric(5,1),
  distance_km  numeric(5,2),
  avg_hr       int,
  notes         text,
  created_at    timestamptz default now()
);

-- COACH CHAT HISTORY --------------------------------------------------
create table if not exists chat_history (
  id          bigserial primary key,
  user_id     bigint references users(id) on delete cascade,
  role        text not null,                  -- user | assistant
  content     text not null,
  created_at  timestamptz default now()
);
create index if not exists chat_history_user_idx on chat_history(user_id, created_at desc);

-- DAILY TOTALS VIEW (handy for dashboards) ----------------------------
create or replace view daily_totals as
select
  user_id,
  day,
  sum(kcal)       as kcal,
  sum(protein_g)  as protein_g,
  sum(carbs_g)    as carbs_g,
  sum(fat_g)      as fat_g,
  count(*)        as items
from meals
group by user_id, day;

-- PRs VIEW (best set per exercise name per user) ----------------------
create or replace view prs as
select
  w.user_id,
  e.name as exercise,
  max(s.weight_kg) as max_weight_kg
from sets s
join exercises e on e.id = s.exercise_id
join workouts w on w.id = e.workout_id
where s.weight_kg is not null
group by w.user_id, e.name;
