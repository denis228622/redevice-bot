import os
import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Error: BOT_TOKEN environment variable is not set")

ADMIN_CHAT_ID = 1044925457  # Твой Telegram ID

PHOTO, DESCRIPTION, PRICE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📱 Оценить технику", "❓ Что мы скупаем?"],
        ["📞 Связаться с менеджером"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Это бот по скупке техники Re:Device.", reply_markup=reply_markup
    )

async def handle_start_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📱 Оценить технику":
        await update.message.reply_text("Пришли фото техники.")
        return PHOTO

    elif text == "❓ Что мы скупаем?":
        await update.message.reply_text(
            "📦 Скупим:\n"
            "📱 — Смартфоны Android и iPhone\n"
            "💻 — Ноутбуки, приставки, планшеты, ПК\n"
            "⌚ — Apple Watch, AirPods и др."
        )
        return ConversationHandler.END

    elif text == "📞 Связаться с менеджером":
        await update.message.reply_text("Напишите нам в Telegram: @skupka_denis")
        return ConversationHandler.END

    else:
        await update.message.reply_text("Выбери пункт из меню.")
        return ConversationHandler.END

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, пришли фото.")
        return PHOTO
    photo_file = update.message.photo[-1]
    context.user_data['photo_file_id'] = photo_file.file_id
    await update.message.reply_text(
        "Напиши краткое описание техники (модель, состояние, комплектация):"
    )
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Какую цену вы хотите за устройство?")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_text = update.message.text
    context.user_data['price'] = price_text

    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name

    caption = (
        f"Новая заявка на скупку техники:\n"
        f"Пользователь: {username}\n"
        f"Описание: {context.user_data['description']}\n"
        f"Цена: {context.user_data['price']}\n"
        f"Менеджер: @skupka_denis"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=context.user_data['photo_file_id'],
        caption=caption,
    )

    await update.message.reply_text(
        "Спасибо! Ваша заявка отправлена. Мы скоро свяжемся с вами."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оценка отменена.")
    return ConversationHandler.END

async def main():
    nest_asyncio.apply()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("📱 Оценить технику"), handle_start_buttons)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_buttons))

    print("Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
