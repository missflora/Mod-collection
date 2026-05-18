"""Slash command handlers."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.services import supabase_client as db
from bot.services.formatters import today_summary


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(
        telegram_id = update.effective_user.id,
        name        = update.effective_user.first_name,
    )
    await update.message.reply_text(
        f"👋 Hi {user.get('name') or 'there'}! I'm your fitness coach.\n\n"
        f"Daily target: *{user['daily_kcal']} kcal*\n\n"
        "*What I do:*\n"
        "• Log meals — type, speak, or photo\n"
        "• Log lifts — `bench 80x5`\n"
        "• Log cardio — `ran 5k in 28min`\n"
        "• Log weight — `wi 62.1`\n\n"
        "*Commands:*\n"
        "/today — summary\n"
        "/quick — preset meals\n"
        "/weight — log weight\n"
        "/coach — chat with AI coach\n"
        "/reset — clear today",
        parse_mode="Markdown",
    )


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(update.effective_user.id)
    await update.message.reply_text(today_summary(user), parse_mode="Markdown")


async def cmd_quick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(update.effective_user.id)
    presets = db.get_presets(user["id"])
    if not presets:
        await update.message.reply_text(
            "No presets yet. Add some in Supabase or just log freely!"
        )
        return
    keyboard = [
        [InlineKeyboardButton(
            f"{p.get('emoji','')} {p['name']} · {float(p['kcal']):.0f} kcal",
            callback_data=f"preset:{p['id']}"
        )]
        for p in presets
    ]
    await update.message.reply_text(
        "Tap to add:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(update.effective_user.id)
    db.reset_today_meals(user["id"])
    await update.message.reply_text("✅ Today's log cleared.")


async def cmd_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(update.effective_user.id)
    text = update.message.text.strip()
    try:
        meal_id = int(text.replace("/del", ""))
    except ValueError:
        await update.message.reply_text("Usage: /del<id> e.g. /del42")
        return
    db.delete_meal(meal_id, user["id"])
    await update.message.reply_text(today_summary(user), parse_mode="Markdown")


async def cmd_weight(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(update.effective_user.id)
    if not ctx.args:
        await update.message.reply_text("Usage: /weight 62.1")
        return
    try:
        w = float(ctx.args[0])
    except ValueError:
        await update.message.reply_text("Send a number like /weight 62.1")
        return
    db.log_weight(user["id"], w)
    await update.message.reply_text(f"⚖️ Logged: *{w}kg*", parse_mode="Markdown")


async def on_preset_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, preset_id = query.data.split(":")
    preset = db.get_preset(int(preset_id))
    user = db.get_or_create_user(query.from_user.id)
    db.insert_meal(
        user_id   = user["id"],
        name      = preset["name"],
        kcal      = float(preset["kcal"]),
        protein_g = float(preset["protein_g"]),
        carbs_g   = float(preset["carbs_g"]),
        fat_g     = float(preset["fat_g"]),
        source    = "preset",
    )
    await query.edit_message_text(
        f"✅ Added *{preset['name']}* ({float(preset['kcal']):.0f} kcal)\n\n"
        + today_summary(user),
        parse_mode="Markdown",
    )
