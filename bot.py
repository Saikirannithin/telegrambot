import os
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)

# --- Setup logging first ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Create event loop at module level for async operations ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- Safe config loading ---
try:
    from config import BOT_TOKEN, WEBHOOK_URL, ADMIN_ID, DAILY_ACTIVITY_LIMIT
    logger.info(f"✅ Config loaded. Token exists: {bool(BOT_TOKEN)}")
except Exception as e:
    logger.error(f"❌ Config error: {e}")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "dummy")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://example.com")
    ADMIN_ID = 1994630777
    DAILY_ACTIVITY_LIMIT = 40

# --- Safe imports ---
try:
    from database import get_db, init_db
    logger.info("✅ Database loaded")
except Exception as e:
    logger.error(f"❌ Database error: {e}")
    def get_db(): return None
    def init_db(): pass

try:
    from ai_engine import clean_response, chat_with_ai
    logger.info("✅ AI engine loaded")
except Exception as e:
    logger.error(f"❌ AI engine error: {e}")
    def clean_response(raw, context, name=""): return raw
    def chat_with_ai(msg, name, history): return f"Hey {name}! You said: {msg}"

try:
    from zinghr_api import punch_in_out
    logger.info("✅ ZingHR loaded")
except Exception as e:
    logger.error(f"❌ ZingHR error: {e}")
    def punch_in_out(code, direction): return {"error": "ZingHR not configured"}

try:
    from external_apis import get_weather
    logger.info("✅ External APIs loaded")
except Exception as e:
    logger.error(f"❌ External APIs error: {e}")
    def get_weather(): return {"error": "Weather API not configured"}

# --- Flask App ---
app = Flask(__name__)

# --- Telegram App (safe init) ---
try:
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    logger.info("✅ Telegram app created")
except Exception as e:
    logger.error(f"❌ Telegram init failed: {e}")
    telegram_app = None

# --- Helper Functions ---
def get_user(user_id):
    try:
        conn = get_db()
        if not conn:
            return None
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"DB error: {e}")
        return None

def add_user(user_id, username, first_name):
    try:
        conn = get_db()
        if not conn:
            return
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                  (user_id, username, first_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Add user error: {e}")

def check_activity_limit(user_id):
    try:
        conn = get_db()
        if not conn:
            return True, 0
        c = conn.cursor()
        c.execute("SELECT activity_count FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return True, 0
        
        count = result[0]
        if count >= DAILY_ACTIVITY_LIMIT:
            return False, count
        
        return True, count
    except Exception as e:
        logger.error(f"Activity check error: {e}")
        return True, 0

def increment_activity(user_id):
    try:
        conn = get_db()
        if not conn:
            return
        c = conn.cursor()
        c.execute("UPDATE users SET activity_count = activity_count + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Increment error: {e}")

# --- Admin Functions ---
async def notify_admin(bot, message):
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=message)
    except Exception as e:
        logger.error(f"Notify admin failed: {e}")

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not telegram_app:
        await update.message.reply_text("❌ Bot not initialized properly!")
        return
    
    user = update.effective_user
    user_id = user.id
    
    db_user = get_user(user_id)
    
    if not db_user:
        add_user(user_id, user.username, user.first_name)
        await notify_admin(context.bot, 
            f"🆕 New user!\nName: {user.first_name}\nID: {user_id}\n/approve {user_id}")
        
        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            f"⏳ Waiting for admin approval.\n"
            f"Your ID: {user_id}"
        )
        return
    
    status = db_user[3] if len(db_user) > 3 else "pending"
    
    if status == "pending":
        await update.message.reply_text("⏳ Still pending approval.")
        return
    
    if status == "rejected":
        await update.message.reply_text("❌ Access rejected.")
        return
    
    # Approved user
    await update.message.reply_text(
        f"👋 Welcome back {user.first_name}!\n\n"
        f"Commands:\n"
        f"/weather - Weather\n"
        f"/punchin - ZingHR In\n"
        f"/punchout - ZingHR Out\n"
        f"/zinghrsetup <code> - Link ZingHR\n"
        f"Or just chat!"
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        conn = get_db()
        if not conn:
            await update.message.reply_text("❌ Database error!")
            return
        c = conn.cursor()
        c.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Approved user {user_id}")
        await context.bot.send_message(user_id, "🎉 You are approved! Use /start")
    except Exception as e:
        logger.error(f"Approve error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    can_proceed, count = check_activity_limit(user_id)
    if not can_proceed:
        await update.message.reply_text(f"⚠️ Daily limit: {DAILY_ACTIVITY_LIMIT}")
        return
    
    data = get_weather()
    if "error" in data:
        await update.message.reply_text(f"❌ Error: {data['error']}")
        return
    
    raw = f"Temperature: {data.get('temp', 'N/A')}°C, Humidity: {data.get('humidity', 'N/A')}%, {data.get('emoji', '🌡️')}"
    clean = clean_response(raw, "weather", user_name)
    await update.message.reply_text(clean)
    increment_activity(user_id)

async def zinghr_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /zinghrsetup <employee_code>")
        return
    
    user_id = update.effective_user.id
    code = context.args[0]
    
    try:
        conn = get_db()
        if not conn:
            await update.message.reply_text("❌ Database error!")
            return
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO zinghr_users (user_id, employee_code) VALUES (?, ?)",
                  (user_id, code))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ ZingHR linked!\nCode: {code}\nUse /punchin and /punchout"
        )
    except Exception as e:
        logger.error(f"ZingHR setup error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def punchin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    try:
        conn = get_db()
        if not conn:
            await update.message.reply_text("❌ Database error!")
            return
        c = conn.cursor()
        c.execute("SELECT employee_code FROM zinghr_users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            await update.message.reply_text("❌ Link ZingHR first: /zinghrsetup <code>")
            return
        
        code = result[0]
        response = punch_in_out(code, "IN")
        
        if "error" in response:
            await update.message.reply_text(f"❌ Error: {response['error']}")
            return
        
        raw = f"Punched IN at {datetime.now().strftime('%H:%M')}"
        clean = clean_response(raw, "zinghr_punchin", name)
        await update.message.reply_text(clean)
    except Exception as e:
        logger.error(f"Punchin error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def punchout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    try:
        conn = get_db()
        if not conn:
            await update.message.reply_text("❌ Database error!")
            return
        c = conn.cursor()
        c.execute("SELECT employee_code FROM zinghr_users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            await update.message.reply_text("❌ Link ZingHR first: /zinghrsetup <code>")
            return
        
        code = result[0]
        response = punch_in_out(code, "OUT")
        
        if "error" in response:
            await update.message.reply_text(f"❌ Error: {response['error']}")
            return
        
        raw = f"Punched OUT at {datetime.now().strftime('%H:%M')}"
        clean = clean_response(raw, "zinghr_punchout", name)
        await update.message.reply_text(clean)
    except Exception as e:
        logger.error(f"Punchout error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not telegram_app:
        await update.message.reply_text("❌ Bot not initialized!")
        return
    
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text
    
    db_user = get_user(user_id)
    if not db_user or (len(db_user) > 3 and db_user[3] != "approved"):
        await update.message.reply_text("⏳ Need approval. Use /start")
        return
    
    can_proceed, count = check_activity_limit(user_id)
    if not can_proceed:
        await update.message.reply_text(f"⚠️ Daily limit: {DAILY_ACTIVITY_LIMIT}")
        return
    
    # Simple chat response
    await update.message.reply_text(f"Hey {name}! You said: {text}\n\nI'm learning more features!")

# --- Register Handlers ---
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("approve", approve))
    telegram_app.add_handler(CommandHandler("weather", weather_cmd))
    telegram_app.add_handler(CommandHandler("zinghrsetup", zinghr_setup))
    telegram_app.add_handler(CommandHandler("punchin", punchin))
    telegram_app.add_handler(CommandHandler("punchout", punchout))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook Routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    if not telegram_app:
        return "Bot not initialized", 500
    
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        # Use the module-level event loop
        loop.create_task(telegram_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/")
def health():
    return "✅ Personal Assistant Bot is running!", 200

# --- Startup with proper async handling ---
def init_bot():
    if not telegram_app:
        logger.error("❌ Cannot init: telegram_app is None")
        return
    
    if not BOT_TOKEN or BOT_TOKEN == "dummy":
        logger.error("❌ Cannot init: No valid BOT_TOKEN")
        return
    
    try:
        # Use the module-level event loop to run async initialization
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
        logger.info(f"🚀 Webhook set to: {WEBHOOK_URL}/webhook")
    except Exception as e:
        logger.error(f"Init error: {e}")

init_bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))