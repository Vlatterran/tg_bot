import asyncio
import json
import logging
import sys
from enum import Enum

import typer
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tg_schedule_bot.cli.bot import dp
from tg_schedule_bot.cli.config import Config
from tg_schedule_bot.src.schedule import parse as parse_schedule, Schedule

app = typer.Typer()


class Format(str, Enum):
    JSON = "JSON"


@app.command()
def parse(
        group: str = typer.Option(...),
        output: typer.FileTextWrite = typer.Option("schedule.json", encoding="utf8"),
        schedule_format: Format = typer.Option(default=Format.JSON),
):
    a = asyncio.run(parse_schedule(group))
    match schedule_format:
        case Format.JSON:
            json.dump(a, output, indent=4, ensure_ascii=False)
        case _:
            raise RuntimeError("format is not supported yet")


@app.command()
def bot(
        schedule_file: typer.FileText = typer.Option("schedule.json", "--schedule", encoding="utf8"),
        schedule_format: Format = typer.Option(Format.JSON, "--format"),
        token: str = typer.Option(..., envvar="Token", prompt=True, hide_input=True),
) -> None:
    match schedule_format:
        case Format.JSON:
            Config.schedule = Schedule(json.load(schedule_file))
        case _:
            raise RuntimeError("format is not supported yet")

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot_obj = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    asyncio.run(dp.start_polling(bot_obj))
