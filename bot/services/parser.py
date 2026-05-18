"""Claude-powered parser. Takes free-form input and returns structured log entries.

Replaces the fragile `<number> <name>` regex in the original bot.
Handles meals, sets, cardio, and weight in one parser.
"""
import json
import anthropic

from bot.config import ANTHROPIC_API_KEY, CLAUDE_PARSER_MODEL

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


PARSER_SYSTEM = """You parse short fitness log messages into structured JSON.

Return EXACTLY ONE JSON object, no prose, no markdown fences. Schema:

{
  "type": "meal" | "set" | "cardio" | "weight" | "unknown",
  "confidence": 0.0-1.0,
  "data": { ... },
  "needs_confirm": true|false   // true if you estimated values
}

For "meal":
  data = { "name": str, "kcal": number, "protein_g": number, "carbs_g": number, "fat_g": number }
  If user didn't specify kcal/macros, estimate from typical values and set needs_confirm=true.
  Examples:
    "had 2 eggs and oats"     -> kcal ~280, protein ~14, carbs ~30, fat ~12, needs_confirm=true
    "150 protein shake"       -> kcal=150, name="Protein Shake", needs_confirm=false
    "boiled chicken 165 kcal" -> kcal=165, name="Boiled Chicken", needs_confirm=false

For "set" (lifting):
  data = { "exercise": str, "weight_kg": number, "reps": int, "sets": int (default 1), "rpe": number|null }
  Examples:
    "bench 80x5"        -> exercise="Bench Press", weight_kg=80, reps=5, sets=1
    "squat 100kg 5x5"   -> exercise="Squat", weight_kg=100, reps=5, sets=5
    "ohp 40 x 8 rpe 8"  -> exercise="Overhead Press", weight_kg=40, reps=8, sets=1, rpe=8

For "cardio":
  data = { "type": str, "duration_min": number|null, "distance_km": number|null, "notes": str|null }
  Examples:
    "ran 5k in 28min"     -> type="run", distance_km=5, duration_min=28
    "30min walk"          -> type="walk", duration_min=30
    "cycled 20k"          -> type="bike", distance_km=20

For "weight":
  data = { "weight_kg": number }
  Examples:
    "weighed 62.1"          -> weight_kg=62.1
    "weight check in 63kg"  -> weight_kg=63
    "wi 61.8"               -> weight_kg=61.8

For "unknown":
  data = { "reason": "why you couldn't parse" }
  Use when input is unclear or off-topic.

Always use lowercase for cardio type. Always title-case for exercise and meal names.
Weight is always in kg. Distance in km. Duration in minutes.
"""


def parse(text: str) -> dict:
    """Parse a single message into a structured log dict."""
    msg = _client.messages.create(
        model      = CLAUDE_PARSER_MODEL,
        max_tokens = 400,
        system     = PARSER_SYSTEM,
        messages   = [{"role": "user", "content": text}],
    )
    raw = msg.content[0].text.strip()
    # Strip accidental code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "unknown", "confidence": 0.0,
                "data": {"reason": "parser returned invalid JSON"},
                "needs_confirm": False, "raw": raw}


def parse_photo(image_b64: str, media_type: str = "image/jpeg") -> dict:
    """Parse a meal photo. Returns same schema as parse() with type='meal'."""
    msg = _client.messages.create(
        model      = CLAUDE_PARSER_MODEL,
        max_tokens = 500,
        system     = PARSER_SYSTEM + "\n\nThe user sent a photo of a meal. Identify the food and estimate macros. Always set needs_confirm=true for photo logs.",
        messages   = [{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": image_b64,
                }},
                {"type": "text", "text": "Log this meal."},
            ],
        }],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "unknown", "confidence": 0.0,
                "data": {"reason": "vision parser returned invalid JSON"},
                "needs_confirm": False, "raw": raw}
