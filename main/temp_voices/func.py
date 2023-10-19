import discord
import json
import re
import datetime
from typing import List
from discord.utils import get, format_dt
from discord.ext import tasks
from discord import PermissionOverwrite
from data.postgresql import cursor
from bot import bot

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

onleave_channels = []

async def createProverkaChannel(member: discord.Member, category: discord.CategoryChannel):

    overwrites = {
        member.guild.default_role: PermissionOverwrite(read_messages = False)}

    new_channel = await member.guild.create_voice_channel(name=f"Проверка | {member.name}", category=category, user_limit=2, overwrites=overwrites)
    await member.move_to(new_channel)
    onleave_channels.append(new_channel.id)

    

async def createSupportChannel(member: discord.Member, category: discord.CategoryChannel):

    overwrites = {
        member: PermissionOverwrite(connect=True, create_instant_invite=True),
        member.guild.default_role: PermissionOverwrite(create_instant_invite=True)}

    new_channel = await member.guild.create_voice_channel(member.name, category=category, user_limit=2, overwrites=overwrites)
    await member.move_to(new_channel)
    onleave_channels.append(new_channel.id)

    cursor.execute("INSERT INTO temp_channels (owner, channel_id) VALUES (%s, %s)", (member.id, new_channel.id))



async def checkAfterChannels(member: discord.Member, after_channel: discord.VoiceChannel):
    if after_channel.id == cfg['voices']['create-voice']:
        await createSupportChannel(member, after_channel.category)

    elif after_channel.id == cfg['voices']['proverka-channel']:
        await createProverkaChannel(member, after_channel.category)



async def checkBeforeChannels(before_channel: discord.VoiceChannel):

    if before_channel.id in onleave_channels and len(bot.get_channel(before_channel.id).members) == 0:
        onleave_channels.remove(before_channel.id)

        await bot.get_channel(before_channel.id).delete()

        cursor.execute("DELETE FROM temp_channels WHERE channel_id = %s", (before_channel.id,))



async def checkChannels(member: discord.Member, before_channel: discord.VoiceChannel, after_channel: discord.VoiceChannel):

    if before_channel != None:
        await checkBeforeChannels(before_channel)

    if after_channel != None:
        await checkAfterChannels(member, after_channel)



def not_in_voice(inter: discord.Interaction):

    if inter.user.voice == None or inter.user.voice.channel not in inter.channel.category.voice_channels:
        return False



def not_owner(inter: discord.Interaction):

    cursor.execute("SELECT owner FROM temp_channels WHERE owner = %s", (inter.user.id,))
    owner = cursor.fetchone()

    if owner is None:
        return False



async def check_if_admin(inter: discord.Interaction, member: discord.Member, admin: List[int]):

    has_allowed_role = [role.id in admin for role in member.roles]

    if any(has_allowed_role) == True:
        return True
    else:
        return await inter.response.send_message(f"Вы не являетесь админом!", ephemeral=True)
    


async def mostActiveVoice(member: discord.Member):
    connect_time = datetime.datetime.now()

    if member.voice:
        cursor.execute("SELECT * FROM activity WHERE member = %s", (member.id,))
        existing_record = cursor.fetchone()

        if existing_record:
            cursor.execute("UPDATE activity SET connect_time = %s WHERE member = %s", (connect_time, member.id))
        else:
            cursor.execute("INSERT INTO activity (member, connect_time) VALUES (%s, %s)", (member.id, connect_time))

            
    else:
        cursor.execute("SELECT * FROM activity WHERE member = %s", (member.id,))
        existing_record = cursor.fetchone()

        if existing_record:
            connect_time = datetime.datetime.fromisoformat(str(existing_record[2]))
            left_time = datetime.datetime.now()
            time_spent = (left_time - connect_time).total_seconds()

            h24 = existing_record[3] + time_spent if existing_record[3] else time_spent
            d7 = existing_record[4] + time_spent if existing_record[4] else time_spent
            prev_all_time = existing_record[5] if existing_record[5] else 0

            cursor.execute("UPDATE activity SET h24 = %s, d7 = %s, all_time = %s WHERE member = %s", (h24, d7, prev_all_time + time_spent, member.id))


    
async def proverkaCheck(member: discord.Member, after: discord.VoiceState):
    category_id = 1146277232520736798
    excluded_channel_id = [1150461477300478003, 1146278913086066728]

    if after.channel and after.channel.category_id == category_id and after.channel.id not in excluded_channel_id:
        await after.channel.set_permissions(member, read_messages=True, send_messages=True)



async def teammate_search(member: discord.Member, after: discord.VoiceState):
    channels = [1162036232226865286, 1162036008737570896, 1162036043428667464, 1162036167139663902]
    if after.channel is not None:
        if after.channel.category_id == cfg['voices']['teammate-search-category-id'] and after.channel.id in channels:
            new_channel = await after.channel.category.create_voice_channel(name=f"{after.channel.name[2:]} | {member.name}", user_limit=after.channel.user_limit)
            await member.move_to(new_channel)
            onleave_channels.append(new_channel.id)



async def adminSessions(member: discord.Member, after: discord.VoiceState, before: discord.VoiceState):
    if isinstance(member, discord.Member) and not member.bot:
        channel_ids_to_check = [1156875426040389672, 1156875743503061012, 1156875973560647731, 1156876069455015946, 1156876268143386644, 1156876561006481428]

        is_in_channels_before = before.channel and before.channel.id in channel_ids_to_check
        is_in_channels_after = after.channel and after.channel.id in channel_ids_to_check

        if not is_in_channels_before and is_in_channels_after:
            cursor.execute("SELECT admin FROM adminsessions WHERE admin = %s", (member.id,))
            admin = cursor.fetchone()

            connect = format_dt(datetime.datetime.now(), style='R')

            if admin:
                cursor.execute("UPDATE adminsessions SET connect = %s WHERE admin = %s", (connect, admin[0],))
            else:
                cursor.execute("INSERT INTO adminsessions (admin, connect) VALUES (%s, %s)", (member.id, connect,))

        elif is_in_channels_before and not is_in_channels_after:
            cursor.execute("SELECT * FROM adminsessions WHERE admin = %s", (member.id,))
            admin = cursor.fetchone()

            now = format_dt(datetime.datetime.now(), style='R')

            entry_timestamp_match = re.search(r"<t:(\d+):R>", admin[2])
            exit_timestamp_match = re.search(r"<t:(\d+):R>", now)

            if entry_timestamp_match and exit_timestamp_match:
                entry_timestamp = int(entry_timestamp_match.group(1))
                exit_timestamp = int(exit_timestamp_match.group(1))

                entry_time = datetime.datetime.utcfromtimestamp(entry_timestamp)
                exit_time = datetime.datetime.utcfromtimestamp(exit_timestamp)

                time_difference = exit_time - entry_time


                hours = time_difference.total_seconds() // 3600
                remainder = time_difference.total_seconds() % 3600
                minutes = remainder // 60

                cursor.execute("UPDATE adminsessions SET all_time = %s WHERE admin = %s", (time_difference.total_seconds(), member.id))

            role_icon_mapper = {
                "Главный Админ": "<:GL_Admin:1146487194081579030>",
                "Зам Админ": "<:Zam_Admin:1146487191757918338>",
                "Старший Админ": "<:St_Admin:1157048535506768027>",
                "Админ": "<:Admin:1146487184677933068>"
            }

            try:
                role_icon = role_icon_mapper[member.roles[-1].name]
            except KeyError:
                role_icon = ' '

            embed = discord.Embed(title="Завершённая Сессия", description="", color=discord.Colour.blurple(), timestamp=datetime.datetime.now())
            embed.set_author(name=f"{member.name}", icon_url=f"{member.avatar.url if member.avatar else member.default_avatar.url}")
            embed.set_thumbnail(url=f"{member.avatar.url if member.avatar else member.default_avatar.url}")
            embed.add_field(name="Присоединился:", value=f"{admin[2]}", inline=True)
            embed.add_field(name="Вышел:", value=f"{now}", inline=True)
            embed.add_field(name="", value=f"- <:time:1157158683881525298> Всего провёл: **{int(hours)}** ч. **{int(minutes)}** мин.\n- <:ShieldDone:1157159384124751923> Админ: {member.mention}\n- <:voice:1157158687157276712> Канал: {before.channel.mention}\n- <:role:1157158688977600574> Роль: {member.roles[-1].mention} {role_icon}", inline=False)
            embed.set_footer(text=f"{member.guild.name}", icon_url=f"{member.guild.icon.url}")

            channel = bot.get_channel(1156875579698720830)
            await channel.send(embed=embed)
            
@tasks.loop(hours=24)
async def topadminsessions():
    cursor.execute("SELECT admin, all_time FROM adminsessions ORDER BY all_time DESC LIMIT 10")
    rows = cursor.fetchmany(10)

    topsessionchannel = bot.get_channel(1151547263953420318)
    guild = bot.get_guild(494212272353181726)

    role_icon_mapper = {
        "Главный Админ": "<:GL_Admin:1146487194081579030>",
        "Зам Админ": "<:Zam_Admin:1146487191757918338>",
        "Старший Админ": "<:St_Admin:1157048535506768027>",
        "Админ": "<:Admin:1146487184677933068>"
    }

    field_value = ""

    for i, all_time in enumerate(rows, start=1):
        hours = all_time[1] // 3600
        remainder = all_time[1] % 3600
        minutes = remainder // 60

        member = guild.get_member(all_time[0])

        try:
            role_icon = role_icon_mapper[member.roles[-1].name]
        except KeyError:
            role_icon = ' '

        field_value += f"{i}) {member.mention} {role_icon} **{hours}** ч. **{minutes}** мин.\n"

    embed = discord.Embed(title="Самые активные админы за 24 часа", color=discord.Colour.blurple(), timestamp=datetime.datetime.now())
    embed.add_field(name="", value=field_value)

    await topsessionchannel.send(embed = embed)

    cursor.execute("UPDATE adminsessions SET all_time = 0")