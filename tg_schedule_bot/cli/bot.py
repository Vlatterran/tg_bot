from aiogram import Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BotCommand

from tg_schedule_bot.cli.config import Config

dp = Dispatcher()


@dp.message(Command(commands=BotCommand(
    command="пары",
    description="[день] - показать расписание на текущий или указаный день")
))
async def lectures(message: Message, command: CommandObject) -> None:
    await message.answer(Config.schedule.lectures(command.args or "сегодня"))
