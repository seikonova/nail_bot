import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from database import (
    get_bookings_for_reminder,
    mark_reminder_sent
)


# ==================================================
# НАПОМИНАНИЕ КЛИЕНТУ
# ==================================================

async def send_booking_reminder(
    bot: Bot,
    user_id: int,
    date: str,
    time: str
):

    text = (
        "🔔 <b>Напоминание о записи</b>\n\n"
        "Вы записаны к мастеру <b>завтра</b>. 💅\n\n"
        f"📅 Дата: <b>{date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n\n"
        "Ждём вас! ❤️"
    )

    try:

        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML"
        )

        return True

    except Exception as e:

        print(
            f"❌ Не удалось отправить напоминание "
            f"user_id={user_id}: {e}"
        )

        return False


# ==================================================
# ПРОВЕРКА НАПОМИНАНИЙ
# ==================================================

async def check_reminders(
    bot: Bot
):

    now = datetime.now()

    # Ищем записи примерно через 24 часа.
    #
    # Используем диапазон 23-25 часов,
    # чтобы напоминание не потерялось,
    # если бот был выключен.

    start = now + timedelta(
        hours=23
    )

    end = now + timedelta(
        hours=25
    )

    bookings = await get_bookings_for_reminder(
        start_datetime=start.isoformat(
            timespec="minutes"
        ),
        end_datetime=end.isoformat(
            timespec="minutes"
        )
    )

    if not bookings:
        return

    print(
        f"🔔 Найдено напоминаний: {len(bookings)}"
    )

    for booking in bookings:

        (
            booking_id,
            user_id,
            slot_id,
            date,
            time
        ) = booking

        sent = await send_booking_reminder(
            bot=bot,
            user_id=user_id,
            date=date,
            time=time
        )

        if sent:

            await mark_reminder_sent(
                booking_id
            )

            print(
                f"✅ Напоминание отправлено "
                f"user_id={user_id}, "
                f"booking_id={booking_id}"
            )

        # Небольшая пауза между сообщениями
        await asyncio.sleep(0.1)


# ==================================================
# ФОНОВЫЙ WORKER
# ==================================================

async def reminder_worker(
    bot: Bot
):

    print(
        "🔔 Система напоминаний запущена"
    )

    while True:

        try:

            await check_reminders(
                bot
            )

        except Exception as e:

            print(
                f"❌ Ошибка системы напоминаний: {e}"
            )

        # Проверяем каждые 5 минут

        await asyncio.sleep(
            5 * 60
        )