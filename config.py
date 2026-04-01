import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

def validate_config():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY topilmadi")
    print(f"✅ Model: {MODEL_NAME}")
    return True

validate_config()