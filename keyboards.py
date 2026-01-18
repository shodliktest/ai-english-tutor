from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, VOICES

def main_menu(user_id):
    kb = [
        [KeyboardButton(text="📝 Matn yuborish"), KeyboardButton(text="ℹ️ Yordam")],
        [KeyboardButton(text="📞 Bog'lanish")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="🔐 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_menu():
    kb = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👥 Foydalanuvchilar")],
        [KeyboardButton(text="🔙 Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def lang_inline_kb():
    # Til tanlash
    kb = []
    row = []
    for code, info in VOICES.items():
        row.append(InlineKeyboardButton(text=info['label'], callback_data=f"lang_{code}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

def voices_inline_kb(lang_code):
    # Tanlangan til ichidagi ovozlarni ko'rsatish
    kb = []
    # 1. Sinov rejimi tugmasi
    kb.append([InlineKeyboardButton(text="🔊 SINOV REJIMI (Barchasini eshitish)", callback_data=f"test_{lang_code}")])
    
    # 2. Ovozlar ro'yxati
    voices = VOICES[lang_code]['voices']
    for v_key, v_val in voices.items():
        kb.append([InlineKeyboardButton(text=f"{v_val['name']}", callback_data=f"voice_{lang_code}_{v_key}")])
    
    kb.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_lang")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
