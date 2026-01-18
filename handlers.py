import os
import tempfile
import asyncio
import re
import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

# Loyihangiz modullari - config, database, keyboards va utils fayllaridan import
from config import ADMIN_ID, VOICES
from database import add_user, update_stats, get_stats, get_all_users
from keyboards import main_menu, admin_menu, lang_inline_kb, voices_inline_kb
from utils import read_pdf, read_docx, read_txt, translate_text, generate_audio

router = Router()

# Botning holatlarini boshqarish (FSM)
class BotStates(StatesGroup):
    waiting_for_broadcast = State()
    processing_audio = State()

# --- 1. YORDAMCHI FUNKSIYALAR ---

def get_p_bar(percent):
    """
    Foydalanuvchiga jarayon holatini ko'rsatuvchi progress bar.
    Masalan: [▓▓▓░░░░░░░] 30%
    """
    filled = int(percent / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"<code>{bar}</code> {percent}%"

def detect_language_by_chars(text):
    """
    Matn ichidagi harflarni tahlil qilib tilni aniqlaydi.
    Unicode diapazonlari: Arab (0600-06FF), Kirill (Rus), Lotin (En).
    """
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'
    elif re.search(r'[а-яА-ЯёЁ]', text):
        return 'ru'
    elif re.search(r'[a-zA-Z]', text):
        return 'en'
    return 'en' # Agar aniqlanmasa default Ingliz tili

def split_text_by_pattern(text):
    """
    Matnni qavs mantiqi asosida bo'laklarga ajratadi:
    - Qavs ichidagilar -> Uzbek (uz)
    - Qavsdan tashqaridagilar -> Harfga qarab (en/ru/ar)
    """
    pattern = r'(\([^()]+\)|[^()]+)'
    parts = re.findall(pattern, text)
    segments = []
    for part in parts:
        clean_part = part.strip()
        if not clean_part:
            continue
            
        if clean_part.startswith("(") and clean_part.endswith(")"):
            # Qavslarni olib tashlab o'zbekcha deb belgilaymiz
            segments.append({'text': clean_part[1:-1].strip(), 'lang': 'uz'})
        else:
            # Qavsdan tashqaridagi qismning tilini harfidan aniqlaymiz
            lang = detect_language_by_chars(clean_part)
            segments.append({'text': clean_part, 'lang': lang})
    return segments

# --- 2. START VA ADMIN BOSHQARUV PANEL ---

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """Botga start berilganda foydalanuvchini ro'yxatga olish va kutib olish."""
    user = message.from_user
    add_user(user.id, user.username, user.full_name)
    welcome_text = (f"Assalomu alaykum, <b>{user.full_name}</b>!\n"
                    "Men darslik matnlarini professional audio qilib beruvchi botman.\n"
                    "Matn yuboring yoki fayl (PDF, Word, TXT) yuklang.\n\n"
                    "🤖 <b>Bot:</b> @TTSpro_robot")
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu(user.id))

@router.message(F.text == "🔐 Admin Panel")
async def admin_panel(message: types.Message):
    """Faqat admin ko'ra oladigan panel."""
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin boshqaruv paneli:", reply_markup=admin_menu())

@router.message(F.text == "📊 Statistika")
async def stats_view(message: types.Message):
    """Bot foydalanuvchilari va audiolar statistikasi."""
    if message.from_user.id == ADMIN_ID:
        t_users, d_usage, t_usage = get_stats()
        text = (f"📈 <b>Bot statistikasi:</b>\n\n"
                f"👥 Jami foydalanuvchilar: {t_users}\n"
                f"📅 Bugungi faollik: {d_usage}\n"
                f"🎙 Jami yaratilgan audiolar: {t_usage}")
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_request(message: types.Message, state: FSMContext):
    """Barcha foydalanuvchilarga xabar tarqatishni boshlash."""
    if message.from_user.id == ADMIN_ID:
        await message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (Matn, rasm yoki video):")
        await state.set_state(BotStates.waiting_for_broadcast)

@router.message(BotStates.waiting_for_broadcast)
async def perform_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    """Xabarni barcha foydalanuvchilarga nusxalash (Copy)."""
    users = get_all_users()
    count = 0
    status_msg = await message.answer(f"⏳ Yuborish boshlandi: 0/{len(users)}")
    
    for u_id in users:
        try:
            await bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
            if count % 10 == 0:
                await status_msg.edit_text(f"⏳ Yuborilmoqda: {count}/{len(users)}")
            await asyncio.sleep(0.05)
        except:
            pass
            
    await message.answer(f"✅ Xabar yuborish tugadi.\nJami yetkazildi: {count} ta foydalanuvchiga.")
    await state.clear()

# --- 3. MATN VA FAYLLRNI QABUL QILISH ---

@router.message(F.content_type.in_({'text', 'document'}))
async def content_handler(message: types.Message, state: FSMContext, bot: Bot):
    """Matn yoki hujjatni qabul qilib, undan matnni ajratib olish."""
    if message.text in ["🔐 Admin Panel", "📊 Statistika", "📢 Xabar yuborish", "🔙 Bosh menyu"]:
        return
    
    msg = await message.answer(f"⏳ Jarayon boshlanmoqda...\n{get_p_bar(10)}", parse_mode="HTML")
    text = ""

    if message.document:
        # Fayl hajmini tekshirish (20MB)
        if message.document.file_size > 20*1024*1024:
            await msg.edit_text("❌ Fayl juda katta. Limit: 20MB.")
            return

        file = await bot.get_file(message.document.file_id)
        await msg.edit_text(f"⏳ Fayl yuklanmoqda...\n{get_p_bar(40)}", parse_mode="HTML")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            await bot.download_file(file.file_path, tmp.name)
            await msg.edit_text(f"⏳ Matn ajratib olinmoqda...\n{get_p_bar(70)}", parse_mode="HTML")
            
            ext = message.document.file_name.split('.')[-1].lower()
            if ext == 'pdf': text = read_pdf(tmp.name)
            elif ext == 'docx': text = read_docx(tmp.name)
            elif ext == 'txt': text = read_txt(tmp.name)
            os.remove(tmp.name)
    else:
        text = message.text
        await msg.edit_text(f"⏳ Matn tahlil qilinmoqda...\n{get_p_bar(80)}", parse_mode="HTML")

    if not text or len(text.strip()) < 2:
        await msg.edit_text("❌ Xatolik: Matn topilmadi yoki juda qisqa.")
        return

    await msg.edit_text(f"✅ Tayyor!\n{get_p_bar(100)}", parse_mode="HTML")
    await asyncio.sleep(0.5)

    await state.update_data(text=text)
    await msg.edit_text("🌍 Kerakli tilni yoki <b>Mix Rejimni</b> tanlang:", 
                        parse_mode="HTML", reply_markup=lang_inline_kb())

# --- 4. AUDIO GENERATSIYA VA BIRLASHTIRISH ---

@router.callback_query(F.data.startswith("lang_"))
async def lang_choice(call: types.CallbackQuery, state: FSMContext):
    """Til tanlangandan so'ng ovoz modellarini (Erkak/Ayol) ko'rsatish."""
    lang = call.data.split("_")[1]
    await state.update_data(lang=lang)
    await call.message.edit_text("🗣 Ovoz turini tanlang:", reply_markup=voices_inline_kb(lang))

@router.callback_query(F.data.startswith("voice_"))
async def voice_choice(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Ovoz tanlangandan so'ng audio yaratish mantiqi."""
    parts = call.data.split("_", 2)
    lang_code, voice_key = parts[1], parts[2]
    
    data = await state.get_data()
    original_text = data.get("text", "")
    output_final = f"audio_{call.from_user.id}.mp3"
    
    try:
        # A) KO'P TILLI MIX REJIM
        if lang_code == "multi":
            segments = split_text_by_pattern(original_text)
            temp_files = []
            await call.message.edit_text(f"🌐 Ko'p tilli tahlil boshlandi...\n{get_p_bar(10)}", parse_mode="HTML")
            
            for i, seg in enumerate(segments):
                tmp_name = f"chunk_{i}_{call.from_user.id}.mp3"
                # Har bir bo'lak tilini aniqlab, mos ovoz bilan o'qitish
                target_lang = seg['lang'] if seg['lang'] in VOICES else 'uz'
                v_id = VOICES[target_lang]['voices'][voice_key]['id']
                
                await generate_audio(seg['text'], v_id, tmp_name)
                temp_files.append(tmp_name)
                
                prog = 10 + int((i+1)/len(segments) * 80)
                await call.message.edit_text(f"🎙 Audio yozilmoqda ({i+1}/{len(segments)})...\n{get_p_bar(prog)}", parse_mode="HTML")

            # Bo'laklarni bitta MP3 faylga birlashtirish
            with open(output_final, "wb") as outfile:
                for f in temp_files:
                    with open(f, "rb") as infile: outfile.write(infile.read())
                    os.remove(f)
            rejim_label = "Ko'p tilli (Smart Mix)"
            
        # B) STANDART TARJIMA REJIMI
        else:
            await call.message.edit_text(f"🌍 Tarjima qilinmoqda...\n{get_p_bar(40)}", parse_mode="HTML")
            final_text = await translate_text(original_text, lang_code)
            
            await call.message.edit_text(f"🎙 Audio yozilmoqda...\n{get_p_bar(70)}", parse_mode="HTML")
            v_id = VOICES[lang_code]['voices'][voice_key]['id']
            await generate_audio(final_text, v_id, output_final)
            rejim_label = f"Tarjima ({lang_code})"

        # --- YUKLASH VA YAKUNIY IMZO ---
        await call.message.edit_text(f"📤 Telegramga yuklanmoqda...\n{get_p_bar(95)}", parse_mode="HTML")
        
        # Siz so'ragan imzo tartibi:
        voice_name = VOICES[lang_code if lang_code!='multi' else 'uz']['voices'][voice_key]['name']
        caption = (f"✅ <b>Audio Tayyor!</b>\n\n"
                   f"🎙 Ovoz: {voice_name}\n"
                   f"🤖 <b>Bot:</b> @TTSpro_robot\n"
                   f"⚙️ Rejim: {rejim_label}")
        
        await bot.send_audio(call.message.chat.id, FSInputFile(output_final), caption=caption, parse_mode="HTML")
        update_stats()
        
    except Exception as e:
        await call.message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    finally:
        if os.path.exists(output_final): os.remove(output_final)
        await call.message.delete()
        await state.clear()

# --- 5. NAVIGATSIYA VA QAYTA ISHLASH ---

@router.callback_query(F.data == "back_to_lang")
async def back_to_lang(call: types.CallbackQuery):
    """Ovoz tanlashdan til tanlashga qaytish."""
    await call.message.edit_text("🌍 Tilni yoki rejimni tanlang:", reply_markup=lang_inline_kb())

@router.message(F.text == "🔙 Bosh menyu")
async def back_to_main(message: types.Message):
    """Bosh menyuga qaytish."""
    await message.answer("Asosiy menyu", reply_markup=main_menu(message.from_user.id))
