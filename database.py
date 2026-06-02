import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    return psycopg2.connect(DATABASE_URL)


def create_user_preferences(user_id):
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute( """
        INSERT INTO user_preferences (user_id)
        VALUES (%s)
        ON CONFLICT (user_id)
        DO NOTHING
        """, (user_id,) )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error creating user preferences: {e}")


def get_user_preferences(user_id):
    try:
        conn =get_db()
        c = conn.cursor()

        c.execute( """
                SELECT *
                  FROM user_preferences
                    WHERE user_id = %s
                """, (user_id,) )
        result = c.fetchone()
        conn.close()

        return result
    except Exception as e:
        print(f"Error getting user preferences: {e}")
        return None
    

def update_work_start(user_id, work_start):
    try:
        conn=get_db()
        c = conn.cursor()   

        c.execute( """
        UPDATE user_preferences
        SET work_start = %s
        WHERE user_id = %s
        """, (work_start, user_id) )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating work start: {e}")





def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        message TEXT,
        response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS briefing_settings (
        user_id BIGINT PRIMARY KEY,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS zinghr_users (
        user_id BIGINT PRIMARY KEY,
        employee_code TEXT,
        subscription_name TEXT,
        api_token TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        text TEXT,
        remind_at TIMESTAMP,
        type TEXT DEFAULT 'time',
        condition TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        text TEXT,
        done INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
         user_id BIGINT PRIMARY KEY,
         profession TEXT,
         city TEXT,
         work_start TEXT,
         interests TEXT,
         stocks TEXT,
         crypto TEXT,
         daily_briefing BOOLEAN DEFAULT FALSE,
         preferred_briefing_time TEXT DEFAULT '08:00',
         onboarding_complete BOOLEAN DEFAULT FALSE,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        c.execute("ALTER TABLE user_preferences ADD COLUMN profession TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE user_preferences ADD COLUMN city TEXT")
    except:
        pass
    try:
        c.execute("ALTER TABLE user_preferences ADD COLUMN preferred_briefing_time TEXT DEFAULT '08:00'")
    except:
        pass

def save_preferences(user_id, prefs):
    try:
        conn=get_db()
        c = conn.cursor()

        c.execute( """
                  INSERT INTO user_preferences(user_id)
                  VALUES (%s)
                    ON CONFLICT (user_id) DO NOTHING
        """, (user_id,) )

        allowed_fields = ["profession", "city", "work_start", "interests", "stocks", "crypto", "daily_briefing", "preferred_briefing_time"]

        for key, value in prefs.items():
            if key in allowed_fields and value is not None:
                c.execute(
                    f"UPDATE user_preferences SET {key} = %s WHERE user_id = %s, 
                    (str(value), user_id)
                     )
                
         conn.commit()
         conn.close()

         except Exception as e:
                print(f"Save PREF ERROR: {e}")

                    
        
        
            



    conn.commit()
    conn.close()


# =========================
# CHAT HISTORY
# =========================

def log_chat(user_id, message, response):
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO chat_history
            (user_id, message, response)
            VALUES (%s, %s, %s)
            """,
            (user_id, message, response)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging chat: {e}")


def get_chat_history(user_id, limit=5):
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute(
            """
            SELECT message, response
            FROM chat_history
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT %s
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


def reset_daily_activity():
    try:
        conn = get_db()
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


init_db()