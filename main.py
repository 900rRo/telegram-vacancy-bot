from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Получаем значения из переменных окружения
TELEGRAM_ID = os.getenv("TELEGRAM_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Состояния
SELECT_ACTION, SELECT_CHANNEL, ENTER_VACANCY, CONFIRM_VACANCY, SHOW_INFO, SHOW_SUPPORT = range(6)

# Каналы
CHANNELS = {
    "WorkDrom": "@WorkDrom",
    "Заработок на пляже": "@zarabotoknaplyazhe",
    "Вакансии рядом": "@Job0pening3"
}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Опубликовать вакансию", callback_data="publish")],
        [InlineKeyboardButton("Вопросы", callback_data="info")],
        [InlineKeyboardButton("Поддержка", callback_data="support")]
    ]
    await update.message.reply_text("Привет! Что вы хотите сделать?", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION

# Получение Telegram ID
async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")

# Пинг-функция
async def ping(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=TELEGRAM_ID, text="✅ Я работаю!")
    except Exception as e:
        print(f"Ошибка при отправке пинга: {e}")

# Обработка выбора действия
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Обработка кнопки "Назад"
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

# Выбор канала
async def select_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Прием текста вакансии
async def receive_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vacancy'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Готово", callback_data="publish_vacancy")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    await update.message.reply_text("Вакансия сохранена. Нажмите «Готово», чтобы опубликовать.",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_VACANCY

# Публикация вакансии
async def confirm_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()

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

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("myid", get_my_id))  # временно для получения ID

    # Пинг каждые 5 минут
    app.job_queue.run_repeating(ping, interval=300, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
