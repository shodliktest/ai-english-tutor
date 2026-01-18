import asyncio
import logging
import sys
import streamlit as st
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DB_FILE
from database import init_db
from handlers import router

async def main():
    # Bazani yaratish
    init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Routerni ulash
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Streamlit orqali Web Interfeys (Serverni tirik saqlash uchun)
    st.set_page_config(page_title="Multi-Voice Bot", page_icon="🎙")
    st.title("🎙 Telegram TTS Bot")
    st.write("Bot ishlamoqda...")
    
    if st.button("Bot Status"):
        st.write("Active ✅")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
