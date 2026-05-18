"""Main entrypoint. Run with: python -m bot.main"""
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

from bot.config import BOT_TOKEN
from bot.handlers import commands, text, voice, photo


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",  commands.cmd_start))
    app.add_handler(CommandHandler("help",   commands.cmd_start))
    app.add_handler(CommandHandler("today",  commands.cmd_today))
    app.add_handler(CommandHandler("quick",  commands.cmd_quick))
    app.add_handler(CommandHandler("reset",  commands.cmd_reset))
    app.add_handler(CommandHandler("weight", commands.cmd_weight))

    # /del<id> custom regex
    app.add_handler(MessageHandler(filters.Regex(r"^/del\d+$"), commands.cmd_del))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(commands.on_preset_callback, pattern=r"^preset:"))

    # Media handlers
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice.on_voice))
    app.add_handler(MessageHandler(filters.PHOTO, photo.on_photo))

    # Catch-all free text → Claude parser
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text.on_message))

    return app


def main():
    app = build_app()
    print("🤖 Fitness bot running…")
    app.run_polling()


if __name__ == "__main__":
    main()
