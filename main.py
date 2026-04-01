"""
Asosiy fayl - Botni ishga tushirish
"""

from telegram.ext import ApplicationBuilder
from telegram import Update
from telegram.ext import ContextTypes

from config import BOT_TOKEN
from schreiben import register_schreiben_handlers
from logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Xatolik yuz berdi. Iltimos, /start buyrug'i bilan qayta urinib ko'ring."
            )
    except:
        pass


def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_error_handler(error_handler)
        register_schreiben_handlers(app)
        
        logger.info("Bot started...")
        print("🤖 Bot ishga tushdi...")
        
        app.run_polling()
        
    except Exception as e:
        logger.critical(f"Bot failed: {e}", exc_info=True)
        print(f"❌ Bot ishga tushmadi: {e}")


if __name__ == "__main__":
    main()