import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Можно передавать несколько ID через запятую, например "12345678,87654321"
ALLOWED_USERS = list(map(int, os.getenv("TELEGRAM_ID", "").split(",")))
PORT = int(os.environ.get("PORT", 8443))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Состояния
SELECT_ACTION, SELECT_CHANNEL, ENTER_VACANCY, CONFIRM_VACANCY, SHOW_INFO, SHOW_SUPPORT = range(6)

CHANNELS = {
    "WorkDrom": "@WorkDrom",
    "Заработок на пляже": "@zarabotoknaplyazhe",
    "Вакансии рядом": "@Job0pening3"
}

def user_is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Опубликовать вакансию", callback_data="publish")],
        [InlineKeyboardButton("Вопросы", callback_data="info")],
        [InlineKeyboardButton("Поддержка", callback_data="support")]
    ]
    await update.message.reply_text("Привет! Что вы хотите сделать?", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")

async def ping(context: ContextTypes.DEFAULT_TYPE):
    try:
        # Пингуем только первого ID из списка
        if ALLOWED_USERS:
            await context.bot.send_message(chat_id=ALLOWED_USERS[0], text="✅ Я работаю!")
    except Exception as e:
        print(f"Ошибка при отправке пинга: {e}")

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_allowed(user_id):
        await update.callback_query.answer("Доступ запрещён.", show_alert=True)
        return

    query = update.callback_query
    await query.answer()

    if query.data == "publish":
        keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in CHANNELS.keys()]
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_start")])
        await query.edit_message_text("Выберите канал для публикации:", reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_CHANNEL

    elif query.data == "info":
        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
        await query.edit_message_text(
            "Мы публикуем вакансии в трёх Telegram-каналах: WorkDrom, Заработок на пляже и Вакансии рядом. "
            "Выберите «Опубликовать вакансию», чтобы начать.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SHOW_INFO

    elif query.data == "support":
        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
        await query.edit_message_text("По всем вопросам пишите: https://t.me/+Tl8MMZ9tMtEyNzEy",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return SHOW_SUPPORT

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Опубликовать вакансию", callback_data="publish")],
        [InlineKeyboardButton("Вопросы", callback_data="info")],
        [InlineKeyboardButton("Поддержка", callback_data="support")]
    ]
    await query.edit_message_text("Привет! Что вы хотите сделать?", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION

async def select_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_allowed(user_id):
        await update.callback_query.answer("Доступ запрещён.", show_alert=True)
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()
    context.user_data['channel'] = query.data

    example_vacancy = (
        "Пример вакансии:\n\n"
        "🔹 Должность: Менеджер по продажам\n"
        "🔹 Местоположение: Москва\n"
        "🔹 Требования: Опыт работы от 1 года, уверенный пользователь ПК, коммуникабельность.\n"
        "🔹 Условия: Официальное трудоустройство, стабильная заработная плата, карьерный рост.\n"
        "🔹 Заработная плата: 50,000 - 60,000 рублей\n\n"
        "Теперь отправьте текст вакансии в таком же формате."
    )

    await query.edit_message_text(
        f"Вы выбрали канал: {query.data}\n\n{example_vacancy}\n\nТеперь отправьте текст вакансии."
    )
    return ENTER_VACANCY

async def receive_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_allowed(user_id):
        await update.message.reply_text("Доступ запрещён.")
        return ConversationHandler.END

    context.user_data['vacancy'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Готово", callback_data="publish_vacancy")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    await update.message.reply_text("Вакансия сохранена. Нажмите «Готово», чтобы опубликовать.",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_VACANCY

async def confirm_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_allowed(user_id):
        await update.callback_query.answer("Доступ запрещён.", show_alert=True)
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    selected_channel = CHANNELS[context.user_data['channel']]
    vacancy_text = context.user_data['vacancy']

    await context.bot.send_message(
        chat_id=selected_channel,
        text=f"{vacancy_text}\n\nРазмещено через @WorkDromBot"
    )

    await query.edit_message_text("✅ Ваша вакансия успешно опубликована! Чтобы снова запустить бота, напишите /start ему в чат!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_ACTION: [
                CallbackQueryHandler(handle_action),
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
            SELECT_CHANNEL: [
                CallbackQueryHandler(select_channel),
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
            ENTER_VACANCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_vacancy),
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
            CONFIRM_VACANCY: [
                CallbackQueryHandler(confirm_publish, pattern="^publish_vacancy$"),
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
            SHOW_INFO: [
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
            SHOW_SUPPORT: [
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("myid", get_my_id))
    application.job_queue.run_repeating(ping, interval=300, first=10)

    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    print(f"Webhook URL: {webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
