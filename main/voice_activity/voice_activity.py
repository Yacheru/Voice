import asyncio
import datetime
import json
import pytz
from discord import Embed, Colour
from discord.ext import commands
from bot import bot
from data.postgresql import cursor

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

async def reset_h24():
    while True:
        await asyncio.sleep(1440)
        cursor.execute("UPDATE activity SET h24 = 0")

async def reset_d7():
    while True:
        await asyncio.sleep(10080)
        cursor.execute("UPDATE activity SET d7 = 0")

async def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"**{int(hours)}** часов **{int(minutes)}** минут"

async def send_top_users():
    await bot.wait_until_ready()

    while not bot.is_closed():
        current_time = datetime.datetime.now()
        target_time = current_time.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        time_difference = (target_time - current_time).total_seconds()
        await asyncio.sleep(time_difference - 1)

        top_users = cursor.execute("SELECT user, h24 FROM activity ORDER BY h24 DESC LIMIT 5").fetchall()

        embed = Embed(title="Топ 5 пользователей в голосовой активности:", color=Colour.green().from_rgb(16, 212, 235), timestamp=datetime.datetime.now())
        top_users_str = ""
        for idx, (user_id, activity) in enumerate(top_users, 1):
            user = bot.get_user(user_id)
            if user:
                formatted_time = await format_time(activity)
                top_users_str += f"{idx}) {user.mention} <:voice_leader:1146495799740600340> - {formatted_time}\n"
                guild = bot.get_guild(494212272353181726)
                role = guild.get_role(cfg['communication-leader-id'])
                if role:
                    member = guild.get_member(user_id)
                    if member:
                        await member.add_roles(role)

        embed.description = top_users_str
        channel = bot.get_channel(cfg['leaders-channel'])
        if channel:
            await channel.send(embed=embed)

async def remove_role_after_1_days():
    await bot.wait_until_ready()

    while not bot.is_closed():
        guild = bot.get_guild(494212272353181726)
        role = guild.get_role(cfg['communication-leader-id'])
        if role:
            for member in guild.members:
                if role in member.roles:
                    join_time = member.joined_at
                    if join_time:
                        join_time_naive = join_time.astimezone(pytz.utc).replace(tzinfo=None)
                        current_time = datetime.datetime.utcnow()
                        time_difference = current_time - join_time_naive
                        if time_difference >= datetime.timedelta(days = 1):
                            await member.remove_roles(role)

        current_time = datetime.datetime.now()
        target_time = current_time.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        time_difference = (target_time - current_time).total_seconds()
        await asyncio.sleep(time_difference - 2)