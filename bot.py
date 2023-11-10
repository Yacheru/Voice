import discord
import json

from discord import Activity, ActivityType
from discord.ext import commands, tasks
from data.postgresql import cursor

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=commands.when_mentioned_or(f"{cfg['BOT']['prefix']}"),
            intents=intents,
            help_command=None)

    async def setup_hook(self) -> None:
        from main.voice_activity.voice_activity import reset_d7, reset_h24
        self.loop.create_task(reset_h24())
        self.loop.create_task(reset_d7())
        # self.loop.create_task(send_top_users())
        # self.loop.create_task(remove_role_after_1_days())

        from main.temp_voices.temp_voices import Temp
        self.add_view(Temp())

    async def update_status(self):
        cursor.execute("SELECT COUNT(channel_id) FROM temp_channels")
        channels = cursor.fetchone()
        await self.change_presence(activity=Activity(type=ActivityType.watching, name=f"за {channels[0]} каналами"))

    @tasks.loop(minutes=1)
    async def update_status_loop(self):
        await self.update_status()

    async def on_ready(self):
        from main.temp_voices.func import topadminsessions
        # await topadminsessions.start()
        await self.tree.sync()
        self.update_status_loop.start()


TOKEN = cfg['BOT']['TOKEN']
bot = Bot()
