"""
Schreiben moduli - B1 imtihon Aufgabe-larini tekshirish
"""

import asyncio
import os
import time
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME
from tasks import TASKS
from logger import get_logger, log_error
from teacher import teacher_mode_start, teacher_respond
from database import (
    get_or_create_user,
    update_user_request,
    log_task_check,
    log_teacher_request,
    get_user_statistics,
    get_admin_stats_text,
    get_all_users,
)
from prompts import get_schreiben_prompt, get_schreiben_photo_prompt
from phrases import show_useful_phrases, phrases_callback_handler

logger = get_logger(__name__)

# Gemini konfiguratsiyasi
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Admin ID (o'z ID ingizni qo'ying!)
ADMIN_IDS = [123456789]  # 👈 O'ZGARTIRING!

# Asosiy menyu
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📚 Aufgabe tanlash"), KeyboardButton("👨‍🏫 AI Ustoz")],
        [KeyboardButton("💬 Foydali iboralar")],
    ],
    resize_keyboard=True,
)


# ============================================
# START KOMANDASI
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    try:
        get_or_create_user(user_id, username, first_name, last_name)
        update_user_request(user_id)
        context.user_data.clear()
        context.user_data["mode"] = None

        await update.message.reply_text(
            "🇩🇪 **Hallo! Willkommen!** 🇩🇪\n\n"
            "Men nemis tilini o'rganuvchilar uchun yordamchi botman.\n\n"
            "📝 **Nima qila olaman?**\n"
            "• B1 Schreiben Aufgabe-larini tekshirish\n"
            "• AI Ustoz sifatida nemis tili savollariga javob berish\n"
            "• Foydali nemis iboralari\n\n"
            "Kerakli bo'limni tanlang 👇",
            reply_markup=main_menu,
            parse_mode="Markdown",
        )
    except Exception as e:
        log_error(logger, e, user_id, "Start")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


# ============================================
# AUFGABE TUGMALARI
# ============================================
def build_buttons(current_page=0, tasks_per_page=10):
    """Aufgabe tugmalarini yaratish"""
    keyboard = []
    total_tasks = len(TASKS)
    total_pages = (total_tasks + tasks_per_page - 1) // tasks_per_page

    start_idx = current_page * tasks_per_page
    end_idx = min(start_idx + tasks_per_page, total_tasks)

    row = []
    for i in range(start_idx + 1, end_idx + 1):
        row.append(InlineKeyboardButton(f"Aufgabe {i}", callback_data=f"task_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Navigatsiya tugmalari
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton("◀️ Oldingi", callback_data=f"page_{current_page - 1}")
        )
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Keyingi ▶️", callback_data=f"page_{current_page + 1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(keyboard)


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aufgabe-larni ko'rsatish"""
    user_id = update.effective_user.id

    try:
        context.user_data["current_page"] = 0

        await update.message.reply_text(
            "📚 **Aufgabe tanlang** (1-20)\n\nQuyidagi tugmalardan birini bosing:",
            reply_markup=build_buttons(0),
            parse_mode="Markdown",
        )
        logger.info(f"Tasks shown to user {user_id}")
    except Exception as e:
        log_error(logger, e, user_id, "Show tasks")
        await update.message.reply_text("❌ Aufgabe-larni yuklashda xatolik yuz berdi.")


async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sahifalashni boshqarish"""
    query = update.callback_query
    user_id = update.effective_user.id

    try:
        await query.answer()

        data = query.data
        if data == "back_to_menu":
            await query.message.delete()
            await query.message.reply_text(
                "🏠 **Asosiy menyu**\n\nKerakli bo'limni tanlang:",
                reply_markup=main_menu,
                parse_mode="Markdown",
            )
            return

        if data.startswith("page_"):
            page = int(data.split("_")[1])
            context.user_data["current_page"] = page

            await query.message.edit_text(
                f"📚 **Aufgabe tanlang** (1-20)\n\nSahifa {page + 1}/{(len(TASKS) + 9) // 10}",
                reply_markup=build_buttons(page),
                parse_mode="Markdown",
            )
    except Exception as e:
        log_error(logger, e, user_id, f"Pagination: {data}")
        await query.message.reply_text("❌ Xatolik yuz berdi.")


async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aufgabe tanlash"""
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username

    try:
        await query.answer()

        task_num = int(query.data.split("_")[1])
        context.user_data["task"] = task_num
        context.user_data["task_name"] = f"Aufgabe {task_num}"
        context.user_data["mode"] = None

        task = TASKS[task_num]

        task_info = (
            f"✅ **{task_num}. Aufgabe**\n\n"
            f"📝 **Vazifa:**\n{task['task']}\n\n"
            f"🎯 **Majburiy punktlar:**\n"
            f"• {task['points'][0]}\n"
            f"• {task['points'][1]}\n"
            f"• {task['points'][2]}\n\n"
            f"📏 **So'zlar soni:** Kamida {task['min_words']} so'z\n"
            f"✍️ **Stil:** {task['style'].upper()}\n\n"
            f"---\n"
            f"✏️ **Endi matn yozing** yoki 📸 **rasm yuboring**.\n"
            f"Men sizning yozganingizni tekshirib, baholayman."
        )

        await query.message.reply_text(task_info, parse_mode="Markdown")
        logger.info(f"Task {task_num} selected by user {user_id} ({username})")

    except Exception as e:
        log_error(logger, e, user_id, f"Choose task: {query.data if query else 'None'}")
        await query.message.reply_text("❌ Aufgabe tanlashda xatolik yuz berdi.")


# ============================================
# MATN VA RASM QAYTA ISHLASH
# ============================================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlarni qayta ishlash"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    text = (update.message.text or "").strip()

    update_user_request(user_id)

    try:
        # --- AI USTOZ REJIMI ---
        if context.user_data.get("mode") == "teacher":
            start_time = time.time()
            await teacher_respond(update, context)
            response_time = int(time.time() - start_time)
            log_teacher_request(user_id, len(text), response_time)
            return

        # --- AUFGABE TANLASH TUGMASI ---
        if "Aufgabe" in text:
            await show_tasks(update, context)
            return

        # --- AI USTOZ TUGMASI ---
        if "Ustoz" in text:
            await teacher_mode_start(update, context)
            return

        # --- FOYDALI IBORALAR TUGMASI ---
        if "Foydali iboralar" in text or "Iboralar" in text:
            await show_useful_phrases(update, context)
            return

        # --- MATN TEKSHIRISH ---
        if "task" not in context.user_data:
            await update.message.reply_text(
                "⚠️ **Avval Aufgabe tanlang!**\n\n"
                "📚 **Aufgabe tanlash** tugmasini bosing yoki\n"
                "👨‍🏫 **AI Ustoz** rejimidan foydalaning.",
                parse_mode="Markdown",
            )
            return

        try:
            task = TASKS[context.user_data["task"]]
            current_task = context.user_data.get("task_name", "Noma'lum Aufgabe")

            loading_msg = await update.message.reply_text(
                f"📌 **Tanlangan:** {current_task}\n\n"
                f"🔍 Matn tekshirilmoqda...\n"
                f"⏳ Iltimos, kuting (10-20 soniya)",
                parse_mode="Markdown",
            )

            prompt = get_schreiben_prompt(task, text)

            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: model.generate_content(prompt)
                ),
                timeout=45,
            )

            await loading_msg.delete()
            await update.message.reply_text(response.text, parse_mode="Markdown")

            log_task_check(user_id, context.user_data["task"], len(text))
            logger.info(
                f"Task {context.user_data['task']} checked for user {user_id} ({username})"
            )

        except asyncio.TimeoutError:
            await loading_msg.delete()
            await update.message.reply_text(
                "⏰ **Tekshirish juda uzoq davom etdi.**\n\n"
                "Iltimos, matnni qisqartirib yoki qayta yuboring.",
                parse_mode="Markdown",
            )
        except Exception as e:
            log_error(logger, e, user_id, f"Task checking")
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ **Matnni tekshirishda xatolik yuz berdi.**\n\n"
                "Iltimos, qayta urinib ko'ring.",
                parse_mode="Markdown",
            )

    except Exception as e:
        log_error(logger, e, user_id, f"Text router")
        await update.message.reply_text(
            "❌ **Kutilmagan xatolik.**\n\nIltimos, /start buyrug'ini bosing.",
            parse_mode="Markdown",
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm yuborilganda - rasmdagi matnni o'qib tekshirish"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    update_user_request(user_id)

    try:
        if context.user_data.get("mode") == "teacher":
            await update.message.reply_text(
                "👨‍🏫 **AI Ustoz rejimidasiz**\n\n"
                "Rasm emas, matn ko'rinishida savolingizni yozing.",
                parse_mode="Markdown",
            )
            return

        if "task" not in context.user_data:
            await update.message.reply_text(
                "⚠️ **Avval Aufgabe tanlang!**\n\n📚 Aufgabe tanlash tugmasini bosing.",
                parse_mode="Markdown",
            )
            return

        try:
            task = TASKS[context.user_data["task"]]
            current_task = context.user_data.get("task_name", "Noma'lum Aufgabe")

            loading_msg = await update.message.reply_text(
                f"📌 **Tanlangan:** {current_task}\n\n"
                f"🖼️ Rasm tekshirilmoqda...\n"
                f"⏳ Iltimos, kuting (20-30 soniya)",
                parse_mode="Markdown",
            )

            photo = update.message.photo[-1]
            file = await photo.get_file()

            filename = f"image_{user_id}_{int(time.time())}.jpg"
            await file.download_to_drive(filename)

            with open(filename, "rb") as f:
                img_data = f.read()

            prompt = get_schreiben_photo_prompt(task)

            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.generate_content(
                        [prompt, {"mime_type": "image/jpeg", "data": img_data}]
                    ),
                ),
                timeout=60,
            )

            if os.path.exists(filename):
                os.remove(filename)

            await loading_msg.delete()
            await update.message.reply_text(response.text, parse_mode="Markdown")

            log_task_check(user_id, context.user_data["task"], 0)
            logger.info(f"Photo checked for user {user_id} ({username})")

        except asyncio.TimeoutError:
            await loading_msg.delete()
            await update.message.reply_text(
                "⏰ **Rasmni tekshirish juda uzoq davom etdi.**\n\n"
                "Iltimos, matnni yozma ravishda yuboring.",
                parse_mode="Markdown",
            )
        except Exception as e:
            log_error(logger, e, user_id, f"Photo checking")
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ **Rasmni tekshirishda xatolik.**\n\nIltimos, matnni yozma yuboring.",
                parse_mode="Markdown",
            )

    except Exception as e:
        log_error(logger, e, user_id, "Handle photo")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


# ============================================
# ADMIN KOMANDALARI
# ============================================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun umumiy statistika"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    stats_text = get_admin_stats_text()
    await update.message.reply_text(stats_text, parse_mode="Markdown")


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi o'z statistikasini ko'rish"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    stats = get_user_statistics(user_id)

    if not stats:
        await update.message.reply_text("❌ Statistikangiz topilmadi.")
        return

    text = (
        f"📊 **Sizning statistikangiz**\n\n"
        f"👤 **Foydalanuvchi:** @{stats['username'] or username}\n"
        f"📅 **Birinchi kelgan:** {stats['first_seen'][:10]}\n"
        f"🕐 **Oxirgi kelgan:** {stats['last_seen'][:10]}\n\n"
        f"📝 **Jami so'rovlar:** {stats['total_requests']}\n"
        f"✅ **Task tekshirishlar:** {stats['task_checks']}\n"
        f"👨‍🏫 **AI Ustoz so'rovlari:** {stats['teacher_requests']}\n"
    )

    if stats["top_tasks"]:
        text += f"\n🔥 **Eng ko'p tekshirgan Aufgabe:**\n"
        for task in stats["top_tasks"]:
            text += f"  • Aufgabe {task['task_number']}: {task['count']} marta\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin barcha foydalanuvchilarga xabar yuborish"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    message_text = " ".join(context.args)

    if not message_text:
        await update.message.reply_text(
            "❌ Xabar matnini yozing!\n\nMasalan: /broadcast Salom hammaga!"
        )
        return

    users = get_all_users()
    sent = 0
    failed = 0

    await update.message.reply_text(f"📨 Xabar {len(users)} foydalanuvchiga yuborilmoqda...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 **Yangilik!**\n\n{message_text}",
                parse_mode="Markdown",
            )
            sent += 1
        except:
            failed += 1

        await asyncio.sleep(0.05)

    await update.message.reply_text(f"✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}")


# ============================================
# HANDLERLARNI RO'YXATGA OLISH
# ============================================
def register_schreiben_handlers(app):
    """Handlerlarni ro'yxatdan o'tkazish"""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("my_stats", my_stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(
        CallbackQueryHandler(handle_pagination, pattern="^(page_|back_to_menu)")
    )
    app.add_handler(CallbackQueryHandler(choose_task, pattern=r"^task_"))
    app.add_handler(CallbackQueryHandler(phrases_callback_handler, pattern="^phrases_"))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))