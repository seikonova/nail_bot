from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from texts import start_text
import keyboards.reply_kb as rkb


com_router = Router()


@com_router.message(CommandStart())
async def start(message: Message):

    await message.answer(
        text=start_text,
        parse_mode="Markdown",
        reply_markup=rkb.start_kb
    )