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