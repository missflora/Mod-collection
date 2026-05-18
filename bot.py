import base64
import os
import sqlite3
from datetime import date

import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

BOT_TOKEN       = os.environ["BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DAILY_GOAL      = 1400

_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PRESETS = [
    {"name": "Protein Shake",       "cal": 150, "protein": 25, "carbs": 8,  "fat": 3},
    {"name": "Meal Replace. Shake", "cal": 200, "protein": 20, "carbs": 24, "fat": 5},
    {"name": "Steamed Egg",         "cal": 80,  "protein": 8,  "carbs": 1,  "fat": 5},
    {"name": "Congee (plain)",      "cal": 120, "protein": 3,  "carbs": 25, "fat": 1},
    {"name": "Steamed Fish",        "cal": 150, "protein": 28, "carbs": 0,  "fat": 4},
    {"name": "Stir-fry Veg",        "cal": 90,  "protein": 3,  "carbs": 10, "fat": 4},
    {"name": "Tofu Soup",           "cal": 100, "protein": 10, "carbs": 4,  "fat": 5},
    {"name": "Brown Rice (½ cup)",  "cal": 110, "protein": 3,  "carbs": 23, "fat": 1},
    {"name": "Boiled Chicken",      "cal": 165, "protein": 31, "carbs": 0,  "fat": 4},
    {"name": "Wonton Soup",         "cal": 180, "protein": 12, "carbs": 20, "fat": 5},
    {"name": "Green Tea",           "cal": 0,   "protein": 0,  "carbs": 0,  "fat": 0},
    {"name": "Fruit Fibre Shake",   "cal": 285, "protein": 5,  "carbs": 55, "fat": 4},
    {"name": "Scallion Pancake",    "cal": 270, "protein": 5,  "carbs": 35, "fat": 12},
]


# ── database ────────────────────────────────────────────────────────────────

def db():
    conn = sqlite3.connect("calories.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day     TEXT    NOT NULL,
            name    TEXT    NOT NULL,
            cal     REAL    NOT NULL,
            protein REAL    DEFAULT 0,
            carbs   REAL    DEFAULT 0,
            fat     REAL    DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def today_str():
    return date.today().isoformat()


def get_today(user_id: int):
    with db() as conn:
        return conn.execute(
            "SELECT id, name, cal, protein, carbs, fat FROM entries WHERE user_id=? AND day=?",
            (user_id, today_str()),
        ).fetchall()


def insert_entry(user_id: int, name: str, cal: float,
                 protein: float, carbs: float, fat: float):
    with db() as conn:
        conn.execute(
            "INSERT INTO entries (user_id, day, name, cal, protein, carbs, fat) VALUES (?,?,?,?,?,?,?)",
            (user_id, today_str(), name, cal, protein, carbs, fat),
        )


def delete_entry(entry_id: int, user_id: int):
    with db() as conn:
        conn.execute("DELETE FROM entries WHERE id=? AND user_id=?", (entry_id, user_id))


def reset_today(user_id: int):
    with db() as conn:
        conn.execute("DELETE FROM entries WHERE user_id=? AND day=?", (user_id, today_str()))


# ── formatting ───────────────────────────────────────────────────────────────

def summary_text(user_id: int) -> str:
    rows = get_today(user_id)
    total_cal = sum(r[2] for r in rows)
    total_p   = sum(r[3] for r in rows)
    total_c   = sum(r[4] for r in rows)
    total_f   = sum(r[5] for r in rows)
    remaining = DAILY_GOAL - total_cal
    bar_filled = int((total_cal / DAILY_GOAL) * 10)
    bar = "🟩" * min(bar_filled, 10) + "⬜" * max(10 - bar_filled, 0)

    status = f"🔴 {abs(remaining):.0f} kcal over goal!" if total_cal > DAILY_GOAL \
             else f"✅ {remaining:.0f} kcal remaining"

    lines = [
        f"📊 *Today — {today_str()}*",
        f"{bar}",
        f"*{total_cal:.0f}* / {DAILY_GOAL} kcal  |  {status}",
        f"Protein: {total_p:.0f}g  Carbs: {total_c:.0f}g  Fat: {total_f:.0f}g",
    ]

    if rows:
        lines.append("\n*Log:*")
        for row in rows:
            lines.append(f"  • {row[1]} — {row[2]:.0f} kcal  `[/del{row[0]}]`")

    return "\n".join(lines)


# ── handlers ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your personal calorie tracker.\n\n"
        "Goal: *64 kg → 58 kg* | Daily target: *1,400 kcal*\n\n"
        "Commands:\n"
        "/today — see today's summary\n"
        "/add <food> <kcal> — log a meal\n"
        "/quick — quick-add from presets\n"
        "/reset — clear today's log\n"
        "/help — show this message\n\n"
        "Or just send: `150 protein shake`\n"
        "📸 Send a photo — I'll estimate the calories automatically",
        parse_mode="Markdown",
    )


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        summary_text(update.effective_user.id),
        parse_mode="Markdown",
    )


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _parse_and_add(update, " ".join(ctx.args))


async def cmd_quick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} · {p['cal']} kcal", callback_data=str(i))]
        for i, p in enumerate(PRESETS)
    ]
    await update.message.reply_text(
        "Tap to add:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reset_today(update.effective_user.id)
    await update.message.reply_text("✅ Today's log cleared.")


async def cmd_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        entry_id = int(text.replace("/del", ""))
    except ValueError:
        await update.message.reply_text("Usage: /del<id>  e.g. /del42")
        return
    delete_entry(entry_id, update.effective_user.id)
    await update.message.reply_text(
        summary_text(update.effective_user.id), parse_mode="Markdown"
    )


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    preset = PRESETS[int(query.data)]
    insert_entry(
        query.from_user.id,
        preset["name"], preset["cal"],
        preset["protein"], preset["carbs"], preset["fat"],
    )
    await query.edit_message_text(
        f"✅ Added *{preset['name']}* ({preset['cal']} kcal)\n\n"
        + summary_text(query.from_user.id),
        parse_mode="Markdown",
    )


_PHOTO_PROMPT = (
    "You are a nutrition expert. Analyze this food photo and estimate the calories and macros. "
    "Reply ONLY in this exact format with no other text:\n"
    "Food: <name>\n"
    "Calories: <number>\n"
    "Protein: <number>g\n"
    "Carbs: <number>g\n"
    "Fat: <number>g\n"
    "Note: <one sentence confidence note>"
)


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Analysing your photo…")

    photo_file = await (await ctx.bot.get_file(update.message.photo[-1].file_id)).download_as_bytearray()
    image_b64 = base64.standard_b64encode(bytes(photo_file)).decode()

    try:
        response = _anthropic.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                    {"type": "text", "text": _PHOTO_PROMPT},
                ],
            }],
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Vision API error: {e}")
        return

    raw = response.content[0].text.strip()
    parsed = {k.strip(): v.strip() for line in raw.splitlines() if ":" in line
              for k, v in [line.split(":", 1)]}

    try:
        food_name = parsed["Food"]
        cal     = float(parsed["Calories"])
        protein = float(parsed["Protein"].replace("g", ""))
        carbs   = float(parsed["Carbs"].replace("g", ""))
        fat     = float(parsed["Fat"].replace("g", ""))
        note    = parsed.get("Note", "")
    except (KeyError, ValueError):
        await update.message.reply_text(
            "⚠️ Couldn't read the nutrition data from the photo. Try a clearer image."
        )
        return

    insert_entry(update.effective_user.id, food_name, cal, protein, carbs, fat)
    await update.message.reply_text(
        f"📸 *{food_name}* — {cal:.0f} kcal\n"
        f"Protein: {protein:.0f}g  Carbs: {carbs:.0f}g  Fat: {fat:.0f}g\n"
        f"_{note}_\n\n"
        + summary_text(update.effective_user.id),
        parse_mode="Markdown",
    )


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _parse_and_add(update, update.message.text.strip())


async def _parse_and_add(update: Update, text: str):
    """Parse '<number> <name>' or '<name> <number>' then log it."""
    if not text:
        await update.message.reply_text(
            "Send something like: `150 congee` or `/add boiled chicken 165`",
            parse_mode="Markdown",
        )
        return

    parts = text.split()
    cal = None
    name_parts = []
    for part in parts:
        try:
            cal = float(part)
        except ValueError:
            name_parts.append(part)

    if cal is None or not name_parts:
        await update.message.reply_text(
            "⚠️ Include a calorie number, e.g. `tofu soup 100`",
            parse_mode="Markdown",
        )
        return

    name = " ".join(name_parts).title()
    insert_entry(update.effective_user.id, name, cal, 0, 0, 0)
    await update.message.reply_text(
        f"✅ Added *{name}* ({cal:.0f} kcal)\n\n" + summary_text(update.effective_user.id),
        parse_mode="Markdown",
    )


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_start))
    app.add_handler(CommandHandler("today",  cmd_today))
    app.add_handler(CommandHandler("add",    cmd_add))
    app.add_handler(CommandHandler("quick",  cmd_quick))
    app.add_handler(CommandHandler("reset",  cmd_reset))
    app.add_handler(MessageHandler(filters.Regex(r"^/del\d+$"), cmd_del))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
