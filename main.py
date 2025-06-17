from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7890639729:AAFSNqu2oayhs8aYh9o9l_T5PjUqLTEl58Q"
bot = Bot(token=TOKEN)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает через вебхук.")

application.add_handler(CommandHandler("start", start))

# Flask-роут для Telegram Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.create_task(application.process_update(update))
    return "ok"

@app.route("/")
def home():
    return "Бот жив!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
