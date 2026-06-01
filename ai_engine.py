import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def clean_response(raw_data, context_type, user_name=""):
    """Clean API responses through OpenAI to make them human-like"""
    
    prompts = {
        "weather": f"Make this weather data friendly and personal for {user_name}. Add emojis and advice:",
        "news": f"Summarize this news for {user_name} in a conversational, engaging way. Add context and emojis:",
        "stock": f"Make this stock data exciting and personal for {user_name}. Add insights and emojis:",
        "crypto": f"Make this crypto update engaging for {user_name}. Add market insights and emojis:",
        "gold": f"Make this gold rate update friendly for {user_name}. Add investment context if relevant:",
        "zinghr_punchin": f"Create a warm, friendly punch-in message for {user_name}. Add motivation for the day:",
        "zinghr_punchout": f"Create a warm punch-out message for {user_name}. Ask about their day, wish them well:",
        "zinghr_leave": f"Create a friendly leave application confirmation for {user_name}:",
        "general": f"Respond to {user_name} in a friendly, conversational way. Be helpful and warm:"
    }
    
    prompt = prompts.get(context_type, prompts["general"])
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a friendly personal assistant. Keep responses warm, concise, and engaging."},
                {"role": "user", "content": f"{prompt}\n\n{raw_data}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hey {user_name}! Here's what I found: {raw_data}"

def chat_with_ai(user_message, user_name, chat_history):
    """General chat with memory"""
    messages = [{"role": "system", "content": f"You are a friendly personal assistant talking to {user_name}. Be warm, helpful, and conversational."}]
    
    for msg in chat_history[-5:]:  # Last 5 messages for context
        messages.append({"role": "user", "content": msg["message"]})
        messages.append({"role": "assistant", "content": msg["response"]})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OPENAI ERROR: {e}")
    return f"OPENAI ERROR: {e}"