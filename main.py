import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import init_db

from reminders import reminder_worker

from handlers.commands import com_router
from handlers.admin import admin_router
from handlers.client import client_router


# ==================================================
# ЗАПУСК БОТА
# ==================================================

async def main():

    # --------------------------------------------------
    # База данных
    # --------------------------------------------------

    await init_db()

    # --------------------------------------------------
    # Bot
    # --------------------------------------------------

    bot = Bot(
        token=BOT_TOKEN
    )

    # --------------------------------------------------
    # Dispatcher
    # --------------------------------------------------

    dp = Dispatcher()

    # --------------------------------------------------
    # Роутеры
    # --------------------------------------------------

    dp.include_router(
        com_router
    )

    dp.include_router(
        admin_router
    )

    dp.include_router(
            client_router
        )

    # --------------------------------------------------
    # Запускаем worker напоминаний
    # --------------------------------------------------

    reminder_task = asyncio.create_task(
        reminder_worker(bot)
    )

    print("Start Bot")

    try:

        # --------------------------------------------------
        # Запускаем Telegram polling
        # --------------------------------------------------

        await dp.start_polling(
            bot
        )

    finally:

        # --------------------------------------------------
        # Останавливаем worker
        # --------------------------------------------------

        reminder_task.cancel()

        try:

            await reminder_task

        except asyncio.CancelledError:

            pass

        await bot.session.close()


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )