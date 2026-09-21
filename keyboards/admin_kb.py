from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ==================================================
# АДМИН-ПАНЕЛЬ
# ==================================================

def admin_keyboard():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Одно окно",
        callback_data="admin:add_slot"
    )

    builder.button(
        text="➕ Массово",
        callback_data="admin:add_slots"
    )

    builder.button(
        text="📅 Расписание",
        callback_data="admin:schedule"
    )

    builder.button(
        text="📆 Неделя",
        callback_data="admin:week"
    )

    builder.button(
        text="🗑 Удалить окно",
        callback_data="admin:delete"
    )

    builder.button(
        text="🗑 Удалить день",
        callback_data="admin:delete_day"
    )

    builder.button(
        text="📋 Записи",
        callback_data="admin:bookings"
    )

    builder.button(
        text="📊 Статистика",
        callback_data="admin:stats"
    )

    builder.adjust(2)

    return builder.as_markup()


# ==================================================
# НАЗАД
# ==================================================

def back_keyboard():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Назад",
        callback_data="admin:back"
    )

    return builder.as_markup()


# ==================================================
# ВРЕМЕНА
# ==================================================

def time_keyboard(
    selected_times=None
):

    if selected_times is None:
        selected_times = set()

    builder = InlineKeyboardBuilder()

    times = [
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
    ]

    for time in times:

        if time in selected_times:
            text = f"✅ {time}"
        else:
            text = time

        builder.button(
            text=text,
            callback_data=f"admin:time:{time}"
        )

    builder.adjust(3)

    builder.row(
        InlineKeyboardButton(
            text="⏱ Свой интервал",
            callback_data="admin:custom_interval"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="✅ Добавить выбранные",
            callback_data="admin:confirm_slots"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin:cancel_slots"
        )
    )

    return builder.as_markup()


# ==================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ ДНЯ
# ==================================================

def delete_day_confirm_keyboard():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Да, удалить",
        callback_data="admin:delete_day_confirm"
    )

    builder.button(
        text="❌ Отмена",
        callback_data="admin:delete_day_cancel"
    )

    builder.adjust(1)

    return builder.as_markup()


# ==================================================
# УДАЛЕНИЕ ОКНА
# ==================================================

def delete_slot_keyboard(slots):

    builder = InlineKeyboardBuilder()

    for slot_id, date, time, available in slots:

        status = "🟢" if available else "🔴"

        builder.button(
            text=f"{status} {date} — {time}",
            callback_data=f"admin:delete_slot:{slot_id}"
        )

    builder.button(
        text="⬅️ Назад",
        callback_data="admin:back"
    )

    builder.adjust(1)

    return builder.as_markup()


# ==================================================
# РАСПИСАНИЕ
# ==================================================

def schedule_dates_keyboard(
    dates
):

    builder = InlineKeyboardBuilder()

    for date in dates:

        builder.button(
            text=f"📅 {date}",
            callback_data=f"admin:date:{date}"
        )

    builder.button(
        text="⬅️ Назад",
        callback_data="admin:back"
    )

    builder.adjust(2)

    return builder.as_markup()