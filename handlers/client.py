from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.client_kb import (
    dates_keyboard,
    times_keyboard,
    confirm_booking_keyboard,
    my_bookings_keyboard
)

from keyboards.reply_kb import start_kb

from database import (
    get_available_slots,
    get_slots_by_date,
    get_slot_by_id,
    create_booking,
    get_user_bookings,
    cancel_booking
)


client_router = Router()


# ==================================================
# ЗАПИСАТЬСЯ
# ==================================================

@client_router.message(
    F.text == "💅 Записаться"
)
async def booking_start(message: Message):

    dates = await get_available_slots()

    if not dates:

        await message.answer(
            "😔 Сейчас свободных окон для записи нет.\n\n"
            "Попробуйте зайти позже.",
            reply_markup=start_kb
        )

        return

    dates = [
        row[0]
        for row in dates
    ]

    await message.answer(
        "💅 <b>Запись к мастеру</b>\n\n"
        "Выберите удобную дату:",
        parse_mode="HTML",
        reply_markup=dates_keyboard(dates)
    )


# ==================================================
# ВЫБОР ДАТЫ
# ==================================================

@client_router.callback_query(
    F.data.startswith("client:date:")
)
async def select_date(
    callback: CallbackQuery
):

    date = callback.data.split(
        "client:date:",
        1
    )[1]

    slots = await get_slots_by_date(
        date
    )

    if not slots:

        await callback.answer(
            "На эту дату свободных окон уже нет.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        f"📅 <b>{date}</b>\n\n"
        "Выберите удобное время:",
        parse_mode="HTML",
        reply_markup=times_keyboard(slots)
    )

    await callback.answer()


# ==================================================
# ВЫБОР ВРЕМЕНИ
# ==================================================

@client_router.callback_query(
    F.data.startswith("client:slot:")
)
async def select_slot(
    callback: CallbackQuery
):

    slot_id = int(
        callback.data.split(
            "client:slot:",
            1
        )[1]
    )

    slot = await get_slot_by_id(slot_id)

    if not slot:

        await callback.answer(
            "❌ Окно не найдено.",
            show_alert=True
        )

        return

    slot_id, date, time, available = slot

    if not available:

        await callback.answer(
            "❌ Это окно уже занято.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "💅 <b>Подтверждение записи</b>\n\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n\n"
        "Подтвердить запись?",
        parse_mode="HTML",
        reply_markup=confirm_booking_keyboard(
            slot_id
        )
    )

    await callback.answer()


# ==================================================
# ПОДТВЕРЖДЕНИЕ
# ==================================================

@client_router.callback_query(
    F.data.startswith("client:confirm:")
)
async def confirm_booking(
    callback: CallbackQuery
):

    slot_id = int(
        callback.data.split(
            "client:confirm:",
            1
        )[1]
    )

    success, status = await create_booking(
        user_id=callback.from_user.id,
        slot_id=slot_id
    )

    if not success:

        if status == "busy":

            text = "❌ К сожалению, это время уже заняли."

        elif status == "not_found":

            text = "❌ Окно не найдено."

        elif status == "already_booked":

            text = "❌ Вы уже записаны на это время."

        else:

            text = "❌ Не удалось создать запись."

        await callback.answer(
            text,
            show_alert=True
        )

        return

    slot = await get_slot_by_id(slot_id)

    # После записи окно уже будет unavailable,
    # но дата и время нам всё равно нужны.
    # Поэтому получаем их из БД через SQL отдельно.
    from database import get_booking_info

    info = await get_booking_info(
        callback.from_user.id,
        slot_id
    )

    if info:

        date, time = info

    elif slot:

        _, date, time, _ = slot

    else:

        date = "—"
        time = "—"

    await callback.message.edit_text(
        "✅ <b>Вы успешно записались!</b>\n\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n\n"
        "Ждём вас 💅",
        parse_mode="HTML"
    )

    await callback.answer(
        "Запись создана!"
    )


# ==================================================
# МОИ ЗАПИСИ
# ==================================================

@client_router.message(
    F.text == "📋 Мои записи"
)
async def my_bookings(
    message: Message
):

    bookings = await get_user_bookings(
        message.from_user.id
    )

    if not bookings:

        await message.answer(
            "📋 <b>Мои записи</b>\n\n"
            "У вас пока нет активных записей.",
            parse_mode="HTML",
            reply_markup=start_kb
        )

        return

    text = "📋 <b>Мои записи</b>\n\n"

    for index, booking in enumerate(
        bookings,
        start=1
    ):

        booking_id, slot_id, date, time = booking

        text += (
            f"<b>{index}.</b> "
            f"📅 {date} — 🕐 {time}\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=my_bookings_keyboard(
            bookings
        )
    )


# ==================================================
# ОТМЕНА ЗАПИСИ
# ==================================================

@client_router.callback_query(
    F.data.startswith("client:cancel:")
)
async def cancel_my_booking(
    callback: CallbackQuery
):

    booking_id = int(
        callback.data.split(
            "client:cancel:",
            1
        )[1]
    )

    result = await cancel_booking(
        booking_id=booking_id,
        user_id=callback.from_user.id
    )

    if not result:

        await callback.answer(
            "❌ Запись не найдена.",
            show_alert=True
        )

        return

    await callback.answer(
        "✅ Запись отменена."
    )

    bookings = await get_user_bookings(
        callback.from_user.id
    )

    if not bookings:

        await callback.message.edit_text(
            "📋 <b>Мои записи</b>\n\n"
            "У вас больше нет активных записей.",
            parse_mode="HTML"
        )

        return

    text = "📋 <b>Мои записи</b>\n\n"

    for index, booking in enumerate(
        bookings,
        start=1
    ):

        booking_id, slot_id, date, time = booking

        text += (
            f"<b>{index}.</b> "
            f"📅 {date} — 🕐 {time}\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=my_bookings_keyboard(
            bookings
        )
    )


# ==================================================
# НАЗАД К ДАТАМ
# ==================================================

@client_router.callback_query(
    F.data == "client:dates"
)
async def back_to_dates(
    callback: CallbackQuery
):

    dates = await get_available_slots()

    dates = [
        row[0]
        for row in dates
    ]

    if not dates:

        await callback.message.edit_text(
            "😔 Свободных окон сейчас нет."
        )

        await callback.answer()

        return

    await callback.message.edit_text(
        "💅 <b>Запись к мастеру</b>\n\n"
        "Выберите дату:",
        parse_mode="HTML",
        reply_markup=dates_keyboard(dates)
    )

    await callback.answer()


# ==================================================
# ЗАКРЫТЬ
# ==================================================

@client_router.callback_query(
    F.data == "client:close"
)
async def close_booking(
    callback: CallbackQuery
):

    await callback.message.delete()

    await callback.answer()


# ==================================================
# УСЛУГИ
# ==================================================

@client_router.message(
    F.text == "💰 Услуги и цены"
)
async def services(message: Message):

    await message.answer(
        "💰 <b>Услуги и цены</b>\n\n"
        "💅 Маникюр — 1500 ₽\n"
        "💎 Маникюр + покрытие — 2000 ₽\n"
        "✨ Дизайн — от 300 ₽\n"
        "💅 Снятие покрытия — 300 ₽",
        parse_mode="HTML",
        reply_markup=start_kb
    )


# ==================================================
# АДРЕС
# ==================================================

@client_router.message(
    F.text == "📍 Адрес"
)
async def address(message: Message):

    await message.answer(
        "📍 <b>Адрес мастера</b>\n\n"
        "Укажите здесь адрес вашего кабинета.",
        parse_mode="HTML",
        reply_markup=start_kb
    )


# ==================================================
# СВЯЗАТЬСЯ
# ==================================================

@client_router.message(
    F.text == "☎️ Связаться с мастером"
)
async def contact_master(message: Message):

    await message.answer(
        "☎️ <b>Связаться с мастером</b>\n\n"
        "Напишите мастеру:\n"
        "@username",
        parse_mode="HTML",
        reply_markup=start_kb
    )