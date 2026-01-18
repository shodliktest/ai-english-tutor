import streamlit as st

# Streamlit Secrets-dan ma'lumotlarni xavfsiz o'qish
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    # Lokal testlar uchun (agar secrets topilmasa)
    BOT_TOKEN = "TOKEN_YOKI_XATOLIK"
    GROQ_API_KEY = "KALIT_YOKI_XATOLIK"

ADMIN_ID = 1416457518
DB_FILE = "bot_database.db"

# Ovozlar bazasi (Multi-lang uchun maxsus bo'lim)
VOICES = {
    "multi": {
        "label": "🌐 Ko'p tilli (Aqlli Mix) ➡️",
        "voices": {
            "female_1": {"id": "uz-UZ-MadinaNeural", "name": "Madina & Aria (Mix)", "gender": "Ayol"},
            "male_1": {"id": "uz-UZ-SardorNeural", "name": "Sardor & Christopher (Mix)", "gender": "Erkak"},
        }
    },
    "uz": {
        "label": "🇺🇿 O'zbekcha",
        "voices": {
            "female_1": {"id": "uz-UZ-MadinaNeural", "name": "Madina", "gender": "Ayol"},
            "male_1": {"id": "uz-UZ-SardorNeural", "name": "Sardor", "gender": "Erkak"},
        },
        "test_text": "Bu o'zbek tili uchun sinov audiosi."
    },
    "en": {
        "label": "🇺🇸 English",
        "voices": {
            "female_1": {"id": "en-US-AriaNeural", "name": "Aria", "gender": "Ayol"},
            "male_1": {"id": "en-US-ChristopherNeural", "name": "Christopher", "gender": "Erkak"},
        },
        "test_text": "This is a test audio for English."
    },
    "ru": {
        "label": "🇷🇺 Русский",
        "voices": {
            "female_1": {"id": "ru-RU-SvetlanaNeural", "name": "Светлана", "gender": "Ayol"},
            "male_1": {"id": "ru-RU-DmitryNeural", "name": "Дмитрий", "gender": "Erkak"},
        },
        "test_text": "Это тестовое аудио для русского языка."
    }
}
