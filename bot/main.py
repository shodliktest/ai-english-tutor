import asyncio
import logging
import json
import sqlite3
import threading
import re
import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq

# --- 1. SOZLAMALAR VA LOGGING ---
logging.basicConfig(level=logging.INFO)

# Secrets tekshiruvi
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Secrets (BOT_TOKEN yoki GROQ_API_KEY) topilmadi! .streamlit/secrets.toml ni tekshiring.")
    st.stop()

# --- 2. DATABASE (SQLite) ---
DB_NAME = "english_tutor.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            level TEXT DEFAULT 'A1',
            xp INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

db_conn = init_db()

def get_user(user_id):
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def register_user(user_id, full_name):
    if not get_user(user_id):
        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
        db_conn.commit()

def update_xp(user_id, points):
    cursor = db_conn.cursor()
    cursor.execute("UPDATE users SET xp = xp + ? WHERE user_id = ?", (points, user_id))
    db_conn.commit()

def get_xp(user_id):
    user = get_user(user_id)
    return user[3] if user else 0

# --- 3. AI ENGINE (GROQ - ROBUST VERSIYA) ---
client = Groq(api_key=GROQ_API_KEY)

def clean_json_string(json_string):
    """
    MUHIM: AI javobidan faqat JSON qismini ajratib oladi.
    Markdown (```json ... ```) va ortiqcha gaplarni olib tashlaydi.
    """
    try:
        # Markdown belgilarini tozalash
        json_string = json_string.replace("```json", "").replace("```", "").strip()
        
        # Birinchi '{' va oxirgi '}' ni topish
        start = json_string.find('{')
        end = json_string.rfind('}') + 1
        
        if start != -1 and end != -1:
            return json_string[start:end]
        return json_string
    except Exception as e:
        logging.error(f"JSON Cleaning Error: {e}")
        return json_string

async def get_ai_explanation(topic, level):
    prompt = f"""
    You are an expert English teacher. Explain '{topic}' to a student (Level: {level}).
    Structure:
    1. Definition (Uzbek)
    2. Formula (+ / - / ?)
    3. Real example with translation.
    Response MUST be in Uzbek. Keep it short and engaging with emojis.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192", # Kichikroq model barqarorroq ishlaydi
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Explanation API Error: {e}")
        return "⚠️ AI hozir band. Iltimos, birozdan so'ng urinib ko'ring."

async def generate_quiz_question(topic, level):
    prompt = f"""
    Create a multiple-choice question for English topic '{topic}' (Level: {level}).
    Return ONLY valid JSON format like this:
    {{
        "question": "Sentence with a gap",
        "options": ["A", "B", "C", "D"],
        "correct_option_index": 0,
        "explanation": "Explanation in Uzbek"
    }}
    IMPORTANT: Return ONLY the JSON object. Do not write "Here is the json".
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a backend API that outputs strictly JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.3 # Pastroq harorat aniqroq JSON beradi
        )
        content = response.choices[0].message.content
        logging.info(f"AI Raw Response: {content}") 
        
        # JSONni tozalash va o'qish
        clean_content = clean_json_string(content)
        return json.loads(clean_content)
        
    except json.JSONDecodeError:
        logging.error("JSON Decode Error: AI buzuq format yubordi")
        return None
    except Exception as e:
        logging.error(f"API Error: {e}")
        return None

# --- 4. BOT STATES & LOGIC ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class TutorStates(StatesGroup):
    choosing_topic = State()
    learning = State()
    quiz = State()

# --- KLAVIATURALAR ---
def main_menu_kb():
    kb = [
        [InlineKeyboardButton(text="🕒 Present Simple", callback_data="topic:Present Simple")],
        [InlineKeyboardButton(text="🏃 Present Continuous", callback_data="topic:Present Continuous")],
        [InlineKeyboardButton(text="✅ Present Perfect", callback_data="topic:Present Perfect")],
        [InlineKeyboardButton(text="📊 Mening Natijalarim", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def quiz_control_kb():
    kb = [
        [InlineKeyboardButton(text="🧪 Test ishlash", callback_data="start_quiz")],
        [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def options_kb(options):
    kb = []
    for i, opt in enumerate(options):
        kb.append([InlineKeyboardButton(text=opt, callback_data=f"ans:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    register_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        f"Salom, {message.from_user.first_name}! 👋\n\n"
        "Men **AI English Tutor**man. Ingliz tili zamonlarini 0 dan o'rgataman.\n"
        "Qaysi mavzudan boshlaymiz?",
        reply_markup=main_menu_kb()
    )

@dp.callback_query(F.data == "menu")
async def back_to_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Asosiy menyu:", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    xp = get_xp(call.from_user.id)
    await call.answer(f"Sizning hisobingiz: {xp} XP ⭐️", show_alert=True)

# 1. Mavzu tanlash
@dp.callback_query(F.data.startswith("topic:"))
async def topic_selected(call: types.CallbackQuery, state: FSMContext):
    topic = call.data.split(":")[1]
    user = get_user(call.from_user.id)
    level = user[2]
    
    await call.message.edit_text(f"🤖 **{topic}** tahlil qilinmoqda...")
    explanation = await get_ai_explanation(topic, level)
    
    await state.update_data(current_topic=topic, level=level)
    await state.set_state(TutorStates.learning)
    
    await call.message.edit_text(
        explanation, 
        reply_markup=quiz_control_kb(), 
        parse_mode="Markdown"
    )

# 2. Test generatsiya
@dp.callback_query(F.data == "start_quiz")
async def start_quiz(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic = data.get("current_topic")
    level = data.get("level")
    
    await call.message.edit_text("🧠 AI yangi test tuzmoqda... (Kuting)")
    
    quiz_data = await generate_quiz_question(topic, level)
    
    if not quiz_data:
        # Xatolik bo'lsa bot "qulab tushmaydi", shunchaki xabar beradi
        await call.message.edit_text(
            "⚠️ AI test tuza olmadi (Ehtimol API band). Qaytadan urinib ko'ring.", 
            reply_markup=quiz_control_kb()
        )
        return

    await state.update_data(correct_index=quiz_data['correct_option_index'], explanation=quiz_data['explanation'])
    await state.set_state(TutorStates.quiz)
    
    question_text = f"📝 **Test: {topic}**\n\n{quiz_data['question']}"
    await call.message.edit_text(question_text, reply_markup=options_kb(quiz_data['options']))

# 3. Javobni tekshirish
@dp.callback_query(F.data.startswith("ans:"), TutorStates.quiz)
async def check_answer(call: types.CallbackQuery, state: FSMContext):
    try:
        user_idx = int(call.data.split(":")[1])
        data = await state.get_data()
        correct_idx = data.get("correct_index")
        explanation = data.get("explanation")
        
        if user_idx == correct_idx:
            update_xp(call.from_user.id, 10)
            msg = f"✅ **To'g'ri!** (+10 XP)\n\n{explanation}"
        else:
            msg = f"❌ **Xato.**\n\n{explanation}"
        
        kb = [
            [InlineKeyboardButton(text="➡️ Keyingi savol", callback_data="start_quiz")],
            [InlineKeyboardButton(text="🏠 Menyu", callback_data="menu")]
        ]
        await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Answer Check Error: {e}")
        await call.message.edit_text("Xatolik yuz berdi. Menyu tugmasini bosing.", reply_markup=main_menu_kb())

# --- STARTUP ---
async def start_polling():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, handle_signals=False)

def run_bot():
    if "bot_runner" not in st.session_state:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=lambda: (asyncio.set_event_loop(loop), loop.run_until_complete(start_polling())), daemon=True)
        t.start()
        st.session_state.bot_runner = True

st.title("🇬🇧 AI English Tutor Admin")
st.write("Holati: **Ishlamoqda** 🟢")
st.write("Agat 'ModuleNotFoundError' chiqsa, 'Reboot App' qiling.")
run_bot()
