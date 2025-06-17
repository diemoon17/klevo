import logging
from queue import Queue
from flask import Flask, request
from telegram import Bot, Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# Настройки
TOKEN = "7890639729:AAFSNqu2oayhs8aYh9o9l_T5PjUqLTEl58Q"
ADMIN_ID = 425785910  # Твой ID

# Логгирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
print("🔧 Flask стартует...")

# Инициализация
bot = Bot(token=TOKEN)
app = Flask(__name__)
update_queue = Queue()
dispatcher = Dispatcher(bot, update_queue, workers=0, use_context=True)

# Память пользователя
user_data = {}

# Компании
companies = [
    "🏠 Clean House Almaty (от 600 тг/м²)",
    "🧽 UBORKA.KZ (от 700 тг/м²)",
    "🧼 CleanExpert (от 800 тг/м²)",
    "✨ Crystal Clean (от 700 тг/м²)",
    "🌿 Eco Cleaning (от 750 тг/м²)"
]

# Старт
def start(update, context):
    user_id = update.message.chat_id
    user_data[user_id] = {"step": "company"}
    buttons = [[KeyboardButton(name)] for name in companies]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    update.message.reply_text("Выберите клининговую компанию:", reply_markup=markup)

# Обработка сообщений
def handle_message(update, context):
    user_id = update.message.chat_id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {"step": "company"}
        update.message.reply_text("Пожалуйста, начните с команды /start")
        return

    state = user_data[user_id]

    if text == "⬅️ Назад":
        step_order = ["company", "type", "datetime", "contact", "area"]
        current_step = state.get("step")
        if current_step in step_order and step_order.index(current_step) > 0:
            prev_step = step_order[step_order.index(current_step) - 1]
            state["step"] = prev_step
            if prev_step == "company":
                buttons = [[KeyboardButton(name)] for name in companies]
                markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
                update.message.reply_text("Выберите клининговую компанию:", reply_markup=markup)
            elif prev_step == "type":
                update.message.reply_text("Опишите, какую уборку вы хотите:", reply_markup=ReplyKeyboardRemove())
            elif prev_step == "datetime":
                update.message.reply_text("Укажите дату, время и адрес:")
            elif prev_step == "contact":
                update.message.reply_text("Введите ваше имя и номер телефона:")
            return

    if state["step"] == "company":
        state["company"] = text
        state["step"] = "type"
        update.message.reply_text(
            "Опишите, какую уборку вы хотите (можно несколько, например: Генеральная + мойка окон):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ Назад")]], resize_keyboard=True)
        )

    elif state["step"] == "type":
        state["type"] = text
        state["step"] = "datetime"
        update.message.reply_text(
            "Укажите дату, время и адрес (в одном сообщении):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ Назад")]], resize_keyboard=True)
        )

    elif state["step"] == "datetime":
        state["datetime"] = text
        state["step"] = "contact"
        update.message.reply_text(
            "Введите ваше имя и номер телефона:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ Назад")]], resize_keyboard=True)
        )

    elif state["step"] == "contact":
        state["contact"] = text
        state["step"] = "area"
        update.message.reply_text(
            "Укажите площадь помещения (в м²):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ Назад")]], resize_keyboard=True)
        )

    elif state["step"] == "area":
        state["area"] = text
        state["step"] = "done"

        summary = (
            f"✅ Ваша заявка принята!\n\n"
            f"📦 Компания: {state['company']}\n"
            f"🧹 Тип уборки: {state['type']}\n"
            f"📅 Дата и адрес: {state['datetime']}\n"
            f"👤 Контакт: {state['contact']}\n"
            f"📏 Площадь: {state['area']} м²\n\n"
            f"💬 Примерная цена указана компанией, менеджер свяжется с вами для уточнения.\n"
            f"Спасибо за заявку!"
        )

        update.message.reply_text(summary, reply_markup=ReplyKeyboardRemove())
        bot.send_message(chat_id=ADMIN_ID, text=f"📬 Новая заявка:\n\n{summary}")
        update.message.reply_text("Чтобы отправить новую заявку, нажмите /start.")
        user_data.pop(user_id)

# Команда /cancel
def cancel(update, context):
    user_id = update.message.chat_id
    if user_id in user_data and user_data[user_id].get("step") == "done":
        user_data.pop(user_id)
        update.message.reply_text("Заявка отменена.")
    else:
        update.message.reply_text("Отмена доступна только на последнем этапе.")

# Роуты и хендлеры
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("cancel", cancel))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот на Flask работает"

# Запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
