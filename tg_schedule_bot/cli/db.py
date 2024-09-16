from tortoise import fields, Tortoise
from tortoise.models import Model


class Chat(Model):
    id = fields.IntField(primary_key=True)

    group: "Group" = fields.ForeignKeyField('models.Group', related_name='chats')


class Group(Model):
    name: str = fields.CharField(max_length=10, primary_key=True)

    chats: fields.ReverseRelation[Chat]

async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['tg_schedule_bot.cli.db']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()