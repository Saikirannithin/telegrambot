from langsmith import expect

import google.generativeai as genai
import json
from config import GEMINI_API_KEY

print("GEMINI KEY EXISTS:", bool(GEMINI_API_KEY))
print("GEMINI KEY LENGTH:", len(GEMINI_API_KEY) if GEMINI_API_KEY else 0)  

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.5-flash")




def clean_response(raw_data, context_type, user_name=""):
    """Clean API responses through Gemini to make them human-like"""

    prompts = {
        "weather": f"Make this weather data friendly and personal for {user_name}. Add emojis and advice:",
        "news": f"Summarize this news for {user_name} in a conversational, engaging way. Add context and emojis:",
        "stock": f"Make this stock data exciting and personal for {user_name}. Add insights and emojis:",
        "crypto": f"Make this crypto update engaging for {user_name}. Add market insights and emojis:",
        "gold": f"Make this gold rate update friendly for {user_name}. Add investment context if relevant:",
        "zinghr_punchin": f"Create a warm, friendly punch-in message for {user_name}. Add motivation for the day:",
        "zinghr_punchout": f"Create a warm punch-out message for {user_name}. Ask about their day and wish them well:",
        "zinghr_leave": f"Create a friendly leave application confirmation for {user_name}:",
        "general": f"Respond to {user_name} in a friendly, conversational way. Be helpful and warm:"
    }

    prompt = prompts.get(context_type, prompts["general"])

    try:
        full_prompt = f"""
You are a friendly personal assistant.

{prompt}

Data:
{raw_data}
"""

        response = model.generate_content(full_prompt)

        return response.text

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return f"Hey {user_name}! Here's what I found: {raw_data}"


def chat_with_ai(user_message, user_name, chat_history):
    """General chat with memory"""

    try:
        history_text = ""

        for msg in chat_history[-5:]:
            history_text += f"""
User: {msg['message']}
Assistant: {msg['response']}
"""

        prompt = f"""
You are a friendly personal assistant talking to {user_name}.

Be warm, helpful and conversational.

Previous Conversation:
{history_text}

Current User Message:
{user_message}
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return f"GEMINI ERROR: {str(e)}"
    


import google.generativeai as genai
from config import GEMINI_API_KEY

print("GEMINI KEY EXISTS:", bool(GEMINI_API_KEY))
print("GEMINI KEY LENGTH:", len(GEMINI_API_KEY) if GEMINI_API_KEY else 0)  

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.5-flash")




def clean_response(raw_data, context_type, user_name=""):
    """Clean API responses through Gemini to make them human-like"""

    prompts = {
        "weather": f"Make this weather data friendly and personal for {user_name}. Add emojis and advice:",
        "news": f"Summarize this news for {user_name} in a conversational, engaging way. Add context and emojis:",
        "stock": f"Make this stock data exciting and personal for {user_name}. Add insights and emojis:",
        "crypto": f"Make this crypto update engaging for {user_name}. Add market insights and emojis:",
        "gold": f"Make this gold rate update friendly for {user_name}. Add investment context if relevant:",
        "zinghr_punchin": f"Create a warm, friendly punch-in message for {user_name}. Add motivation for the day:",
        "zinghr_punchout": f"Create a warm punch-out message for {user_name}. Ask about their day and wish them well:",
        "zinghr_leave": f"Create a friendly leave application confirmation for {user_name}:",
        "general": f"Respond to {user_name} in a friendly, conversational way. Be helpful and warm:"
    }

    prompt = prompts.get(context_type, prompts["general"])

    try:
        full_prompt = f"""
You are a friendly personal assistant.

{prompt}

Data:
{raw_data}
"""

        response = model.generate_content(full_prompt)

        return response.text

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return f"Hey {user_name}! Here's what I found: {raw_data}"


def chat_with_ai(user_message, user_name, chat_history):
    """General chat with memory"""

    try:
        history_text = ""

        for msg in chat_history[-5:]:
            history_text += f"""
User: {msg['message']}
Assistant: {msg['response']}
"""

        prompt = f"""
You are a friendly personal assistant talking to {user_name}.

Be warm, helpful and conversational.

Previous Conversation:
{history_text}

Current User Message:
{user_message}
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return f"GEMINI ERROR: {str(e)}"
    

def detect_intent(user_message):
        prompt = f"""You are an intent classifier for a personal assistant.
        Available intents: weather, news, stock, crypto, gold,punchin, punchout, leave, general, reminder, note, todo, chat.
        Rules
        - Reply ONLY with the intent name.
        - Do not add any extra text or explanation.
        - No markdown.
        - One word only.
        Examples:
        'Will it rain today?'
        weather
        'How is Bitcoin doing?'
        crypto
        'Clock me out'
        punchout
        'Tell me a joke'
        Chat
        User Message:
        {user_message}
        """
        
        try:
            response = model.generate_content(prompt)
            intent = response.text.strip().lower()
            print(f"INTENT DETECTED: {intent}")
            return intent
        
        except Exception as e:
            print(f"GEMINI ERROR: {e}")
            return "chat"


def extract_preferences(message):
        prompt = f"""
        You are extracting user preferences.
        Return ONLY valid JSON.
        Schema:
        {{
        "profession": null,
        "city": null,
        "work_start": null,
        "interests": null,
        "stocks": null,
        "crypto": null,
        "daily_briefing": null
        }}

        Examples:
        "I work in recruitment and follow AI news"
        {{
        "profession":"Recruitment",
        "city":null,
        "work_start":null,
        "interests":"AI",
        "stocks":null,
        "crypto":null,
        "daily_briefing":null
        }}

        User Message:
        {message}
        """

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace(       "```json", "").replace("```", "").strip()

                return json.loads(text)
        except Exception as e:
                print(f"PREFERENCE ERROR: {e}")
                return None



    
        


        

        



        


        