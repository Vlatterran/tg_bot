import re

from aiogram import Dispatcher as BaseDispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BotCommand

from tg_schedule_bot.cli.config import Config


class Dispatcher(BaseDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands: list[BotCommand] = []
        self.startup.register(self._startup)

    async def _startup(self, bot):
        await bot.set_my_commands(
            command
            for command
            in self._commands if re.match('^[A-Za-z0-9_]*$', command.command)
        )

    def command(self, command: BotCommand):
        self._commands.append(command)
        return self.message(Command(commands=command))


dp = Dispatcher()


@dp.command(BotCommand(
    command="пары",
    description="[день] - показать расписание на текущий или указанный день"
))
async def lectures(message: Message, command: CommandObject) -> None:
    await message.answer(Config.schedule.lectures(command.args or "сегодня"))
