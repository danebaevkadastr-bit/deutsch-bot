"""
Asosiy fayl - WEBHOOK bilan ishga tushirish
"""

import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from config import BOT_TOKEN
from schreiben import register_schreiben_handlers
from logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Qátelik júz berdi. Iltimas, /start buyrıǵı menen qayta urınıp kóriń."
            )
    except Exception:
        pass


def main():
    try:
        port = int(os.environ.get("PORT", "8000"))
        railway_static_url = os.environ.get("RAILWAY_STATIC_URL")

        if not railway_static_url:
            raise ValueError("RAILWAY_STATIC_URL topilmadi")

        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_error_handler(error_handler)
        register_schreiben_handlers(app)

        webhook_url = f"https://{railway_static_url}/telegram"

        logger.info("Bot started with webhook...")
        print("🚀 Bot webhook menen iske túsdi...")

        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram",
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )

    except Exception as e:
        logger.critical(f"Bot failed: {e}", exc_info=True)
        print(f"❌ Bot ishga tushmadi: {e}")


if __name__ == "__main__":
    main()