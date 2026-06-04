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
    from database import (
    get_db,
    init_db,
    get_chat_history,
    log_chat,
    save_preferences,
    get_user_preferences,
    add_todo,
    get_todos,
    complete_todo

)
    logger.info("✅ Database loaded")
except Exception as e:
    logger.error(f"❌ Database error: {e}")
    def get_db(): return None
    def init_db(): pass

try:
    from ai_engine import(clean_response, chat_with_ai, detect_intent, extract_preferences, extract_task_info) 
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

# --- Inline weather function (no external_apis import) ---
def get_weather():
    """Get weather using Open-Meteo (FREE, no API key)"""
    try:
        import requests
        lat, lon = 17.4065, 78.4772
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        current = data.get("current", {})
        
        weather_emojis = {
            0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 
            45: "🌫️", 48: "🌫️",
            51: "🌦️", 53: "🌧️", 55: "🌧️", 
            61: "🌧️", 63: "🌧️", 65: "🌧️",
            71: "🌨️", 73: "🌨️", 75: "🌨️", 
            95: "⛈️", 96: "⛈️", 99: "⛈️"
        }
        
        emoji = weather_emojis.get(current.get("weather_code", 0), "🌡️")
        
        return {
            "temp": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "emoji": emoji
        }
    except Exception as e:
        return {"error": str(e)}

logger.info("✅ Weather function loaded inline")

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
        c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
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
        c.execute("""INSERT INTO users (user_id, username, first_name)
                  VALUES (%s, %s, %s)
                  ON CONFLICT (user_id) DO NOTHING
                  """,(user_id, username, first_name))
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
        c.execute("SELECT activity_count FROM users WHERE user_id = %s", (user_id,))
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
        c.execute("UPDATE users SET activity_count = activity_count + 1 WHERE user_id = %s", (user_id,))
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
    if user_id == ADMIN_ID:
            conn = get_db()
            c = conn.cursor()

            c.execute("""
                      INSERT INTO users
                      (user_id, username, first_name, status)
                      VALUES (%s, %s, %s, 'approved')
                      ON CONFLICT (user_id)
                      DO UPDATE SET status='approved'
                      """, (user_id, user.username, user.first_name))
            conn.commit()
            conn.close()



    
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
        c.execute("UPDATE users SET status = 'approved' WHERE user_id = %s", (user_id,))
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
        c.execute("""
                  INSERT INTO zinghr_users (user_id, employee_code)
                  VALUES (%s, %s) 
                  ON CONFLICT (user_id)     
                  DO UPDATE SET employee_code = EXCLUDED.employee_code 
                  """,(user_id, code))
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
        c.execute("SELECT employee_code FROM zinghr_users WHERE user_id = %s", (user_id,))
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
        c.execute("SELECT employee_code FROM zinghr_users WHERE user_id = %s", (user_id,))
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

async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    prefs = get_user_preferences(user_id)

    if not prefs:
        await update.message.reply_text(
            "👤 I don't know much about you yet.\n\n"
            "Tell me things like:\n"
            "• I am a Product Manager\n"
            "• I live in Hyderabad\n"
            "• I follow AI and Tech news"
        )
        return

    profile = (
        f"👤 Your Profile\n\n"
        f"💼 Profession: {prefs[8] or 'Not set'}\n\n"
        f"📍 City: {prefs[9] or 'Not set'}\n\n"
        f"⏰ Work Start: {prefs[1] or 'Not set'}\n\n"
        f"🎯 Interests: {prefs[2] or 'Not set'}\n\n"
        f"📈 Stocks: {prefs[3] or 'Not set'}\n\n"
        f"₿ Crypto: {prefs[4] or 'Not set'}\n\n"
        f"📰 Daily Briefing: {'Enabled' if prefs[5] else 'Disabled'}\n"
        f"🕗 Briefing Time: {prefs[10] or '08:00'}"
    )

    await update.message.reply_text(profile)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not telegram_app:
        await update.message.reply_text("❌ Bot not initialized!")
        return
    
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text

    
    prefs = extract_preferences(text)
    logger.info(f"EXTRACTED PREFS: {prefs}")
    if prefs and any(v is not None for v in prefs.values()):
        logger.info("SAVING PREFERENCES")
        save_preferences(user_id, prefs)


    
    db_user = get_user(user_id)
    if not db_user or (len(db_user) > 3 and db_user[3] != "approved"):
        await update.message.reply_text("⏳ Need approval. Use /start")
        return
    
    can_proceed, count = check_activity_limit(user_id)
    if not can_proceed:
        await update.message.reply_text(f"⚠️ Daily limit: {DAILY_ACTIVITY_LIMIT}")
        return
    
    # Get chat history for context
    history = get_chat_history(user_id)
    intent = detect_intent(text)
    logger.info(f"INTENT DETECTED: {intent}")
    logger.info(f"USER MESSAGE: {text}")


    try: 
        # Weather Intent 
        if intent == "weather":
            logger.info("WEATHER INTENT DETECTED")
            data = get_weather()

            if "error" in data:
                response = f"Weather error: {data['error']}"

            else:
                raw = (
                    f"Temperature: {data.get('temp')}°C, "
                    f"Humidity: {data.get('humidity')}%, "
                    f"{data.get('emoji')}"
                    )
                response = clean_response(raw, "weather", name)

                    # Punch In Intent
        elif intent == "punchin":
            await punchin(update, context)
            return
        
        #Punch Out Intent
        elif intent == "punchout":
            await punchout(update, context)
            return
        #todo intent

        elif intent == "todo_add":
            task_info = extract_task_info(text)
            logger.info(f"TASK INFO: {task_info}")
            
            if task_info:
                 task = task_info.get("task")
                 if task:
                     add_todo(user_id, task)
                     await update.message.reply_text(
                    f"✅ Added to your todo list:\n\n{task}"
                     )  
                 else:  
                   await update.message.reply_text("❌ Could not Understand task.")
            else:
                 await update.message.reply_text("❌ Could not extarct task.")
            return
        
        #Normal AI Chat
        else:
            logger.info("GENERAL CHAT INTENT") 
            response = chat_with_ai(text, name, history)




    
    # Use AI for response (if OpenAI key is configured)
   
        
    except Exception as e:
        logger.error(f"AI error: {e}")
        logger.exception("AI error")
        response = f"AI ERROR: {str(e)}"
    # Log chat
    log_chat(user_id, text, response)
    
    await update.message.reply_text(response)
    increment_activity(user_id)   
# --- Register Handlers ---
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("approve", approve))
    telegram_app.add_handler(CommandHandler("weather", weather_cmd))
    telegram_app.add_handler(CommandHandler("myprofile", myprofile))
    telegram_app.add_handler(CommandHandler("zinghrsetup", zinghr_setup))
    telegram_app.add_handler(CommandHandler("punchin", punchin))
    telegram_app.add_handler(CommandHandler("punchout", punchout))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook Routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("🔔 WEBHOOK RECEIVED!")
    
    if not telegram_app:
        logger.error("❌ telegram_app is None")
        return "Bot not initialized", 500
    
    try:
        json_data = request.get_json(force=True)
        logger.info(f"📦 JSON: {json_data}")
        
        # Check if update_id exists
        if not json_data or 'update_id' not in json_data:
            logger.error("❌ Invalid JSON: no update_id")
            return "Invalid update", 400
        
        update = Update.de_json(json_data, telegram_app.bot)
        logger.info(f"📨 Update: {update.update_id}")
        
        # Process with try-except inside
        try:
            logger.info("⚙️ Processing...")
            loop.run_until_complete(telegram_app.process_update(update))
            logger.info("✅ Success")
            return "OK", 200
        except Exception as process_error:
            logger.error(f"❌ Process error: {process_error}")
            import traceback
            logger.error(traceback.format_exc())
            return f"Process error: {str(process_error)}", 500
            
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error: {str(e)}", 500

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
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
        logger.info(f"🚀 Webhook set to: {WEBHOOK_URL}/webhook")
    except Exception as e:
        logger.error(f"Init error: {e}")


init_bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))