"""Photo handler — Claude vision identifies meals and estimates macros."""
import base64
import tempfile
import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.services import supabase_client as db
from bot.services import parser
from bot.services.formatters import today_summary, confirm_prompt


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # largest size
    status = await update.message.reply_text("📷 Analysing photo…")

    file = await photo.get_file()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await file.download_to_drive(tmp_path)
        with open(tmp_path, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    parsed = parser.parse_photo(img_b64)

    if parsed["type"] != "meal":
        await status.edit_text(
            "🤔 I couldn't identify a meal in that photo. "
            "Try sending the photo with a caption like `chicken salad`."
        )
        return

    user = db.get_or_create_user(update.effective_user.id)
    d = parsed["data"]
    db.insert_meal(
        user_id   = user["id"],
        name      = d["name"],
        kcal      = float(d["kcal"]),
        protein_g = float(d.get("protein_g", 0)),
        carbs_g   = float(d.get("carbs_g", 0)),
        fat_g     = float(d.get("fat_g", 0)),
        source    = "photo",
    )

    await status.edit_text(
        confirm_prompt(parsed) + "\n\n" + today_summary(user),
        parse_mode="Markdown",
    )
