from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

async def teacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "👨‍🏫 AI Ustoz\n\n"
            "Mavzuni shu formatda yozing:\n"
            "/teacher Perfekt\n"
            "/teacher Artikel\n"
            "/teacher B1 Schreiben"
        )
        return

    topic = " ".join(context.args)

    prompt = f"""
Sen nemis tili ustozisan.

Foydalanuvchi mavzusi:
{topic}

Quyidagicha javob ber:
1. Mavzuni oddiy o‘zbek tilida tushuntir
2. Muhim qoidalarni ayt
3. 3 ta nemischa misol ber
4. Eng ko‘p qilinadigan xatoni ayt
5. Oxirida kichik mashq ber
"""

    response = model.generate_content(prompt)
    await update.message.reply_text(response.text)

def register_teacher_handlers(app):
    app.add_handler(CommandHandler("teacher", teacher_command))