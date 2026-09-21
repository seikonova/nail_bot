from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from filters.admin_filter import IsAdmin
from states.admin_state import AdminStates

from database import (
    add_booking_slot,
    get_all_slots,
    get_slots_by_date,
    delete_slot,
    delete_slots_by_date,
    get_bookings_count,
)

from keyboards.admin_kb import (
    admin_keyboard,
    back_keyboard,
    time_keyboard,
    delete_day_confirm_keyboard,
    delete_slot_keyboard,
)


admin_router = Router()


# ==================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==================================================

def valid_date(value: str) -> bool:

    try:

        datetime.strptime(
            value,
            "%d.%m.%Y"
        )

        return True

    except ValueError:

        return False


def valid_time(value: str) -> bool:

    try:

        datetime.strptime(
            value,
            "%H:%M"
        )

        return True

    except ValueError:

        return False


def time_to_minutes(value: str) -> int:

    hours, minutes = map(
        int,
        value.split(":")
    )

    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:

    hours = minutes // 60
    mins = minutes % 60

    return f"{hours:02d}:{mins:02d}"


# ==================================================
# /ADMIN
# ==================================================

@admin_router.message(
    Command("admin"),
    IsAdmin()
)
async def admin_panel(
    message: Message
):

    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# НАЗАД
# ==================================================

@admin_router.callback_query(
    F.data == "admin:back",
    IsAdmin()
)
async def admin_back(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.clear()

    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ==================================================
# ОДНО ОКНО
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:add_slot",
    IsAdmin()
)
async def add_slot_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.clear()

    await state.set_state(
        AdminStates.waiting_date
    )

    await callback.message.edit_text(
        "➕ <b>Добавление одного окна</b>\n\n"
        "Введите дату:\n\n"
        "<code>25.08.2026</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.waiting_date,
    IsAdmin()
)
async def get_slot_date(
    message: Message,
    state: FSMContext
):

    date = message.text.strip()

    if not valid_date(date):

        await message.answer(
            "❌ Неверная дата.\n\n"
            "Пример:\n"
            "<code>25.08.2026</code>",
            parse_mode="HTML"
        )

        return

    await state.update_data(
        date=date
    )

    await state.set_state(
        AdminStates.waiting_time
    )

    await message.answer(
        "🕐 Теперь введите время:\n\n"
        "<code>14:30</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.waiting_time,
    IsAdmin()
)
async def get_slot_time(
    message: Message,
    state: FSMContext
):

    time = message.text.strip()

    if not valid_time(time):

        await message.answer(
            "❌ Неверное время.\n\n"
            "Пример:\n"
            "<code>14:30</code>",
            parse_mode="HTML"
        )

        return

    data = await state.get_data()

    date = data["date"]

    created = await add_booking_slot(
        date=date,
        time=time
    )

    await state.clear()

    if created:

        text = (
            "✅ <b>Окно добавлено!</b>\n\n"
            f"📅 {date}\n"
            f"🕐 {time}"
        )

    else:

        text = (
            "⚠️ Такое окно уже существует.\n\n"
            f"📅 {date}\n"
            f"🕐 {time}"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ==================================================
# МАССОВОЕ ДОБАВЛЕНИЕ
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:add_slots",
    IsAdmin()
)
async def add_slots_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.clear()

    await state.set_state(
        AdminStates.waiting_date
    )

    await callback.message.edit_text(
        "➕ <b>Массовое добавление</b>\n\n"
        "Введите дату:\n\n"
        "<code>25.08.2026</code>",
        parse_mode="HTML"
    )


# ==================================================
# ДАТА МАССОВОГО ДОБАВЛЕНИЯ
# ==================================================

@admin_router.message(
    AdminStates.waiting_date,
    IsAdmin()
)
async def mass_date(
    message: Message,
    state: FSMContext
):

    date = message.text.strip()

    if not valid_date(date):

        await message.answer(
            "❌ Неверная дата.\n\n"
            "Введите:\n"
            "<code>25.08.2026</code>",
            parse_mode="HTML"
        )

        return

    await state.update_data(
        date=date,
        selected_times=[]
    )

    await state.set_state(
        AdminStates.selecting_times
    )

    await message.answer(
        f"📅 <b>{date}</b>\n\n"
        "Выберите время:",
        parse_mode="HTML",
        reply_markup=time_keyboard()
    )


# ==================================================
# ВЫБОР ВРЕМЕНИ
# ==================================================

@admin_router.callback_query(
    AdminStates.selecting_times,
    F.data.startswith("admin:time:"),
    IsAdmin()
)
async def select_time(
    callback: CallbackQuery,
    state: FSMContext
):

    time = callback.data.split(
        "admin:time:",
        1
    )[1]

    data = await state.get_data()

    selected = set(
        data.get(
            "selected_times",
            []
        )
    )

    if time in selected:

        selected.remove(time)

    else:

        selected.add(time)

    selected = sorted(selected)

    await state.update_data(
        selected_times=selected
    )

    await callback.message.edit_reply_markup(
        reply_markup=time_keyboard(
            set(selected)
        )
    )

    await callback.answer()


# ==================================================
# СВОЙ ИНТЕРВАЛ
# ==================================================

@admin_router.callback_query(
    AdminStates.selecting_times,
    F.data == "admin:custom_interval",
    IsAdmin()
)
async def custom_interval_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.set_state(
        AdminStates.custom_interval_start
    )

    await callback.message.edit_text(
        "⏱ <b>Свой интервал</b>\n\n"
        "Введите время начала:\n\n"
        "<code>09:00</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.custom_interval_start,
    IsAdmin()
)
async def custom_start(
    message: Message,
    state: FSMContext
):

    time = message.text.strip()

    if not valid_time(time):

        await message.answer(
            "❌ Неверное время.\n\n"
            "Пример: <code>09:00</code>",
            parse_mode="HTML"
        )

        return

    await state.update_data(
        interval_start=time
    )

    await state.set_state(
        AdminStates.custom_interval_end
    )

    await message.answer(
        "Введите время окончания:\n\n"
        "<code>20:00</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.custom_interval_end,
    IsAdmin()
)
async def custom_end(
    message: Message,
    state: FSMContext
):

    time = message.text.strip()

    if not valid_time(time):

        await message.answer(
            "❌ Неверное время.\n\n"
            "Пример: <code>20:00</code>",
            parse_mode="HTML"
        )

        return

    data = await state.get_data()

    start = time_to_minutes(
        data["interval_start"]
    )

    end = time_to_minutes(time)

    if end <= start:

        await message.answer(
            "❌ Конечное время должно быть "
            "позже начального."
        )

        return

    await state.update_data(
        interval_end=time
    )

    await state.set_state(
        AdminStates.custom_interval_step
    )

    await message.answer(
        "⏱ Введите интервал в минутах.\n\n"
        "Например:\n"
        "<code>60</code>\n\n"
        "Для окон каждые 30 минут:\n"
        "<code>30</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.custom_interval_step,
    IsAdmin()
)
async def custom_step(
    message: Message,
    state: FSMContext
):

    try:

        step = int(
            message.text.strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите число минут.\n\n"
            "Например: <code>30</code>",
            parse_mode="HTML"
        )

        return

    if step <= 0:

        await message.answer(
            "❌ Интервал должен быть больше 0."
        )

        return

    data = await state.get_data()

    start = time_to_minutes(
        data["interval_start"]
    )

    end = time_to_minutes(
        data["interval_end"]
    )

    times = []

    current = start

    while current <= end:

        times.append(
            minutes_to_time(current)
        )

        current += step

    await state.update_data(
        selected_times=times
    )

    await state.set_state(
        AdminStates.selecting_times
    )

    await message.answer(
        "✅ <b>Интервал создан!</b>\n\n"
        f"⏱ От: <b>{data['interval_start']}</b>\n"
        f"До: <b>{data['interval_end']}</b>\n"
        f"Шаг: <b>{step} мин.</b>\n\n"
        "Выбранные окна:\n"
        + "\n".join(
            f"• {time}"
            for time in times
        ),
        parse_mode="HTML",
        reply_markup=time_keyboard(
            set(times)
        )
    )


# ==================================================
# ПОДТВЕРЖДЕНИЕ МАССОВОГО ДОБАВЛЕНИЯ
# ==================================================

@admin_router.callback_query(
    AdminStates.selecting_times,
    F.data == "admin:confirm_slots",
    IsAdmin()
)
async def confirm_slots(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    date = data.get("date")

    selected_times = data.get(
        "selected_times",
        []
    )

    if not selected_times:

        await callback.answer(
            "❌ Выберите хотя бы одно время.",
            show_alert=True
        )

        return

    added = 0
    skipped = 0

    for time in selected_times:

        result = await add_booking_slot(
            date=date,
            time=time
        )

        if result:
            added += 1
        else:
            skipped += 1

    await state.clear()

    await callback.answer(
        "Готово!"
    )

    text = (
        "✅ <b>Массовое добавление завершено</b>\n\n"
        f"📅 Дата: <b>{date}</b>\n\n"
        f"➕ Добавлено: <b>{added}</b>\n"
        f"⚠️ Уже существовало: <b>{skipped}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ОТМЕНА МАССОВОГО ДОБАВЛЕНИЯ
# ==================================================

@admin_router.callback_query(
    AdminStates.selecting_times,
    F.data == "admin:cancel_slots",
    IsAdmin()
)
async def cancel_slots(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer(
        "Отменено"
    )

    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ==================================================
# РАСПИСАНИЕ
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:schedule",
    IsAdmin()
)
async def schedule(
    callback: CallbackQuery
):

    await callback.answer()

    slots = await get_all_slots()

    if not slots:

        await callback.message.edit_text(
            "📅 <b>Расписание пустое.</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        return

    # Группируем по датам
    grouped = {}

    for slot in slots:

        date = slot[1]

        if date not in grouped:
            grouped[date] = []

        grouped[date].append(slot)

    # Берём только первые 7 дней
    dates = list(grouped.keys())[:7]

    for index, date in enumerate(dates):

        day_slots = grouped[date]

        text = (
            f"📅 <b>{date}</b>\n\n"
        )

        for slot_id, _, time, available in day_slots:

            status = (
                "🟢"
                if available
                else "🔴"
            )

            text += (
                f"{status} "
                f"<code>{time}</code>\n"
            )

        text += (
            f"\nВсего окон: <b>{len(day_slots)}</b>"
        )

        if len(text) > 3500:

            text = text[:3400]
            text += "\n\n..."

        if index == 0:

            await callback.message.edit_text(
                text,
                parse_mode="HTML"
            )

        else:

            await callback.message.answer(
                text,
                parse_mode="HTML"
            )

    await callback.message.answer(
        "Выберите действие:",
        reply_markup=back_keyboard()
    )


# ==================================================
# РАСПИСАНИЕ НА НЕДЕЛЮ
# ==================================================

@admin_router.callback_query(
    F.data == "admin:week",
    IsAdmin()
)
async def week_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.set_state(
        AdminStates.week_start_date
    )

    await callback.message.edit_text(
        "📆 <b>Расписание на неделю</b>\n\n"
        "Введите дату начала недели:\n\n"
        "<code>25.08.2026</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.week_start_date,
    IsAdmin()
)
async def week_get_date(
    message: Message,
    state: FSMContext
):

    date = message.text.strip()

    if not valid_date(date):

        await message.answer(
            "❌ Неверная дата.\n\n"
            "Пример:\n"
            "<code>25.08.2026</code>",
            parse_mode="HTML"
        )

        return

    start = datetime.strptime(
        date,
        "%d.%m.%Y"
    )

    await state.clear()

    slots = await get_all_slots()

    grouped = {}

    for slot in slots:

        if not valid_date(slot[1]):
            continue

        slot_date = datetime.strptime(
            slot[1],
            "%d.%m.%Y"
        )

        if (
            start
            <= slot_date
            < start + timedelta(days=7)
        ):

            if slot[1] not in grouped:
                grouped[slot[1]] = []

            grouped[slot[1]].append(slot)

    if not grouped:

        await message.answer(
            "📆 За следующие 7 дней "
            "окон нет.",
            reply_markup=admin_keyboard()
        )

        return

    # Каждый день отдельным сообщением.
    # Поэтому MESSAGE_TOO_LONG не возникает.

    first = True

    for i in range(7):

        current = start + timedelta(days=i)

        date_text = current.strftime(
            "%d.%m.%Y"
        )

        day_slots = grouped.get(
            date_text,
            []
        )

        text = (
            f"📅 <b>{date_text}</b>\n\n"
        )

        if not day_slots:

            text += "— Нет окон"

        else:

            for slot in day_slots:

                status = (
                    "🟢"
                    if slot[3]
                    else "🔴"
                )

                text += (
                    f"{status} "
                    f"<code>{slot[2]}</code>\n"
                )

        if first:

            await message.answer(
                text,
                parse_mode="HTML"
            )

            first = False

        else:

            await message.answer(
                text,
                parse_mode="HTML"
            )

    await message.answer(
        "👑 Админ-панель",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ==================================================
# УДАЛЕНИЕ ОДНОГО ОКНА
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:delete",
    IsAdmin()
)
async def delete_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    slots = await get_all_slots()

    if not slots:

        await callback.message.edit_text(
            "🗑 Удалять нечего.\n\n"
            "Расписание пустое.",
            reply_markup=back_keyboard()
        )

        return

    # Ограничиваем вывод
    # чтобы клавиатура не стала огромной.

    slots = slots[:50]

    await callback.message.edit_text(
        "🗑 <b>Удаление окна</b>\n\n"
        "Выберите окно:",
        parse_mode="HTML",
        reply_markup=delete_slot_keyboard(slots)
    )


@admin_router.callback_query(
    F.data.startswith("admin:delete_slot:"),
    IsAdmin()
)
async def delete_one_slot(
    callback: CallbackQuery
):

    slot_id_text = callback.data.split(
        "admin:delete_slot:",
        1
    )[1]

    try:

        slot_id = int(
            slot_id_text
        )

    except ValueError:

        await callback.answer(
            "Ошибка ID",
            show_alert=True
        )

        return

    await delete_slot(
        slot_id
    )

    await callback.answer(
        "Окно удалено"
    )

    slots = await get_all_slots()

    if not slots:

        await callback.message.edit_text(
            "✅ Окно удалено.\n\n"
            "Расписание теперь пустое.",
            reply_markup=back_keyboard()
        )

        return

    slots = slots[:50]

    await callback.message.edit_text(
        "🗑 <b>Удаление окна</b>\n\n"
        "Выберите окно:",
        parse_mode="HTML",
        reply_markup=delete_slot_keyboard(slots)
    )


# ==================================================
# ==================================================
# УДАЛЕНИЕ ЦЕЛОГО ДНЯ
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:delete_day",
    IsAdmin()
)
async def delete_day_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.set_state(
        AdminStates.deleting_day
    )

    await callback.message.edit_text(
        "🗑 <b>Удаление целого дня</b>\n\n"
        "Введите дату:\n\n"
        "<code>25.08.2026</code>",
        parse_mode="HTML"
    )


@admin_router.message(
    AdminStates.deleting_day,
    IsAdmin()
)
async def delete_day_get_date(
    message: Message,
    state: FSMContext
):

    date = message.text.strip()

    if not valid_date(date):

        await message.answer(
            "❌ Неверная дата.\n\n"
            "Пример:\n"
            "<code>25.08.2026</code>",
            parse_mode="HTML"
        )

        return

    slots = await get_slots_by_date(
        date
    )

    if not slots:

        await state.clear()

        await message.answer(
            "❌ На эту дату нет окон.\n\n"
            f"📅 {date}",
            reply_markup=admin_keyboard()
        )

        return

    await state.update_data(
        delete_date=date
    )

    text = (
        "⚠️ <b>Удалить весь день?</b>\n\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Окон: <b>{len(slots)}</b>\n\n"
    )

    # Ограничиваем текст
    # даже если окон очень много.

    for slot in slots[:30]:

        status = (
            "🟢"
            if slot[3]
            else "🔴"
        )

        text += (
            f"{status} {slot[2]}\n"
        )

    if len(slots) > 30:

        text += (
            f"\n... ещё "
            f"{len(slots) - 30}"
        )

    text += (
        "\n\n"
        "❗ Все окна этого дня "
        "будут удалены."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=delete_day_confirm_keyboard()
    )


@admin_router.callback_query(
    AdminStates.deleting_day,
    F.data == "admin:delete_day_confirm",
    IsAdmin()
)
async def delete_day_confirm(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    date = data.get(
        "delete_date"
    )

    if not date:

        await state.clear()

        await callback.answer(
            "Дата не найдена",
            show_alert=True
        )

        return

    deleted = await delete_slots_by_date(
        date
    )

    await state.clear()

    await callback.answer(
        "День удалён"
    )

    await callback.message.edit_text(
        "✅ <b>День удалён!</b>\n\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🗑 Удалено окон: <b>{deleted}</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


@admin_router.callback_query(
    AdminStates.deleting_day,
    F.data == "admin:delete_day_cancel",
    IsAdmin()
)
async def delete_day_cancel(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer(
        "Удаление отменено"
    )

    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ==================================================
# ==================================================
# ЗАПИСИ
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:bookings",
    IsAdmin()
)
async def bookings(
    callback: CallbackQuery
):

    await callback.answer()

    count = await get_bookings_count()

    await callback.message.edit_text(
        "📋 <b>Записи клиентов</b>\n\n"
        f"Всего записей: <b>{count}</b>",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


# ==================================================
# ==================================================
# СТАТИСТИКА
# ==================================================
# ==================================================

@admin_router.callback_query(
    F.data == "admin:stats",
    IsAdmin()
)
async def stats(
    callback: CallbackQuery
):

    await callback.answer()

    slots = await get_all_slots()

    total = len(slots)

    available = sum(
        1
        for slot in slots
        if slot[3] == 1
    )

    busy = total - available

    bookings_count = (
        await get_bookings_count()
    )

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"📅 Всего окон: <b>{total}</b>\n"
        f"🟢 Свободных: <b>{available}</b>\n"
        f"🔴 Занятых: <b>{busy}</b>\n"
        f"👥 Записей: <b>{bookings_count}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )