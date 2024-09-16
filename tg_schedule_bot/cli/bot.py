import re

from aiogram import Dispatcher as BaseDispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BotCommand
from tortoise.exceptions import DoesNotExist

from tg_schedule_bot.cli import db
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

    def command(self, *commands: BotCommand):
        self._commands.extend(commands)
        return self.message(Command(commands=commands))


dp = Dispatcher()


@dp.command(
    BotCommand(
        command="пары",
        description="[день] - показать расписание на текущий или указанный день"
    ), BotCommand(
        command="lectures",
        description="[день] - показать расписание на текущий или указанный день"
    )
)
async def lectures(message: Message, command: CommandObject) -> None:
    DEFAULT_DAY = "сегодня"
    args = (command.args or "").split(" ")
    if len(args) == 0:
        try:
            group = (await db.Chat.get(id=message.chat.id)).group.name
        except DoesNotExist:
            await message.answer(
                "Группа по умолканию не установлена\n"
                "Задайте её через <code>/set_default</code> или укажите вторым аргументом"
            )
            return
        day = DEFAULT_DAY
    if len(args) == 1:
        if args[0] in Config.schedule.schedule:
            group = args[0]
            day = DEFAULT_DAY
        else:
            try:
                group = (await db.Chat.get(id=message.chat.id).prefetch_related("group")).group.name
            except DoesNotExist:
                await message.answer(
                    "Группа по умолканию не установлена\n"
                    "Задайте её через <code>/set_default</code> или укажите вторым аргументом"
                )
                return
            day = args[0]
    elif len(args) == 2:
        group = args[0]
        day = args[1]
    await message.answer(Config.schedule.lectures(day, group))


@dp.command(BotCommand(
    command="set_default",
    description="группа - установить группу по умолчанию для чата",
))
async def set_default(message: Message, command: CommandObject) -> None:
    group = command.args.split(" ")[0]
    await db.Chat.get_or_create(id=message.chat.id, defaults=dict(group=(await db.Group.get_or_create(name=group))[0]))
    await message.answer(f"Групп по умолчанию: {group}")


@dp.command(BotCommand(
    command="get_default",
    description="- показать группу по умолчанию для текущего чата"
))
async def get_default(message: Message) -> None:
    try:
        answer = (await db.Chat.get(id=message.chat.id)).group.name
    except DoesNotExist:
        answer = "Для данного чата группа по умолчанию не установлена"
    await message.answer(answer)
