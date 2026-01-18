from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, VOICES

def main_menu(user_id):
    """Asosiy menyu tugmalari"""
    kb = [
        [KeyboardButton(text="📝 Matn yuborish"), KeyboardButton(text="ℹ️ Yordam")],
        [KeyboardButton(text="📞 Bog'lanish")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="🔐 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_menu():
    """Admin boshqaruv paneli tugmalari"""
    kb = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Xabar yuborish")],
        [KeyboardButton(text="🔙 Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def lang_inline_kb():
    """Tillar va rejimlarni tanlash menyusi"""
    kb = []
    
    # 1. Ko'p tilli rejim (Mix matnlar uchun) eng tepada
    kb.append([InlineKeyboardButton(text="🌐 Ko'p tilli (Uzbek + English) ➡️", callback_data="lang_multi")])
    
    # 2. Oddiy tillar ro'yxatini chiqarish
    row = []
    for code, info in VOICES.items():
        if code == "multi":
            continue # Multi tepada alohida chiqdi, bu yerda takrorlanmasin
            
        row.append(InlineKeyboardButton(text=info['label'], callback_data=f"lang_{code}"))
        
        # Har 2 ta tilni bitta qatorga joylash
        if len(row) == 2:
            kb.append(row)
            row = []
            
    # Agar oxirida 1 ta til qolib ketgan bo'lsa, uni ham qo'shish
    if row:
        kb.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

def voices_inline_kb(lang_code):
    """Tanlangan til uchun ovoz modellarini ko'rsatish"""
    kb = []
    
    # Tanlangan tilga tegishli ovozlarni olish
    if lang_code in VOICES:
        voices = VOICES[lang_code]['voices']
        for v_key, v_val in voices.items():
            # Ovoz nomi va jinsini ko'rsatish
            gender_icon = "👩‍💼" if v_val.get('gender') == "Ayol" else "👨‍💼"
            kb.append([InlineKeyboardButton(
                text=f"{gender_icon} {v_val['name']}", 
                callback_data=f"voice_{lang_code}_{v_key}"
            )])
    
    # 3. Sinov rejimi (Barcha ovozlarni eshitib ko'rish)
    kb.append([InlineKeyboardButton(text="🔊 SINOV REJIMI", callback_data=f"test_{lang_code}")])
    
    # 4. Ortga qaytish tugmasi
    kb.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_lang")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)
