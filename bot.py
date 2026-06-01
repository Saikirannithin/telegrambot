import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Config ---
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App (MUST be at module level for Gunicorn) ---
app = Flask(__name__)

# --- Telegram App ---
telegram_app = Application.builder().token(TOKEN).build()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"I'm your bot. I'm alive! 🚀\n"
        f"Send me any message and I'll echo it back."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "\nJust send any text and I'll reply!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"📝 You said: {text}")

# --- Register Handlers ---
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.create_task(telegram_app.process_update(update))
    return "OK", 200

@app.route("/")
def health():
    return "✅ Bot is running!", 200

# --- Startup ONLY when running directly (not when imported by Gunicorn) ---
if __name__ == "__main__":
    telegram_app.initialize()
    telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logger.info(f"🚀 Webhook set to: {WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=PORT)