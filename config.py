import streamlit as st

# 1. TOKENLARNI STREAMLIT SECRETS ORQALI OLISH
# Streamlit Cloud panelida 'Settings -> Secrets' bo'limiga BOT_TOKEN qo'shilgan bo'lishi shart.
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except (KeyError, FileNotFoundError):
    # Lokal testlar uchun placeholder
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# 2. ADMIN VA BAZA SOZLAMALARI
ADMIN_ID = 1416457518
DB_FILE = "bot_database.db"

# 3. OVOZLAR BAZASI (edge-tts modellaridan foydalaniladi)
# Har bir til uchun Erkak va Ayol ovozlari sozlangan.
VOICES = {
    "multi": {
        "label": "🌐 Ko'p tilli (Smart Mix) ➡️",
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
    "ar": {
        "label": "🇸🇦 Arabcha",
        "voices": {
            "female_1": {"id": "ar-SA-ZariyahNeural", "name": "Zariyah", "gender": "Ayol"},
            "male_1": {"id": "ar-SA-HamedNeural", "name": "Hamed", "gender": "Erkak"},
        },
        "test_text": "هذا تسجيل صوتي تجريبي للغة العربية"
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
