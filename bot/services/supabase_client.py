"""Supabase data layer. All DB access goes through here."""
from datetime import date, datetime
from typing import Optional
from supabase import create_client, Client

from bot.config import SUPABASE_URL, SUPABASE_KEY, DAILY_KCAL_DEFAULT, TIMEZONE_DEFAULT

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── users ─────────────────────────────────────────────────────────────
def get_or_create_user(telegram_id: int, name: str = None) -> dict:
    res = _client.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if res.data:
        return res.data[0]
    new = _client.table("users").insert({
        "telegram_id":  telegram_id,
        "name":         name,
        "daily_kcal":   DAILY_KCAL_DEFAULT,
        "timezone":     TIMEZONE_DEFAULT,
    }).execute()
    return new.data[0]


def update_user(user_id: int, fields: dict) -> dict:
    return _client.table("users").update(fields).eq("id", user_id).execute().data[0]


# ── meals ─────────────────────────────────────────────────────────────
def insert_meal(user_id: int, name: str, kcal: float,
                protein_g: float = 0, carbs_g: float = 0, fat_g: float = 0,
                source: str = "text", photo_url: str = None) -> dict:
    return _client.table("meals").insert({
        "user_id":   user_id,
        "name":      name,
        "kcal":      kcal,
        "protein_g": protein_g,
        "carbs_g":   carbs_g,
        "fat_g":     fat_g,
        "source":    source,
        "photo_url": photo_url,
    }).execute().data[0]


def meals_today(user_id: int) -> list[dict]:
    today = date.today().isoformat()
    return _client.table("meals").select("*") \
        .eq("user_id", user_id).eq("day", today) \
        .order("logged_at").execute().data


def delete_meal(meal_id: int, user_id: int) -> None:
    _client.table("meals").delete().eq("id", meal_id).eq("user_id", user_id).execute()


def reset_today_meals(user_id: int) -> None:
    today = date.today().isoformat()
    _client.table("meals").delete().eq("user_id", user_id).eq("day", today).execute()


# ── presets ───────────────────────────────────────────────────────────
def get_presets(user_id: int) -> list[dict]:
    return _client.table("meal_presets").select("*") \
        .eq("user_id", user_id).eq("archived", False) \
        .order("sort_order").execute().data


def get_preset(preset_id: int) -> Optional[dict]:
    res = _client.table("meal_presets").select("*").eq("id", preset_id).execute()
    return res.data[0] if res.data else None


# ── weight ────────────────────────────────────────────────────────────
def log_weight(user_id: int, weight_kg: float, photo_url: str = None) -> dict:
    return _client.table("weight_logs").upsert({
        "user_id":   user_id,
        "day":       date.today().isoformat(),
        "weight_kg": weight_kg,
        "photo_url": photo_url,
    }, on_conflict="user_id,day").execute().data[0]


def recent_weights(user_id: int, days: int = 90) -> list[dict]:
    return _client.table("weight_logs").select("*") \
        .eq("user_id", user_id) \
        .order("day", desc=True).limit(days).execute().data


# ── cardio ────────────────────────────────────────────────────────────
def log_cardio(user_id: int, type_: str, duration_min: float = None,
               distance_km: float = None, notes: str = None) -> dict:
    return _client.table("cardio_logs").insert({
        "user_id":      user_id,
        "type":         type_,
        "duration_min": duration_min,
        "distance_km":  distance_km,
        "notes":        notes,
    }).execute().data[0]


# ── workouts / sets (used in Phase 2) ─────────────────────────────────
def log_set(user_id: int, exercise_name: str, weight_kg: float, reps: int,
            rpe: float = None) -> dict:
    """Quick-log a single set without a structured workout.
    Creates an ad-hoc workout + exercise if none exists for today."""
    today = date.today().isoformat()

    # find or create today's adhoc workout
    res = _client.table("workouts").select("*") \
        .eq("user_id", user_id).eq("day", today).execute()
    if res.data:
        workout = res.data[0]
    else:
        workout = _client.table("workouts").insert({
            "user_id": user_id, "type": "adhoc", "status": "active",
            "started_at": datetime.utcnow().isoformat(),
        }).execute().data[0]

    # find or create exercise within that workout
    res = _client.table("exercises").select("*") \
        .eq("workout_id", workout["id"]).ilike("name", exercise_name).execute()
    if res.data:
        exercise = res.data[0]
    else:
        exercise = _client.table("exercises").insert({
            "workout_id": workout["id"], "name": exercise_name.title(),
        }).execute().data[0]

    # set number
    res = _client.table("sets").select("set_num") \
        .eq("exercise_id", exercise["id"]) \
        .order("set_num", desc=True).limit(1).execute()
    next_set = (res.data[0]["set_num"] + 1) if res.data else 1

    return _client.table("sets").insert({
        "exercise_id": exercise["id"],
        "set_num":     next_set,
        "reps":        reps,
        "weight_kg":   weight_kg,
        "rpe":         rpe,
    }).execute().data[0]


# ── chat history (for coach) ──────────────────────────────────────────
def save_chat(user_id: int, role: str, content: str) -> None:
    _client.table("chat_history").insert({
        "user_id": user_id, "role": role, "content": content,
    }).execute()


def recent_chat(user_id: int, limit: int = 20) -> list[dict]:
    res = _client.table("chat_history").select("role, content") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True).limit(limit).execute()
    return list(reversed(res.data))
