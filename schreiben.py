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

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📚 Aufgabe tanlash"), KeyboardButton("👨‍🏫 AI Ustoz")],
    ],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "Xush kelibsiz 🤖\n\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu,
    )


def build_buttons():
    keyboard = []
    row = []

    for i in range(1, 21):
        row.append(InlineKeyboardButton(f"Aufgabe {i}", callback_data=f"task_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Aufgabe tanlang:",
        reply_markup=build_buttons(),
    )


async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        task_num = int(query.data.split("_")[1])
        context.user_data["task"] = task_num
        context.user_data["task_name"] = f"Aufgabe {task_num}"
        context.user_data["mode"] = None

        task = TASKS[task_num]

        await query.message.reply_text(
            f"✅ Aufgabe {task_num}\n\n"
            f"{task['task']}\n\n"
            f"Punkte:\n"
            f"- {task['points'][0]}\n"
            f"- {task['points'][1]}\n"
            f"- {task['points'][2]}\n\n"
            f"Min: {task['min_words']} so‘z\n"
            f"Stil: {task['style']}\n\n"
            f"Endi matn yozing yoki rasm yuboring."
        )
    except Exception as e:
        await query.message.reply_text(f"Aufgabe tanlashda xatolik:\n{e}")


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # AI Ustoz rejimi
    if context.user_data.get("mode") == "teacher":
        try:
            await update.message.reply_text("Ustoz javob bermoqda...")

            prompt = f"""
Sen nemis tili ustozisan.

Foydalanuvchi savoli:
{text}

Quyidagicha javob ber:
1. Mavzuni oddiy va tushunarli qilib tushuntir
2. Muhim qoidani ayt
3. 3 ta nemischa misol ber
4. Eng ko‘p qilinadigan xatoni ayt
5. Oxirida kichik mashq ber

Javob o‘zbek tilida bo‘lsin, misollar nemis tilida bo‘lsin.
Juda uzun yozma.
"""

            response = model.generate_content(prompt)
            await update.message.reply_text(response.text)

        except Exception as e:
            await update.message.reply_text(f"AI Ustoz xatoligi:\n{e}")

        context.user_data["mode"] = None
        return

    # Aufgabe tugmasi
    if "Aufgabe" in text:
        await show_tasks(update, context)
        return

    # AI Ustoz tugmasi
    if "Ustoz" in text:
        context.user_data["mode"] = "teacher"
        await update.message.reply_text(
            "👨‍🏫 AI Ustoz\n\nQaysi mavzuda yordam kerak?\nMasalan: Perfekt, Artikel, B1 Schreiben"
        )
        return

    # Oddiy matn yuborilgan bo‘lsa, Aufgabe tanlangan bo‘lishi kerak
    if "task" not in context.user_data:
        await update.message.reply_text("Avval Aufgabe tanlang")
        return

    try:
        task = TASKS[context.user_data["task"]]
        current_task = context.user_data.get("task_name", "Noma’lum Aufgabe")

        await update.message.reply_text(
            f"📌 Tanlangan: {current_task}\n\nTekshiryapman..."
        )

        prompt = f"""
Sen nemis tili Schreiben imtihon tekshiruvchisisan.

Tanlangan Aufgabe:
{task['task']}

Majburiy punktlar:
- {task['points'][0]}
- {task['points'][1]}
- {task['points'][2]}

Talablar:
- Kamida {task['min_words']} ta so‘z bo‘lsin
- Stil: {task['style']}

Foydalanuvchi matni:
{text}

Javobni FAQAT quyidagi 3 bo‘limda ber:

1. QISQA XULOSA
- so‘zlar soni
- talab bajarilganmi
- punktlar bajarilganmi
- stil to‘g‘rimi
- 1-2 gaplik umumiy izoh

2. XATOLAR VA TO‘G‘RILASH
- faqat xatolar bo‘lsa yoz
- har bir xato uchun:
  xato → to‘g‘risi → qisqa tushuntirish
- agar xato bo‘lmasa: "Jiddiy xato topilmadi" deb yoz

3. BAHOLASH
- Inhalt: x/6
- Stil: x/4
- Grammatik/Wortschatz: x/6
- Aufbau: x/2
- Wortzahl: x/2
- Jami: x/20

Muhim:
- Juda uzun yozma
- Soddaroq, ixcham, o‘qishga qulay bo‘lsin
- Barcha javob o‘zbek tilida bo‘lsin
"""

        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"Matn tekshirishda xatolik:\n{e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") == "teacher":
        await update.message.reply_text("AI Ustoz rejimidasiz. Avval mavzuni yozing.")
        return

    if "task" not in context.user_data:
        await update.message.reply_text("Avval Aufgabe tanlang")
        return

    try:
        task = TASKS[context.user_data["task"]]
        current_task = context.user_data.get("task_name", "Noma’lum Aufgabe")

        await update.message.reply_text(
            f"📌 Tanlangan: {current_task}\n\nRasm tekshiryapman..."
        )

        photo = update.message.photo[-1]
        file = await photo.get_file()
        await file.download_to_drive("image.jpg")

        with open("image.jpg", "rb") as f:
            img = f.read()

        prompt = f"""
Sen nemis tili Schreiben imtihon tekshiruvchisisan.

Tanlangan Aufgabe:
{task['task']}

Majburiy punktlar:
- {task['points'][0]}
- {task['points'][1]}
- {task['points'][2]}

Talablar:
- Kamida {task['min_words']} ta so‘z bo‘lsin
- Stil: {task['style']}

Vazifa:
1. Rasmdagi nemischa matnni o‘qib chiq
2. Matnni tekshir

Javobni FAQAT quyidagi 3 bo‘limda ber:

1. QISQA XULOSA
- so‘zlar soni
- talab bajarilganmi
- punktlar bajarilganmi
- stil to‘g‘rimi
- 1-2 gaplik umumiy izoh

2. XATOLAR VA TO‘G‘RILASH
- faqat xatolar bo‘lsa yoz
- har bir xato uchun:
  xato → to‘g‘risi → qisqa tushuntirish
- agar xato bo‘lmasa: "Jiddiy xato topilmadi" deb yoz

3. BAHOLASH
- Inhalt: x/6
- Stil: x/4
- Grammatik/Wortschatz: x/6
- Aufbau: x/2
- Wortzahl: x/2
- Jami: x/20

Muhim:
- Juda uzun yozma
- Soddaroq, ixcham, o‘qishga qulay bo‘lsin
- Barcha javob o‘zbek tilida bo‘lsin
"""

        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": img}]
        )
        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"Rasm xatoligi:\n{e}")


def register_schreiben_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_task, pattern=r"^task_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))