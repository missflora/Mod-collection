"""Central config — reads env vars exactly once."""
import os

BOT_TOKEN          = os.environ["BOT_TOKEN"]
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_KEY       = os.environ["SUPABASE_SERVICE_KEY"]  # service role key, server-side only
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")     # optional, for Whisper

# Models
CLAUDE_PARSER_MODEL = "claude-haiku-4-5-20251001"   # cheap+fast for log parsing
CLAUDE_COACH_MODEL  = "claude-sonnet-4-6"           # smart for coaching

# Defaults
DAILY_KCAL_DEFAULT  = 1400
TIMEZONE_DEFAULT    = "Pacific/Auckland"
