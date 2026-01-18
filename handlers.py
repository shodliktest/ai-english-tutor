import os
import tempfile
from datetime import datetime
from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, VOICES
from database import add_user, update_stats, get_stats, get_all_users
from keyboards import main_menu, admin_menu, lang_inline_kb, voices_inline_kb
from utils import read_pdf, read_docx, read_txt, translate_text, generate_audio

router = Router()

class TTSState(StatesGroup):
    processing_text = State()

# --- START & MENU ---
@router.message(Command("start"))
async def start_handler(message: types.Message, bot: Bot):
    user = message.from_user
    is_new, date_joined = add_user(user.id, user.username, user.full_name)
    welcome_text = (f"Assalomu alaykum, <b>{user.full_name}</b>!\n"
                    "Ovozli yordamchiga xush kelibsiz. Matn yoki fayl yuboring.")
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu(user.id))
    
    if is_new:
        try:
            await bot.send_message(ADMIN_ID, f"🆕 Yangi user: {user.full_name} (@{user.username})")
        except: pass

@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: types.Message):
    await message.answer("Matn yozing yoki fayl tashlang. Men uni o'qib beraman.")

# --- ADMIN PANEL ---
@router.message(F.text == "🔐 Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz", reply_markup=admin_menu())

@router.message(F.text == "📊 Statistika")
async def stats_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total, today, usage = get_stats()
        await message.answer(f"📊 Jami user: {total}\n📅 Bugun: {today}\n🎧 Audio: {usage}")

@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        users = get_all_users()
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt") as temp:
            for u in users: temp.write(f"{u}\n")
            temp_path = temp.name
        await message.answer_document(FSInputFile(temp_path))
        os.remove(temp_path)

@router.message(F.text == "🔙 Bosh menyu")
async def back_home(message: types.Message):
    await message.answer("Asosiy menyu", reply_markup=main_menu(message.from_user.id))

# --- CONTENT HANDLER (TEXT/FILES) ---
@router.message(F.content_type.in_({'text', 'document'}))
async def content_handler(message: types.Message, state: FSMContext, bot: Bot):
    if message.text and message.text.startswith(("🔐", "📊", "👥", "🔙")): return

    msg = await message.answer("⏳ Matn o'qilmoqda...")
    text_to_process = ""

    if message.document:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            await bot.download_file(file.file_path, temp_file.name)
            temp_path = temp_file.name
        
        ext = message.document.file_name.split('.')[-1].lower()
        if ext == 'pdf': text_to_process = read_pdf(temp_path)
        elif ext == 'docx': text_to_process = read_docx(temp_path)
        elif ext == 'txt': text_to_process = read_txt(temp_path)
        os.remove(temp_path)
    else:
        text_to_process = message.text

    if not text_to_process or len(text_to_process) < 2:
        await msg.edit_text("❌ Matn topilmadi.")
        return

    await state.update_data(text=text_to_process)
    await msg.edit_text("🌍 Qaysi tilda o'qish kerak?", reply_markup=lang_inline_kb())
    try: await message.delete() 
    except: pass

# --- CALLBACKS ---
@router.callback_query(F.data.startswith("lang_"))
async def lang_selected(callback: types.CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    await state.update_data(lang_code=lang_code)
    await callback.message.edit_text("🗣 Ovoz turini tanlang yoki 'Sinov Rejimi'ni bosing:", 
                                     reply_markup=voices_inline_kb(lang_code))

@router.callback_query(F.data == "back_to_lang")
async def back_to_lang(callback: types.CallbackQuery):
    await callback.message.edit_text("🌍 Qaysi tilda o'qish kerak?", reply_markup=lang_inline_kb())

# --- SINOV REJIMI (TEST MODE) ---
@router.callback_query(F.data.startswith("test_"))
async def test_mode_handler(callback: types.CallbackQuery, bot: Bot):
    lang_code = callback.data.split("_")[1]
    test_text = VOICES[lang_code]['test_text']
    voices_list = VOICES[lang_code]['voices']
    
    await callback.message.edit_text(f"⏳ <b>Sinov rejimi ishga tushdi...</b>\nJami {len(voices_list)} ta ovoz tayyorlanmoqda.", parse_mode="HTML")
    
    for v_key, v_val in voices_list.items():
        output_file = f"test_{v_key}_{callback.from_user.id}.mp3"
        await generate_audio(test_text, v_val['id'], output_file)
        
        caption = (f"🔍 <b>SINOV REJIMI</b>\n"
                   f"👤 Ovoz: {v_val['name']}\n"
                   f"🗣 Turi: {v_val['gender']}")
        
        await bot.send_audio(callback.message.chat.id, FSInputFile(output_file), caption=caption, parse_mode="HTML")
        os.remove(output_file)
    
    await callback.message.answer("Sinov tugadi. Endi haqiqiy matn uchun ovoz tanlang:", reply_markup=voices_inline_kb(lang_code))

# --- FINAL AUDIO GENERATION ---
@router.callback_query(F.data.startswith("voice_"))
async def voice_selected(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split("_")
    lang_code = parts[1]
    voice_key = parts[2]  # male_1, female_1 va hokazo
    
    voice_info = VOICES[lang_code]['voices'][voice_key]
    voice_id = voice_info['id']
    
    data = await state.get_data()
    original_text = data.get("text", "")
    
    msg = callback.message
    await msg.edit_text("🔄 Tarjima qilinmoqda (agar kerak bo'lsa)...")
    
    translated_text = await translate_text(original_text, lang_code)
    
    await msg.edit_text(f"🎙 <b>{voice_info['name']}</b> ovozida yozilmoqda... (Progress: 50%)", parse_mode="HTML")
    
    output_file = f"audio_{callback.from_user.id}.mp3"
    try:
        await generate_audio(translated_text, voice_id, output_file)
        
        await msg.edit_text("📤 Yuklanmoqda... (90%)")
        
        caption = (f"🎧 <b>Audio Tayyor!</b>\n\n"
                   f"🗣 Til: {VOICES[lang_code]['label']}\n"
                   f"👤 Ovoz: {voice_info['name']} ({voice_info['gender']})\n"
                   f"🤖 Bot: @{(await bot.get_me()).username}")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="♻️ Ulashish", url="https://t.me/share/url?url=Zo'r bot ekan")]])
        
        await bot.send_audio(msg.chat.id, FSInputFile(output_file), caption=caption, parse_mode="HTML", reply_markup=kb)
        update_stats()
        
    except Exception as e:
        await msg.edit_text(f"Xatolik: {e}")
    finally:
        if os.path.exists(output_file): os.remove(output_file)
        await msg.delete()
        await state.clear()
