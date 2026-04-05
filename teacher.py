"""
AI Ustaz moduli - Nemis tili oqıtıwshısı
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME
from logger import get_logger, log_error
from prompts import get_teacher_prompt

logger = get_logger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)


async def teacher_mode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI Ustaz rejimin iske túsiriw"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    try:
        context.user_data["mode"] = "teacher"
        
        await update.message.reply_text(
            "👨‍🏫 **AI Ustaz rejimi**\n\n"
            "🇩🇪 Nemis tili boyınsha sorawlarıńızǵa juwap beremen.\n\n"
            "✏️ **Sorawıńızdı jazıń:**",
            parse_mode="Markdown"
        )
        
        logger.info(f"Teacher mode: {user_id} ({username})")
        
    except Exception as e:
        log_error(logger, e, user_id, "Teacher mode start")
        await update.message.reply_text("❌ Qátelik júz berdi.")


async def teacher_respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paydalanıwshınıń sorawına juwap beriw"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    question = (update.message.text or "").strip()
    
    try:
        loading_msg = await update.message.reply_text(
            "👨‍🏫 **Ustaz juwap berip atır...**\n\n"
            "⏳ Iltitmas, kútiń...",
            parse_mode="Markdown"
        )
        
        prompt = get_teacher_prompt(question)
        
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt)),
            timeout=35
        )
        
        await loading_msg.delete()
        # Markdown parse_mode ni olib tashladik (xatolik ketadi)
        await update.message.reply_text(response.text)
        
        logger.info(f"Teacher responded: {user_id} ({username})")
        context.user_data["mode"] = None
        
    except asyncio.TimeoutError:
        await loading_msg.delete()
        await update.message.reply_text(
            "⏰ Soraw juwaplawda kóp waqıt ketti.\n\n"
            "Sorawıńızdı qısqartırıp qayta jazıń."
        )
    except Exception as e:
        log_error(logger, e, user_id, "Teacher respond")
        await loading_msg.delete()
        await update.message.reply_text(
            "❌ Qátelik júz berdi.\n\n"
            "Qayta urınıp kóriń."
        )
        context.user_data["mode"] = None


__all__ = ['teacher_mode_start', 'teacher_respond']