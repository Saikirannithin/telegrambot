import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from @BotFather
TOKEN = "8035671580:AAEMJzGbwRvRM6gseiV8JVY6pXVj2SvJ5BQ"

# Conversation states
NAME, AGE = range(2)


# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        f"Available commands:\n"
        f"/start - Start the bot\n"
        f"/help - Show help\n"
        f"/echo <text> - Echo your message\n"
        f"/survey - Start a short survey\n"
        f"/cancel - Cancel current operation"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    await update.message.reply_text(
        "🤖 *Bot Help*\n\n"
        "Just send me any message and I'll echo it back!\n"
        "Use /survey to try the conversation feature.",
        parse_mode="Markdown"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message (with /echo prefix removed)."""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /echo <your message>")
        return
    await update.message.reply_text(f"📢 {text}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text("❓ Unknown command. Use /help for available commands.")


# --- Conversation Handler (Survey Example) ---

async def survey_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the survey conversation."""
    await update.message.reply_text("Let's do a quick survey! What's your name?")
    return NAME

async def survey_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store name and ask for age."""
    context.user_data["name"] = update.message.text
    await update.message.reply_text(f"Nice to meet you, {update.message.text}! How old are you?")
    return AGE

async def survey_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store age and finish survey."""
    context.user_data["age"] = update.message.text
    name = context.user_data["name"]
    age = context.user_data["age"]
    
    await update.message.reply_text(
        f"✅ Survey complete!\n\n"
        f"Name: {name}\n"
        f"Age: {age}\n\n"
        f"Thanks for participating!"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Survey cancelled. See you next time!")
    return ConversationHandler.END


# --- Message Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")


# --- Error Handler ---

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ An error occurred. Please try again.")


# --- Main ---

def main() -> None:
    """Start the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("echo", echo))

    # Add conversation handler for survey
    survey_conv = ConversationHandler(
        entry_points=[CommandHandler("survey", survey_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, survey_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, survey_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(survey_conv)

    # Handle unknown commands (must be added after all other command handlers)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Handle regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Run the bot until Ctrl+C
    print("🤖 Bot is running... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()