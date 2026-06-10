import os

# Telegram
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_ID = 1994630777  # Your Telegram ID

# ZingHR
ZINGHR_SUBSCRIPTION = os.environ.get("ZINGHR_SUBSCRIPTION", "")
ZINGHR_API_TOKEN = os.environ.get("ZINGHR_API_TOKEN", "")

# APIs
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
# Bot Settings
DAILY_ACTIVITY_LIMIT = 40