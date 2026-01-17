import asyncio
import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from groq import Groq
import threading
import logging

# Loglarni Streamlit konsolida ko'rish uchun sozlash
logging.basicConfig(level=logging.INFO)

# 1. Secrets tekshiruvi
if "BOT_TOKEN" not in st.secrets:
    st.error("BOT_TOKEN topilmadi! Settings > Secrets qismini tekshiring.")
    st.stop()

BOT_TOKEN = st.secrets["BOT_TOKEN"]
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# 2. Bot obyektlarini yaratish
# Proxy yoki ulanish xatolarini oldini olish uchun
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    logging.info(f"Start buyrug'i keldi: {message.from_user.id}")
    await message.answer("Salom! Men ishlayapman. Gapingizni yuboring.")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if not client:
        await message.answer("Groq API kaliti kiritilmagan.")
        return
        
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Correct this: {message.text}"}],
            model="llama3-8b-8192",
        )
        await message.answer(completion.choices[0].message.content)
    except Exception as e:
        logging.error(f"AI xatosi: {e}")
        await message.answer("AI hozircha javob bera olmaydi.")

# --- ISHGA TUSHIRISH ---

async def start_polling():
    try:
        # Avvalgi eski sessiyalarni tozalash
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Bot polling boshlandi...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Botni yurgizishda xatolik: {e}")

def run_bot():
    if "bot_thread" not in st.session_state:
        loop = asyncio.new_event_loop()
        def target():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_polling())
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        st.session_state.bot_thread = thread
        st.write("✅ Bot oqimi yaratildi.")

# UI
st.title("Bot Control Panel")
run_bot()

# Bot haqida ma'lumot chiqarish (Tekshirish uchun)
async def get_bot_info():
    info = await bot.get_me()
    return info.username

if st.button("Bot holatini tekshirish"):
    try:
        loop = asyncio.new_event_loop()
        name = loop.run_until_complete(get_bot_info())
        st.success(f"Bot ulandi: @{name}")
    except Exception as e:
        st.error(f"Bot ulanmadi: {e}")
    
