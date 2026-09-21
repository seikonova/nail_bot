import aiosqlite

from config import DATABASE


# ==================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ==================================================

async def init_db():

    async with aiosqlite.connect(DATABASE) as db:

        # ==================================================
        # ОКНА ДЛЯ ЗАПИСИ
        # ==================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS booking_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        # ==================================================
        # ЗАПИСИ КЛИЕНТОВ
        # ==================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                slot_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                reminder_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        # ==================================================
        # МИГРАЦИЯ СТАРОЙ БАЗЫ
        # ==================================================

        cursor = await db.execute(
            "PRAGMA table_info(bookings)"
        )

        columns = await cursor.fetchall()

        column_names = [
            column[1]
            for column in columns
        ]

        if "reminder_sent" not in column_names:

            await db.execute(
                """
                ALTER TABLE bookings
                ADD COLUMN reminder_sent INTEGER NOT NULL DEFAULT 0
                """
            )

            print(
                "✅ В таблицу bookings добавлено поле reminder_sent"
            )

        await db.commit()

    print("✅ База данных инициализирована")


# ==================================================
# ДОБАВЛЕНИЕ ОКНА
# ==================================================

async def add_booking_slot(
    date: str,
    time: str
):

    async with aiosqlite.connect(DATABASE) as db:

        # Не создаём одинаковые окна
        cursor = await db.execute(
            """
            SELECT id
            FROM booking_slots
            WHERE date = ?
            AND time = ?
            """,
            (
                date,
                time
            )
        )

        existing = await cursor.fetchone()

        if existing:
            return False

        await db.execute(
            """
            INSERT INTO booking_slots
            (
                date,
                time,
                is_available
            )
            VALUES (?, ?, 1)
            """,
            (
                date,
                time
            )
        )

        await db.commit()

        return True


# ==================================================
# ПОЛУЧИТЬ ВСЕ ОКНА
# ==================================================

async def get_all_slots():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                date,
                time,
                is_available
            FROM booking_slots
            ORDER BY
                substr(date, 7, 4),
                substr(date, 4, 2),
                substr(date, 1, 2),
                time
            """
        )

        return await cursor.fetchall()


# ==================================================
# ПОЛУЧИТЬ ДАТЫ СО СВОБОДНЫМИ ОКНАМИ
# ==================================================

async def get_available_slots():
    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT DISTINCT date
            FROM booking_slots
            WHERE is_available = 1
            ORDER BY date
            """
        )

        return await cursor.fetchall()


# ==================================================
# ПОЛУЧИТЬ СВОБОДНЫЕ ОКНА НА КОНКРЕТНУЮ ДАТУ
# ==================================================

async def get_slots_by_date(date: str):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                date,
                time,
                is_available
            FROM booking_slots
            WHERE date = ?
              AND is_available = 1
            ORDER BY time
            """,
            (date,)
        )

        return await cursor.fetchall()


# ==================================================
# ПОЛУЧИТЬ ОКНО ПО ID
# ==================================================

async def get_slot_by_id(slot_id: int):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                date,
                time,
                is_available
            FROM booking_slots
            WHERE id = ?
            """,
            (slot_id,)
        )

        return await cursor.fetchone()


# ==================================================
# УДАЛИТЬ ОКНО
# ==================================================

async def delete_slot(
    slot_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        # Проверяем, есть ли запись на это окно
        cursor = await db.execute(
            """
            SELECT id
            FROM bookings
            WHERE slot_id = ?
            """,
            (slot_id,)
        )

        booking = await cursor.fetchone()

        if booking:
            return False

        await db.execute(
            """
            DELETE FROM booking_slots
            WHERE id = ?
            """,
            (slot_id,)
        )

        await db.commit()

        return True


# ==================================================
# УДАЛИТЬ ВСЕ ОКНА ЗА ДЕНЬ
# ==================================================

async def delete_slots_by_date(
    date: str
):

    async with aiosqlite.connect(DATABASE) as db:

        # Проверяем, есть ли записи клиентов
        cursor = await db.execute(
            """
            SELECT bookings.id
            FROM bookings
            INNER JOIN booking_slots
                ON bookings.slot_id = booking_slots.id
            WHERE booking_slots.date = ?
            """,
            (date,)
        )

        bookings = await cursor.fetchall()

        if bookings:
            return False

        await db.execute(
            """
            DELETE FROM booking_slots
            WHERE date = ?
            """,
            (date,)
        )

        await db.commit()

        return True


# ==================================================
# СОЗДАТЬ ЗАПИСЬ КЛИЕНТА
# ==================================================

async def create_booking(
    user_id: int,
    slot_id: int,
    created_at: str
):

    async with aiosqlite.connect(DATABASE) as db:

        # Проверяем окно
        cursor = await db.execute(
            """
            SELECT is_available
            FROM booking_slots
            WHERE id = ?
            """,
            (slot_id,)
        )

        slot = await cursor.fetchone()

        if not slot:
            return False

        if slot[0] != 1:
            return False

        # Создаём запись
        await db.execute(
            """
            INSERT INTO bookings
            (
                user_id,
                slot_id,
                created_at,
                reminder_sent
            )
            VALUES (?, ?, ?, 0)
            """,
            (
                user_id,
                slot_id,
                created_at
            )
        )

        # Закрываем окно
        await db.execute(
            """
            UPDATE booking_slots
            SET is_available = 0
            WHERE id = ?
            """,
            (slot_id,)
        )

        await db.commit()

        return True


# ==================================================
# МОИ ЗАПИСИ
# ==================================================

async def get_user_bookings(
    user_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                bookings.id,
                bookings.slot_id,
                booking_slots.date,
                booking_slots.time
            FROM bookings
            INNER JOIN booking_slots
                ON bookings.slot_id = booking_slots.id
            WHERE bookings.user_id = ?
            ORDER BY
                substr(booking_slots.date, 7, 4),
                substr(booking_slots.date, 4, 2),
                substr(booking_slots.date, 1, 2),
                booking_slots.time
            """,
            (user_id,)
        )

        return await cursor.fetchall()


# ==================================================
# ПОЛУЧИТЬ ЗАПИСЬ
# ==================================================

async def get_booking_by_id(
    booking_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                bookings.id,
                bookings.user_id,
                bookings.slot_id,
                booking_slots.date,
                booking_slots.time
            FROM bookings
            INNER JOIN booking_slots
                ON bookings.slot_id = booking_slots.id
            WHERE bookings.id = ?
            """,
            (booking_id,)
        )

        return await cursor.fetchone()


# ==================================================
# ОТМЕНА ЗАПИСИ
# ==================================================

async def cancel_booking(
    booking_id: int,
    user_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                slot_id
            FROM bookings
            WHERE id = ?
            AND user_id = ?
            """,
            (
                booking_id,
                user_id
            )
        )

        booking = await cursor.fetchone()

        if not booking:
            return False

        slot_id = booking[0]

        # Удаляем запись
        await db.execute(
            """
            DELETE FROM bookings
            WHERE id = ?
            AND user_id = ?
            """,
            (
                booking_id,
                user_id
            )
        )

        # Освобождаем окно
        await db.execute(
            """
            UPDATE booking_slots
            SET is_available = 1
            WHERE id = ?
            """,
            (slot_id,)
        )

        await db.commit()

        return True


# ==================================================
# КОЛИЧЕСТВО ЗАПИСЕЙ
# ==================================================

async def get_bookings_count():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM bookings
            """
        )

        result = await cursor.fetchone()

        return result[0]


# ==================================================
# ЗАПИСИ, КОТОРЫМ НУЖНО ОТПРАВИТЬ НАПОМИНАНИЕ
# ==================================================

async def get_bookings_for_reminder(
    start_datetime: str,
    end_datetime: str
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT
                bookings.id,
                bookings.user_id,
                bookings.slot_id,
                booking_slots.date,
                booking_slots.time
            FROM bookings
            INNER JOIN booking_slots
                ON bookings.slot_id = booking_slots.id
            WHERE bookings.reminder_sent = 0
            """,
        )

        rows = await cursor.fetchall()

        result = []

        from datetime import datetime

        for row in rows:

            booking_id = row[0]
            user_id = row[1]
            slot_id = row[2]
            date = row[3]
            time = row[4]

            try:

                booking_datetime = datetime.strptime(
                    f"{date} {time}",
                    "%d.%m.%Y %H:%M"
                )

                start = datetime.fromisoformat(
                    start_datetime
                )

                end = datetime.fromisoformat(
                    end_datetime
                )

            except ValueError:
                continue

            if start <= booking_datetime <= end:

                result.append(
                    (
                        booking_id,
                        user_id,
                        slot_id,
                        date,
                        time
                    )
                )

        return result


# ==================================================
# ПОМЕТИТЬ НАПОМИНАНИЕ КАК ОТПРАВЛЕННОЕ
# ==================================================

async def mark_reminder_sent(
    booking_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE bookings
            SET reminder_sent = 1
            WHERE id = ?
            """,
            (booking_id,)
        )

        await db.commit()


# ==================================================
# СБРОС НАПОМИНАНИЯ
# ==================================================

async def reset_booking_reminder(
    booking_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE bookings
            SET reminder_sent = 0
            WHERE id = ?
            """,
            (booking_id,)
        )

        await db.commit()