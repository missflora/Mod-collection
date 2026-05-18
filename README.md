# Fitness Bot — Phase 0 + Phase 1

All-in-one Telegram trainer: nutrition, lifting, cardio, weight tracking.
Smart parsing via Claude. Voice notes via Whisper. Photos via Claude vision.

## What this replaces

The original `bot.py` was a SQLite calorie tracker with regex parsing.
This is a refactor that:

- Migrates to **Supabase Postgres** (no more data loss on Railway redeploys)
- Adds **Claude Haiku parsing** — handles any free-form input
- Adds **voice logging** (Whisper)
- Adds **photo logging** (Claude vision)
- Extends data model to **workouts, sets, cardio, weight**
- Moves presets from hardcoded list → DB table (editable without redeploy)
- Restructures into proper modules for future growth

## Setup

### 1. Create Supabase project
- Go to supabase.com, new project (free tier)
- SQL Editor → paste `db/schema.sql` → run
- Settings → API → copy *Project URL* and *service_role* key

### 2. Get API keys
- **Anthropic**: console.anthropic.com → API keys
- **OpenAI** (for voice): platform.openai.com → API keys (optional)

### 3. Set env vars in Railway
```
BOT_TOKEN=...                  # from @BotFather
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...    # service role, NOT anon
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # optional
```

### 4. Seed your presets
After `/start` (which creates your user row):
```sql
-- Find your user id
SELECT id FROM users WHERE telegram_id = <your_telegram_id>;

-- Then run db/seed_presets.sql replacing :user_id with that number
```

### 5. Deploy
Push to GitHub. Railway auto-deploys.

## Usage

```
/start    — initialize
/today    — summary card
/quick    — preset meals
/weight 62.1
/reset    — clear today
/del42    — delete entry

Free text:
  "150 congee"              → meal
  "had 2 eggs and oats"     → meal (AI estimates macros)
  "bench 80x5x3"            → lift (3 sets logged)
  "ran 5k in 28min"         → cardio
  "wi 62.1"                 → weight

Voice notes → transcribed and parsed
Photos     → identified and logged with estimated macros
```

## Project structure

```
bot/
  main.py                  # entrypoint
  config.py                # env vars
  handlers/
    commands.py            # /start /today /quick /reset /del /weight
    text.py                # free-form text → parser → log
    voice.py               # voice → Whisper → text handler
    photo.py               # photo → Claude vision → meal log
  services/
    supabase_client.py     # all DB operations
    parser.py              # Claude Haiku parser (the brain)
    voice.py               # Whisper wrapper
    formatters.py          # summary cards, progress bars

db/
  schema.sql               # full schema (run once)
  seed_presets.sql         # your Cantonese-style presets

Procfile
railway.toml
requirements.txt
```

## What's next (Phase 2+)

- `/workout` command + structured programs
- Set-by-set logging with inline keyboard + rest timer
- Mini App (React) for dashboard with charts
- `/coach` command with full-context Claude conversation
- GitHub Actions for daily/weekly cron jobs
