from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


# ==================================================
# ДАТЫ
# ==================================================

def dates_keyboard(dates):

    builder = InlineKeyboardBuilder()

    for date in dates:

        builder.button(
            text=f"📅 {date}",
            callback_data=f"client:date:{date}"
        )

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="client:close"
        )
    )

    return builder.as_markup()


# ==================================================
# ВРЕМЯ
# ==================================================

def times_keyboard(slots):

    builder = InlineKeyboardBuilder()

    for slot_id, date, time, available in slots:

        builder.button(
            text=f"🕐 {time}",
            callback_data=f"client:slot:{slot_id}"
        )

    builder.adjust(3)

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="client:dates"
        )
    )

    return builder.as_markup()


# ==================================================
# ПОДТВЕРЖДЕНИЕ
# ==================================================

def confirm_booking_keyboard(slot_id):

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтвердить запись",
        callback_data=f"client:confirm:{slot_id}"
    )

    builder.button(
        text="❌ Отмена",
        callback_data="client:dates"
    )

    builder.adjust(1)

    return builder.as_markup()


# ==================================================
# МОИ ЗАПИСИ
# ==================================================

def my_bookings_keyboard(bookings):

    builder = InlineKeyboardBuilder()

    for booking in bookings:

        booking_id, slot_id, date, time = booking

        builder.button(
            text=f"❌ Отменить {date} {time}",
            callback_data=f"client:cancel:{booking_id}"
        )

    builder.adjust(1)

    return builder.as_markup()