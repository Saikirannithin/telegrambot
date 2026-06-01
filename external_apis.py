import requests
from datetime import datetime

# Weather - Open-Meteo (FREE, no key)
def get_weather(city=""):
    try:
        # Default: auto-detect by IP or use popular Indian cities coordinates
        lat, lon = 17.4065, 78.4772  # Hyderabad default
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        weather_code = current.get("weather_code", 0)
        weather_emojis = {
            0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
            51: "🌦️", 53: "🌧️", 55: "🌧️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
            71: "🌨️", 73: "🌨️", 75: "🌨️", 95: "⛈️", 96: "⛈️", 99: "⛈️"
        }
        
        emoji = weather_emojis.get(weather_code, "🌡️")
        
        return {
            "temp": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "emoji": emoji,
            "raw": data
        }
    except Exception as e:
        return {"error": str(e)}

# News - NewsAPI (FREE tier, needs key)
def get_news(keyword="", api_key=""):
    try:
        if not api_key:
            return {"error": "NewsAPI key not configured"}
        
        if keyword:
            url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=5&apiKey={api_key}"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        articles = data.get("articles", [])
        return {"articles": articles, "raw": data}
    except Exception as e:
        return {"error": str(e)}

# Gold Rate - Frankfurter (FREE, no key)
def get_gold_rate():
    try:
        # XAU (Gold) to USD, then convert to INR approximation
        url = "https://api.frankfurter.app/latest?from=XAU&to=USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        usd_rate = data.get("rates", {}).get("USD", 0)
        # Approximate INR (1 USD ~ 83 INR, 1 oz ~ 31.1 grams)
        inr_per_gram = usd_rate * 83 / 31.1
        
        return {
            "usd_per_oz": usd_rate,
            "inr_per_gram": round(inr_per_gram, 2),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e)}

# Crypto - CoinGecko (FREE, no key)
def get_crypto_price(coin="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,inr&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        coin_data = data.get(coin, {})
        return {
            "usd": coin_data.get("usd"),
            "inr": coin_data.get("inr"),
            "change_24h": coin_data.get("usd_24h_change"),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e)}

# Stock - Alpha Vantage (FREE, 25/day)
def get_stock_price(symbol="AAPL", api_key=""):
    try:
        if not api_key:
            return {"error": "Alpha Vantage key not configured"}
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        quote = data.get("Global Quote", {})
        return {
            "symbol": quote.get("01. symbol"),
            "price": quote.get("05. price"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e)}