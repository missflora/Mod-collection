"""Smart text handler — Claude parses any free-form message into a log entry."""
from telegram import Update
from telegram.ext import ContextTypes

from bot.services import supabase_client as db
from bot.services import parser
from bot.services.formatters import today_summary, confirm_prompt


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await handle_text(update, update.message.text.strip())


async def handle_text(update: Update, text: str):
    """Shared logic — used by text + voice handlers."""
    user = db.get_or_create_user(update.effective_user.id)
    parsed = parser.parse(text)

    t = parsed["type"]
    d = parsed.get("data", {})

    if t == "meal":
        db.insert_meal(
            user_id   = user["id"],
            name      = d["name"],
            kcal      = float(d["kcal"]),
            protein_g = float(d.get("protein_g", 0)),
            carbs_g   = float(d.get("carbs_g", 0)),
            fat_g     = float(d.get("fat_g", 0)),
            source    = "voice" if "voice" in (update.message.voice and "voice" or "") else "text",
        )
        await update.message.reply_text(
            confirm_prompt(parsed) + "\n\n" + today_summary(user),
            parse_mode="Markdown",
        )

    elif t == "set":
        db.log_set(
            user_id       = user["id"],
            exercise_name = d["exercise"],
            weight_kg     = float(d["weight_kg"]),
            reps          = int(d["reps"]),
            rpe           = d.get("rpe"),
        )
        sets = int(d.get("sets", 1))
        # if user said "5x5", log the remaining sets too
        for _ in range(sets - 1):
            db.log_set(user["id"], d["exercise"],
                       float(d["weight_kg"]), int(d["reps"]), d.get("rpe"))
        msg = confirm_prompt(parsed)
        if sets > 1:
            msg += f" × {sets} sets"
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif t == "cardio":
        db.log_cardio(
            user_id      = user["id"],
            type_        = d["type"],
            duration_min = d.get("duration_min"),
            distance_km  = d.get("distance_km"),
            notes        = d.get("notes"),
        )
        await update.message.reply_text(confirm_prompt(parsed), parse_mode="Markdown")

    elif t == "weight":
        db.log_weight(user["id"], float(d["weight_kg"]))
        await update.message.reply_text(confirm_prompt(parsed), parse_mode="Markdown")

    else:
        await update.message.reply_text(
            "🤔 I couldn't make sense of that. Try:\n"
            "• `150 protein shake` (meal)\n"
            "• `bench 80x5` (lift)\n"
            "• `ran 5k in 28min` (cardio)\n"
            "• `wi 62.1` (weight)"
        )
