"""Voice note handler — Whisper transcribes, then routes to text parser."""
import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from bot.services import voice as voice_svc
from bot.handlers.text import handle_text


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    if not voice:
        return

    # Tell the user we're listening
    status = await update.message.reply_text("🎤 Listening…")

    # Download .ogg
    file = await voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await file.download_to_drive(tmp_path)
        text = voice_svc.transcribe(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    await status.edit_text(f"📝 _{text}_", parse_mode="Markdown")
    await handle_text(update, text)
