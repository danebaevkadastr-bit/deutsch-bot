from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from schreiben import register_schreiben_handlers
from teacher import register_teacher_handlers

app = ApplicationBuilder().token(BOT_TOKEN).build()

register_schreiben_handlers(app)
register_teacher_handlers(app)

print("Bot ishga tushdi...")
app.run_polling()git push --set-upstream origin main