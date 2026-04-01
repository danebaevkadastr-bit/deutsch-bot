from telegram import InlineKeyboardMarkup, InlineKeyboardButton

USEFUL_PHRASES = {
    "formell": {
        "title": "📧 **Formell xatlar ushın sózler**",
        "phrases": [
            "Sehr geehrte Frau ... / Sehr geehrter Herr ...",
            "ich möchte mich bei Ihnen erkundigen, ...",
            "ich bedanke mich im Voraus für Ihre Antwort.",
            "Mit freundlichen Grüßen",
            "ich bitte um Informationen bezüglich ..."
        ]
    },
    "informell": {
        "title": "💬 **Informell xatlar ushın sózler**",
        "phrases": [
            "Liebe ... / Lieber ...",
            "wie geht es dir?",
            "ich freue mich auf deine Antwort.",
            "viele Grüße",
            "schreib mir bald zurück!"
        ]
    },
    "einleitung": {
        "title": "✍️ **Kirisiw ushın sózler**",
        "phrases": [
            "ich schreibe dir, weil ...",
            "der Grund für mein Schreiben ist ...",
            "ich möchte mich bei Ihnen für ... bedanken."
        ]
    },
    "abschluss": {
        "title": "🔚 **Juwmaqlawshı bólim ushın sózler**",
        "phrases": [
            "ich freue mich auf Ihre baldige Antwort.",
            "vielen Dank im Voraus.",
            "mit freundlichen Grüßen",
            "viele Grüße"
        ]
    }
}


async def show_useful_phrases(update, context):
    keyboard = [
        [InlineKeyboardButton("📧 Formell", callback_data="phrases_formell")],
        [InlineKeyboardButton("💬 Informell", callback_data="phrases_informell")],
        [InlineKeyboardButton("✍️ Kirish qismi", callback_data="phrases_einleitung")],
        [InlineKeyboardButton("🔚 Yakun qismi", callback_data="phrases_abschluss")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_menu")]
    ]
    await update.message.reply_text(
        "💬 **Paydalı nemis sózleri**\n\nQaysi turdagi iboralarni ko'rmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_phrases_by_type(update, context, phrase_type):
    query = update.callback_query
    await query.answer()
    
    data = USEFUL_PHRASES.get(phrase_type)
    if not data:
        await query.message.reply_text("❌ Iboralar topilmadi.")
        return
    
    text = f"{data['title']}\n\n"
    for i, phrase in enumerate(data['phrases'], 1):
        text += f"{i}. *{phrase}*\n\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_phrases")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def phrases_callback_handler(update, context):
    query = update.callback_query
    data = query.data
    
    if data == "back_to_phrases":
        keyboard = [
            [InlineKeyboardButton("📧 Formell", callback_data="phrases_formell")],
            [InlineKeyboardButton("💬 Informell", callback_data="phrases_informell")],
            [InlineKeyboardButton("✍️ Kirisiw bólimi", callback_data="phrases_einleitung")],
            [InlineKeyboardButton("🔚 Juwmaqlaw bólimi", callback_data="phrases_abschluss")],
            [InlineKeyboardButton("🏠 Bosh bet", callback_data="back_to_menu")]
        ]
        await query.message.edit_text(
            "💬 **Paydalı nemis sózleri**\n\nQanday túrdegi sózlerdi kórgińiz keledi??",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("phrases_"):
        phrase_type = data.split("_")[1]
        await show_phrases_by_type(update, context, phrase_type)