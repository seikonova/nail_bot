from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💅 Записаться"),
            KeyboardButton(text="📋 Мои записи")
        ],
        [
            KeyboardButton(text="💰 Услуги и цены"),
            KeyboardButton(text="📍 Адрес")
        ],
        [
            KeyboardButton(text="☎️ Связаться с мастером")
        ]
    ],
    resize_keyboard=True
)