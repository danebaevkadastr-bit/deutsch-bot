from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, ContextTypes, filters
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

async def teacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "teacher"
    await update.message.reply_text(
        "👨‍🏫 AI Ustoz rejimi yoqildi.\n\n"
        "Mavzuni yozing:\n"
        "- Perfekt\n"
        "- Artikel\n"
        "- B1 Schreiben\n\n"
        "Chiqish uchun: /start"
    )

async def teacher_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") != "teacher":
        return

    text = update.message.text

    if text == "👨‍🏫 AI Ustoz":
        await teacher_command(update, context)
        return

    prompt = f"""
Sen nemis tili ustozisan.

Foydalanuvchi mavzusi:
{text}

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
    app.add_handler(MessageHandler(filters.Regex("^👨‍🏫 AI Ustoz$"), teacher_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_text))