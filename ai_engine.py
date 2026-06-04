import google.generativeai as genai
import json
import traceback
from config import GEMINI_API_KEY

print("GEMINI KEY EXISTS:", bool(GEMINI_API_KEY))
print("GEMINI KEY LENGTH:", len(GEMINI_API_KEY) if GEMINI_API_KEY else 0)

genai.configure(api_key=GEMINI_API_KEY)

# Use whichever model is working in your project
model = genai.GenerativeModel("gemini-3.5-flash")


def clean_response(raw_data, context_type, user_name=""):
    """Polish external API responses"""

    prompts = {
        "weather": f"Make this weather data friendly and personal for {user_name}. Add emojis and advice:",
        "news": f"Summarize this news for {user_name} in a conversational and engaging way. Add context and emojis:",
        "stock": f"Make this stock data exciting and personal for {user_name}. Add insights and emojis:",
        "crypto": f"Make this crypto update engaging for {user_name}. Add market insights and emojis:",
        "gold": f"Make this gold rate update friendly for {user_name}. Add investment context if relevant:",
        "zinghr_punchin": f"Create a warm punch-in message for {user_name}. Add motivation for the day:",
        "zinghr_punchout": f"Create a warm punch-out message for {user_name}. Ask about their day and wish them well:",
        "zinghr_leave": f"Create a friendly leave confirmation for {user_name}:",
        "general": f"Respond to {user_name} in a friendly and helpful way:"
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
        return f"Hey {user_name}! Here's what I found:\n\n{raw_data}"


def chat_with_ai(user_message, user_name, chat_history):
    """General conversation with memory"""

    try:
        history_text = ""

        for msg in chat_history[-5:]:
            history_text += f"""
User: {msg['message']}
Assistant: {msg['response']}
"""

        prompt = f"""
You are Jarvis, a friendly personal AI assistant.

You are talking to {user_name}.

Be conversational, warm, intelligent and concise.

Previous Conversation:
{history_text}

Current User Message:
{user_message}
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        traceback.print_exc()
        return f"Sorry {user_name}, I'm having trouble thinking right now. Please try again."


def detect_intent(user_message):
    """Classify user intent"""

    prompt = f"""
You are an intent classifier for a Personal AI Assistant.

Available intents:

weather
news
stock
crypto
gold

punchin
punchout
leave

todo_add
todo_list
todo_complete
todo_delete

meeting_add
meeting_list

reminder_add
reminder_list

note_add
note_list

chat

Examples:

"Will it rain today?"
weather

"Show me AI news"
news

"I need to update Wisestep docs tomorrow"
todo_add

"Add follow up with client to my tasks"
todo_add

"What are my pending tasks?"
todo_list

"Show my todos"
todo_list

"I completed Wisestep documentation"
todo_complete

"Remove follow up with client"
todo_delete

"I have a meeting with my manager tomorrow at 2 PM"
meeting_add

"What meetings do I have?"
meeting_list

"Remind me to submit appraisal next week"
reminder_add

"What reminders do I have?"
reminder_list

"Save this note: client prefers remote hiring"
note_add

"Show my notes"
note_list

Rules:
- Return ONLY one intent.
- No explanation.
- No markdown.
- No punctuation.
- Output must exactly match one of the intent names above.

User Message:
{user_message}
"""

    try:
        print("CALLING GEMINI FOR INTENT")

        response = model.generate_content(prompt)

        print("INTENT RESPONSE RECEIVED")

        intent = response.text.strip().lower()

        print(f"INTENT DETECTED: {intent}")

        return intent

    except Exception as e:
        print(f"INTENT ERROR: {e}")
        traceback.print_exc()

        return "chat"
    

def extract_task_info(user_message):

    prompt = f"""
Extract task information.

Return ONLY valid JSON.

Schema:

{{
    "task": "",
    "due_date": ""
}}

Examples:

Message:
I need to update Wisestep docs tomorrow

Response:
{{
    "task": "Update Wisestep docs",
    "due_date": "tomorrow"
}}

Message:
Follow up with client next week

Response:
{{
    "task": "Follow up with client",
    "due_date": "next week"
}}

Message:
{user_message}
"""

    try:

        response = model.generate_content(prompt)

        text = response.text.strip()

        if "```json" in text:
            text = text.replace("```json", "").replace("```", "").strip()

        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)

        print(f"TASK INFO: {result}")

        return result

    except Exception as e:

        print(f"TASK EXTRACTION ERROR: {e}")

        return None


def extract_preferences(message):
    """Extract user preferences from normal conversation"""

    prompt = f"""
Extract user preferences.

Return ONLY valid JSON.

Do not use markdown.
Do not explain anything.

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

Message:
I work in recruitment and follow AI news.

Response:
{{
    "profession":"Recruitment",
    "city":null,
    "work_start":null,
    "interests":"AI",
    "stocks":null,
    "crypto":null,
    "daily_briefing":null
}}

Message:
{message}
"""

    try:
        print("CALLING GEMINI FOR PREFERENCES")
        response = model.generate_content(prompt)
        print("PREFERENCE RESPONSE RECEIVED")

        text = response.text.strip()

        print(f"GEMINI RESPONSE: {text}")

        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()

        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)

        print(f"PARSED PREFS: {result}")

        return result

    except Exception as e:

        print(f"PREFERENCE ERROR: {e}")
        traceback.print_exc()

        try:
            print(f"RAW RESPONSE: {response.text}")
        except:
            pass

        return None
    

