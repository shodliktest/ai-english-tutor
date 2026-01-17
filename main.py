import streamlit as st
import sys
import os

# 'bot' papkasini Python qidiruv yo'liga qo'shamiz
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

# Streamlit sahifa sozlamalari
st.set_page_config(page_title="AI English Tutor", page_icon="🇬🇧")
st.title("🤖 AI English Tutor Control Panel")

try:
    # Bot papkasi ichidagi main.py dan ishga tushirish funksiyasini olamiz
    from bot.main import run_streamlit_bot
    run_streamlit_bot()
    st.success("Bot tizimi faol! ✅")
except Exception as e:
    st.error(f"Xatolik yuz berdi: {e}")
  
