"""Reusable formatting helpers — summary cards, progress bars, etc."""
from datetime import date

from bot.services import supabase_client as db


def progress_bar(value: float, goal: float, width: int = 10) -> str:
    if goal <= 0:
        return ""
    filled = int((value / goal) * width)
    filled = max(0, min(filled, width))
    return "🟩" * filled + "⬜" * (width - filled)


def today_summary(user: dict) -> str:
    rows = db.meals_today(user["id"])
    total_cal = sum(float(r["kcal"]) for r in rows)
    total_p   = sum(float(r["protein_g"]) for r in rows)
    total_c   = sum(float(r["carbs_g"])   for r in rows)
    total_f   = sum(float(r["fat_g"])     for r in rows)

    goal = user.get("daily_kcal") or 1400
    remaining = goal - total_cal
    bar = progress_bar(total_cal, goal)
    status = (f"🔴 {abs(remaining):.0f} kcal over goal!"
              if total_cal > goal
              else f"✅ {remaining:.0f} kcal remaining")

    lines = [
        f"📊 *Today — {date.today().isoformat()}*",
        bar,
        f"*{total_cal:.0f}* / {goal} kcal | {status}",
        f"P {total_p:.0f}g · C {total_c:.0f}g · F {total_f:.0f}g",
    ]
    if rows:
        lines.append("\n*Log:*")
        for r in rows:
            emoji = "📷" if r["source"] == "photo" else ("🎤" if r["source"] == "voice" else "•")
            lines.append(f" {emoji} {r['name']} — {float(r['kcal']):.0f} kcal `[/del{r['id']}]`")
    return "\n".join(lines)


def confirm_prompt(parsed: dict) -> str:
    """Build a confirmation message for AI-estimated logs."""
    t = parsed["type"]
    d = parsed["data"]
    if t == "meal":
        return (f"📝 *Logged from estimate:*\n"
                f"{d['name']} — {d['kcal']:.0f} kcal\n"
                f"P {d.get('protein_g',0):.0f}g · "
                f"C {d.get('carbs_g',0):.0f}g · "
                f"F {d.get('fat_g',0):.0f}g\n\n"
                f"Reply with the correct number to override "
                f"(e.g. `220` for kcal).")
    if t == "set":
        return f"💪 Logged: *{d['exercise']}* {d['weight_kg']}kg × {d['reps']}"
    if t == "cardio":
        bits = []
        if d.get("distance_km"): bits.append(f"{d['distance_km']}km")
        if d.get("duration_min"): bits.append(f"{d['duration_min']}min")
        return f"🏃 Logged: *{d['type']}* {' '.join(bits)}"
    if t == "weight":
        return f"⚖️ Weight logged: *{d['weight_kg']}kg*"
    return "🤔 Couldn't parse that."
