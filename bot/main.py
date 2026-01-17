import asyncio
import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from groq import Groq
import threading

# 1. Streamlit Secrets-dan ma'lumotlarni olish
# (Bular Streamlit Dashboard -> Settings -> Secrets qismida bo'lishi shart)
if "BOT_TOKEN" not in st.secrets or "GROQ_API_KEY" not in st.secrets:
    st.error("Xatolik: Secrets (BOT_TOKEN yoki GROQ_API_KEY) topilmadi!")
    st.stop()

BOT_TOKEN = st.secrets["BOT_TOKEN"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# 2. Bot va AI obyektlarini sozlash
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY)

# --- BOT HANDLERLARI (Logikasi) ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Salom {message.from_user.first_name}! 👋\n"
        "Men sizning AI ingliz tili repetitoringizman. "
        "Menga istalgan inglizcha gap yuboring, men xatolaringizni tuzatib beraman!"
    )

@dp.message(F.text)
async def handle_ai(message: types.Message):
    # AI uchun topshiriq (Prompt)
    prompt = f"Correct this English sentence and explain mistakes in Uzbek: '{message.text}'"
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        ai_javobi = completion.choices[0].message.content
        await message.answer(ai_javobi)
    except Exception as e:
        await message.answer("⚠️ AI bilan bog'lanishda xatolik yuz berdi.")
        st.error(f"Groq API Error: {e}")

# --- BOTNI STREAMLIT-DA FONDA ISHLATISH ---

async def start_bot_polling():
    # Eski kutilib qolgan xabarlarni o'chirish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def run_bot_in_background():
    """Botni alohida thread-da (oqimda) yurgizish"""
    if "bot_is_running" not in st.session_state:
        loop = asyncio.new_event_loop()
        def target():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_bot_polling())
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        st.session_state.bot_is_running = True

# --- STREAMLIT INTERFEYSI (Web sahifa) ---

st.set_page_config(page_title="AI Tutor Bot Control", page_icon="🇬🇧")
st.title("🤖 AI English Tutor Bot")
st.subheader("Bot holati: Ishlamoqda ✅")

# Botni fonda ishga tushiruvchi funksiyani chaqiramiz
run_bot_in_background()

st.info("Bot hozirda Telegramda faol. Foydalanuvchilar bilan muloqot qilishingiz mumkin.")
st.write("---")
st.write("Dasturchi uchun eslatma: Ushbu sahifa botni fonda ushlab turish uchun xizmat qiladi.")
