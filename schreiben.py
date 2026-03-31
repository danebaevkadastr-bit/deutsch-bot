async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "task" not in context.user_data:
        await update.message.reply_text("Avval Aufgabe tanlang")
        return

    try:
        task = TASKS[context.user_data["task"]]

        await update.message.reply_text("Rasm tekshiryapman...")

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
2. Matnni to‘liq yozib ber
3. So‘zlar sonini hisobla
4. Har bir punkt bajarilganmi tekshir
5. Stilni tekshir
6. Grammatik xatolarni top
7. To‘g‘ri variantni yoz
8. Ball qo‘y:
   - Inhalt: /6
   - Stil: /4
   - Grammatik/Wortschatz: /6
   - Aufbau: /2
   - Wortzahl: /2
9. Jami ball: /20

Javobni aniq va tartibli qil.
"""

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": img}
        ])

        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"Rasm xatoligi:\n{e}")