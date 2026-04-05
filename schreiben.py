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
ADMIN_IDS = [846543597]  # Danebaev_M ID si

# Asosiy menyu
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📚 Aufgabe tanlaw"), KeyboardButton("👨‍🏫 AI Ustaz")],
        [KeyboardButton("💬 Paydalı sózler")],
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
            "Men nemis tilin úyreniwshiler ushın járdemshi botpan.\n\n"
            "📝 **Ne qıla alaman?**\n"
            "• B1 Schreiben Aufgabe-ların tekseriw\n"
            "• AI Ustaz sıpatında nemis tili sorawlarına juwap beriw\n"
            "• Paydalı nemis sózleri\n\n"
            "Kerekli bólimdi tańlań 👇",
            reply_markup=main_menu,
            parse_mode="Markdown",
        )
    except Exception as e:
        log_error(logger, e, user_id, "Start")
        await update.message.reply_text("❌ Qátelik júz berdi.")


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
            InlineKeyboardButton("◀️ Aldınǵı", callback_data=f"page_{current_page - 1}")
        )
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Keyingi ▶️", callback_data=f"page_{current_page + 1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🏠 Bas menyu", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(keyboard)


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aufgabe-larni ko'rsatish"""
    user_id = update.effective_user.id

    try:
        context.user_data["current_page"] = 0

        await update.message.reply_text(
            "📚 **Aufgabe tańlań** (1-20)\n\nTómendegi túymelerden birin basıń:",
            reply_markup=build_buttons(0),
            parse_mode="Markdown",
        )
        logger.info(f"Tasks shown to user {user_id}")
    except Exception as e:
        log_error(logger, e, user_id, "Show tasks")
        await update.message.reply_text("❌ Aufgabe-lardı júklewde xátelik júz berdi.")


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
                "🏠 **Bas menyu**\n\nKerekli bólimdi tańlań:",
                reply_markup=main_menu,
                parse_mode="Markdown",
            )
            return

        if data.startswith("page_"):
            page = int(data.split("_")[1])
            context.user_data["current_page"] = page

            await query.message.edit_text(
                f"📚 **Aufgabe tańlań** (1-20)\n\nSahifa {page + 1}/{(len(TASKS) + 9) // 10}",
                reply_markup=build_buttons(page),
                parse_mode="Markdown",
            )
    except Exception as e:
        log_error(logger, e, user_id, f"Pagination: {data}")
        await query.message.reply_text("❌ Xátelik júz berdi.")


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
            f"📝 **Wazıypa:**\n{task['task']}\n\n"
            f"🎯 **Májbúriy punktler:**\n"
            f"• {task['points'][0]}\n"
            f"• {task['points'][1]}\n"
            f"• {task['points'][2]}\n\n"
            f"📏 **Sózler sanı:** Káminde {task['min_words']} sóz\n"
            f"✍️ **Stil:** {task['style'].upper()}\n\n"
            f"---\n"
            f"✏️ **Endi tekst jazıń** yamasa 📸 **suwret jiberiń**.\n"
            f"Men sizdiń jazǵanıńızdı tekserip, bahalayman."
        )

        await query.message.reply_text(task_info, parse_mode="Markdown")
        logger.info(f"Task {task_num} selected by user {user_id} ({username})")

    except Exception as e:
        log_error(logger, e, user_id, f"Choose task: {query.data if query else 'None'}")
        await query.message.reply_text("❌ Aufgabe tańlawda xátelik júz berdi.")


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
            try:
                log_teacher_request(user_id, len(text), response_time)
            except Exception as e:
                logger.error(f"Log teacher error: {e}")
            return

        # --- AUFGABE TANLASH TUGMASI ---
        if "Aufgabe" in text or "Aufgabe" in text:
            await show_tasks(update, context)
            return

        # --- AI USTOZ TUGMASI ---
        if "Ustaz" in text or "Ustaz" in text:
            await teacher_mode_start(update, context)
            return

        # --- FOYDALI IBORALAR TUGMASI ---
        if "Paydalı iboralar" in text or "Foydali iboralar" in text:
            await show_useful_phrases(update, context)
            return

        # --- MATN TEKSHIRISH ---
        if "task" not in context.user_data:
            await update.message.reply_text(
                "⚠️ **Aldın Aufgabe tańlań!**\n\n"
                "📚 **Aufgabe tańlaw** túymesin basıń yamasa\n"
                "👨‍🏫 **AI Ustaz** rejiminen paydalanıń.",
                parse_mode="Markdown",
            )
            return

        try:
            task = TASKS[context.user_data["task"]]
            current_task = context.user_data.get("task_name", "Noma'lum Aufgabe")

            loading_msg = await update.message.reply_text(
                f"📌 **Tańlanǵan:** {current_task}\n\n"
                f"🔍 Tekst tekserilmekte...\n"
                f"⏳ Iltimas, kútiń (10-20 sekund)",
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
            await update.message.reply_text(response.text)

            try:
                log_task_check(user_id, context.user_data["task"], len(text))
            except Exception as e:
                logger.error(f"Log task error: {e}")
            logger.info(
                f"Task {context.user_data['task']} checked for user {user_id} ({username})"
            )

        except asyncio.TimeoutError:
            await loading_msg.delete()
            await update.message.reply_text(
                "⏰ **Tekseriw kóp waqıt aldı.**\n\n"
                "Tekstti qısqartırıp qayta jiberiń."
            )
        except Exception as e:
            log_error(logger, e, user_id, f"Task checking")
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ **Tekstti tekseriwde xátelik júz berdi.**\n\n"
                "Qayta urınıp kóriń."
            )

    except Exception as e:
        log_error(logger, e, user_id, f"Text router")
        await update.message.reply_text(
            "❌ **Kutilmegen qátelik.**\n\nIltimas, /start buyrıǵın basıń."
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm yuborilganda - rasmdagi matnni o'qib tekshirish"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    update_user_request(user_id)

    try:
        if context.user_data.get("mode") == "teacher":
            await update.message.reply_text(
                "👨‍🏫 **AI Ustaz rejimindesiz**\n\n"
                "Súwret emes, tekst kórinisinde sorawıńızdı jazıń."
            )
            return

        if "task" not in context.user_data:
            await update.message.reply_text(
                "⚠️ **Aldın Aufgabe tańlań!**\n\n📚 Aufgabe tańlaw túymesin basıń."
            )
            return

        try:
            task = TASKS[context.user_data["task"]]
            current_task = context.user_data.get("task_name", "Noma'lum Aufgabe")

            loading_msg = await update.message.reply_text(
                f"📌 **Tańlanǵan:** {current_task}\n\n"
                f"🖼️ Súwret tekserilmekte...\n"
                f"⏳ Iltimas, kútiń (20-30 sekund)"
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
            await update.message.reply_text(response.text)

            try:
                log_task_check(user_id, context.user_data["task"], 0)
            except Exception as e:
                logger.error(f"Log photo error: {e}")
            logger.info(f"Photo checked for user {user_id} ({username})")

        except asyncio.TimeoutError:
            await loading_msg.delete()
            await update.message.reply_text(
                "⏰ **Suwretti tekseriw kóp waqıt aldı.**\n\n"
                "Tekstti jazba túrinde jiberiń."
            )
        except Exception as e:
            log_error(logger, e, user_id, f"Photo checking")
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ **Suwretti tekseriwde xátelik.**\n\nTekstti jazba túrinde jiberiń."
            )

    except Exception as e:
        log_error(logger, e, user_id, "Handle photo")
        await update.message.reply_text("❌ Qátelik júz berdi.")


# ============================================
# ADMIN KOMANDALARI
# ============================================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun umumiy statistika"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emessiz!")
        return

    stats_text = get_admin_stats_text()
    await update.message.reply_text(stats_text, parse_mode="Markdown")


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi o'z statistikasini ko'rish"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    stats = get_user_statistics(user_id)

    if not stats:
        await update.message.reply_text("❌ Statistikangiz tabılmadı.")
        return

    text = (
        f"📊 **Sizdiń statistikańız**\n\n"
        f"👤 **Paydalanıwshı:** @{stats['username'] or username}\n"
        f"📅 **Birinši kelgen:** {stats['first_seen'][:10]}\n"
        f"🕐 **Aqırǵı kelgen:** {stats['last_seen'][:10]}\n\n"
        f"📝 **Jámi sorawlar:** {stats['total_requests']}\n"
        f"✅ **Task tekseriwler:** {stats['task_checks']}\n"
        f"👨‍🏫 **AI Ustaz sorawları:** {stats['teacher_requests']}\n"
    )

    if stats["top_tasks"]:
        text += f"\n🔥 **Eń kóp teksergen Aufgabe:**\n"
        for task in stats["top_tasks"]:
            text += f"  • Aufgabe {task['task_number']}: {task['count']} márte\n"

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
            "❌ Xabar matnın jazıń!\n\nMáselen: /broadcast Hámmaga salem!"
        )
        return

    users = get_all_users()
    sent = 0
    failed = 0

    await update.message.reply_text(f"📨 Xabar {len(users)} paydalanıwshıǵa jiberilmekte...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 **Jańalıq!**\n\n{message_text}",
                parse_mode="Markdown",
            )
            sent += 1
        except:
            failed += 1

        await asyncio.sleep(0.05)

    await update.message.reply_text(f"✅ Jiberilgen: {sent}\n❌ Jiberilmegen: {failed}")


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