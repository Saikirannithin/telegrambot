import sqlite3
from datetime import datetime

DB_PATH = "bot_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        status TEXT DEFAULT 'pending',
        ai_option TEXT DEFAULT 'bot',
        openai_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_activity_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activity_count INTEGER DEFAULT 0
    )
    """)

    # Chat history
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Briefing preferences
    c.execute("""
    CREATE TABLE IF NOT EXISTS briefing_settings (
        user_id INTEGER PRIMARY KEY,
        weather INTEGER DEFAULT 1,
        news INTEGER DEFAULT 1,
        custom_news_keywords TEXT,
        tasks INTEGER DEFAULT 1,
        stocks TEXT,
        crypto TEXT,
        gold_rate INTEGER DEFAULT 0,
        health INTEGER DEFAULT 0,
        quote INTEGER DEFAULT 1,
        briefing_time TEXT DEFAULT '08:00',
        timezone TEXT DEFAULT 'Asia/Kolkata',
        enabled INTEGER DEFAULT 1
    )
    """)

    # ZingHR mapping
    c.execute("""
    CREATE TABLE IF NOT EXISTS zinghr_users (
        user_id INTEGER PRIMARY KEY,
        employee_code TEXT,
        subscription_name TEXT,
        api_token TEXT
    )
    """)

    # Reminders
    c.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        remind_at TIMESTAMP,
        type TEXT DEFAULT 'time',
        condition TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Notes
    c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Todos
    c.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        done INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


# =========================
# CHAT HISTORY FUNCTIONS
# =========================

def log_chat(user_id, message, response):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO chat_history
            (user_id, message, response)
            VALUES (?, ?, ?)
            """,
            (user_id, message, response)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging chat: {e}")


def get_chat_history(user_id, limit=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            SELECT message, response
            FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit)
        )

        rows = c.fetchall()
        conn.close()

        history = []

        for row in reversed(rows):
            history.append({
                "message": row[0],
                "response": row[1]
            })

        return history

    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []


# =========================
# ACTIVITY RESET
# =========================

def reset_daily_activity():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            UPDATE users
            SET activity_count = 0,
                last_activity_reset = CURRENT_TIMESTAMP
        """)

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Activity reset error: {e}")


# Initialize database
init_db()