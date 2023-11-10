import discord
import asyncio
import datetime
import json
from bot import bot
from discord import Embed, Colour, PermissionOverwrite
from discord.ui import View, UserSelect, Select
from discord.utils import get
from data.postgresql import cursor

from .func import check_if_admin

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)


class LogInSelect(UserSelect):
    def __init__(self):
        super().__init__(placeholder="Выберите пользователя", min_values=1, max_values=1)

    async def callback(self, inter: discord.Interaction):
        if inter.user.voice is None:
            await inter.response.send_messages(
                f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)

        if self.values[0].voice is None or self.values[0].voice.channel != inter.user.voice.channel:
            await inter.user.voice.channel.set_permissions(self.values[0], connect=True, read_messages=True)

            notif = bot.get_channel(cfg['text']['invite-notif-channel'])

            em_connect = Embed(title="",
                               description=f"{self.values[0].mention}, вы были приглашены в канал {inter.user.voice.channel.mention}",
                               color=Colour.dark_embed(), timestamp=datetime.datetime.now())
            em_connect.set_author(name=f"{inter.user.name}",
                                  icon_url=f"{inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar.url}")
            em_connect.set_thumbnail(
                url=f"{self.values[0].avatar.url if self.values[0].avatar else self.values[0].default_avatar.url}")
            em_connect.set_footer(text=f"{inter.guild.name}", icon_url=f"{inter.guild.icon.url}")

            msg = await notif.send(embed=em_connect)

            await inter.response.send_message(f"Пользователь {self.values[0].mention} был приглашён {msg.jump_url}",
                                              ephemeral=True)
        else:
            await self.values[0].move_to(None)
            await inter.response.send_message(f"Пользователь {self.values[0].mention} был отключён с вашего канала",
                                              ephemeral=True)


class ChangeOwner(UserSelect):
    def __init__(self):
        super().__init__(placeholder="Выберите пользователя", min_values=1, max_values=1)

    async def callback(self, inter: discord.Interaction):
        if inter.user.voice is None:
            await inter.response.send_message(
                f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)

        elif self.values[0].voice is None or self.values[0].voice.channel != inter.user.voice.channel:
            await inter.response.send_message(
                f"Пользователь {self.values[0].mention} не находится в вашем голосовом канале", ephemeral=True)

        else:
            cursor.execute("UPDATE temp_channels SET owner = %s WHERE channel_id = %s",
                           (self.values[0].id, inter.user.voice.channel.id))

            await inter.response.send_message(
                f"Пользователь {self.values[0].mention} стал новым владельцем комнаты {inter.user.voice.channel.mention}",
                ephemeral=True)


class Voice(UserSelect):
    def __init__(self):
        super().__init__(placeholder="Выберите пользователя", min_values=1, max_values=1)

    async def callback(self, inter: discord.Interaction):
        if inter.user.voice is None:
            await inter.response.send_message(
                f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
            return

        if self.values[0].voice is None or self.values[0].voice.channel != inter.user.voice.channel:
            await inter.response.send_message(
                f"Пользователь {self.values[0].mention} не находится в вашем голосовом канале", ephemeral=True)
            return

        user_permissions = inter.channel.permissions_for(self.values[0])

        if user_permissions.speak is True:
            await inter.channel.set_permissions(self.values[0], speak=False)
            await inter.response.send_message(f"Пользователь {self.values[0].mention} был замьючен", ephemeral=True)
        elif user_permissions.speak is False:
            await inter.channel.set_permissions(self.values[0], speak=True)
            await inter.response.send_message(f"Пользователь {self.values[0].mention} был размьючен!", ephemeral=True)


class VoiceView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Voice())


class ChangeOwnerView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(ChangeOwner())


class LogInView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(LogInSelect())


class Wabloni(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Мой шаблон", emoji="<:Folder:1148749586068951080>",
                                 description="Применить собственный шаблон."),
            discord.SelectOption(label="Общение", emoji="<:Home:1119525501988515900>",
                                 description="10 участников, 128 кб/с, открытый канал."),
            discord.SelectOption(label="Кинотеатр", emoji="<:Chat:1119525505159401532>",
                                 description="50, говорит только создатель."),
            discord.SelectOption(label="Главные Админы", emoji="<:GL_Admin:1146487194081579030>",
                                 description="Неограниченный лимит, только для Главных админов"),
            discord.SelectOption(label="Зам Админы", emoji="<:Zam_Admin:1146487191757918338>",
                                 description="Неограниченный лимит, только для Зам Админов"),
            discord.SelectOption(label="Старшие Админы", emoji="<:St_Admin:1157048535506768027>",
                                 description="Неограниченный лимит, только для Старших админов"),
            discord.SelectOption(label="Админы", emoji="<:Admin:1146487184677933068>",
                                 description="Неограниченный лимит, только для Админов"),
        ]
        super().__init__(placeholder="Шаблоны каналов", min_values=1, max_values=1, options=options,
                         custom_id="Wabloni")

    async def callback(self, inter: discord.Interaction):
        category = get(inter.guild.categories, id=cfg['voices']['category'])

        async def wait_and_delete_channel(channel: discord.VoiceChannel):
            await asyncio.sleep(10)
            while len(channel.members) > 0:
                await asyncio.sleep(1)
            await channel.delete()

        if self.values[0] == "Общение":
            obzhenie = await inter.guild.create_voice_channel(name="Общение", category=category, bitrate=128000,
                                                              user_limit=10)
            await inter.response.send_message(
                f"Канал категории **Общение** создан: {obzhenie.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                ephemeral=True)
            await wait_and_delete_channel(obzhenie)

        elif self.values[0] == "Кинотеатр":
            kino = await inter.guild.create_voice_channel(name="Кинотеатр", user_limit=50, category=category,
                                                          bitrate=64000)
            await kino.set_permissions(inter.user, speak=True)
            await kino.set_permissions(inter.guild.default_role, speak=False)
            await inter.response.send_message(
                f"Канал категории **Кинотеатр** создан: {kino.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                ephemeral=True)
            await wait_and_delete_channel(kino)

        elif self.values[0] == "Мой шаблон":
            cursor.execute("SELECT * FROM patterns WHERE owner = %s", (inter.user.id,))
            patterns = cursor.fetchone()
            if patterns:
                pattern = await inter.guild.create_voice_channel(name=patterns[2], user_limit=patterns[3],
                                                                 category=category, bitrate=patterns[4])
                await inter.response.send_message(
                    f"Канал категории **Мой шаблон** создан: {pattern.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                    ephemeral=True)
                await wait_and_delete_channel(pattern)
            else:
                await inter.response.send_message("У вас ещё нет своего шаблона!", ephemeral=True)

        elif self.values[0] == "Главные Админы":
            if await check_if_admin(inter, inter.user, [1146225293997117450]) is True:
                gl_admin = get(inter.guild.roles, id=1146225293997117450)

                overwrites = {
                    gl_admin: PermissionOverwrite(read_messages=True, connect=True),
                    inter.guild.default_role: PermissionOverwrite(read_messages=True)}

                gl_admins = await inter.guild.create_voice_channel(name="Главный Админы", category=category,
                                                                   bitrate=128000, overwrites=overwrites)
                await inter.response.send_message(
                    f"Канал категории **Главные Админы** создан: {gl_admins.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                    ephemeral=True)
                await wait_and_delete_channel(gl_admins)

        elif self.values[0] == "Зам Админы":
            if await check_if_admin(inter, inter.user, [1146225328889536594]) is True:
                zam_admin = get(inter.guild.roles, id=1146225328889536594)

                overwrites = {
                    zam_admin: PermissionOverwrite(read_messages=True, connect=True),
                    inter.guild.default_role: PermissionOverwrite(read_messages=True)}

                zam_admins = await inter.guild.create_voice_channel(name="Зам Админы", category=category,
                                                                    bitrate=128000, overwrites=overwrites)
                await inter.response.send_message(
                    f"Канал категории **Зам Админы** создан: {zam_admins.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                    ephemeral=True)
                await wait_and_delete_channel(zam_admins)

        elif self.values[0] == "Старшие Админы":
            if await check_if_admin(inter, inter.user, [1146225443641495562]) is True:
                st_admin = get(inter.guild.roles, id=1146225443641495562)

                overwrites = {
                    st_admin: PermissionOverwrite(read_messages=True, connect=True),
                    inter.guild.default_role: PermissionOverwrite(read_messages=True)}

                st_admins = await inter.guild.create_voice_channel(name="Старшие Админы", category=category,
                                                                   bitrate=128000, overwrites=overwrites)
                await inter.response.send_message(
                    f"Канал категории **Старшие Админы** создан: {st_admins.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                    ephemeral=True)
                await wait_and_delete_channel(st_admins)

        elif self.values[0] == "Админы":
            if await check_if_admin(inter, inter.user, [1146225504190468187]) is True:
                admin = get(inter.guild.roles, id=1146225504190468187)

                overwrites = {
                    admin: PermissionOverwrite(read_messages=True, connect=True),
                    inter.guild.default_role: PermissionOverwrite(read_messages=True)}

                admins = await inter.guild.create_voice_channel(name="Админы", category=category, bitrate=128000,
                                                                overwrites=overwrites)
                await inter.response.send_message(
                    f"Канал категории **Админы** создан: {admins.mention}\n> Перейдите в канал в течении **10 секунд**, иначе он удалится!",
                    ephemeral=True)
                await wait_and_delete_channel(admins)


class Bitrate(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Низкое качество", description="24 кб/с"),
            discord.SelectOption(label="Среднее", description="64 кб/с - как в личных звонках"),
            discord.SelectOption(label="Хорошее", description="128 кб/с - Качество лучше личных звонков"),
            discord.SelectOption(label="Высокое", emoji="<:voice_leader:1146495799740600340>",
                                 description="256 кб/с - Доступно только лидерам общения"),
            discord.SelectOption(label="Наилучшее", emoji="<a:boost:1113257580970639421>",
                                 description="384 кб/с - Доступно только BOOSTER'ам"),
        ]
        super().__init__(placeholder="Качество звука", min_values=1, max_values=1, options=options, custom_id="Bitrate")

    async def callback(self, inter: discord.Interaction):
        boost_role = get(inter.guild.roles, id=853277261960577084)
        leader_voice = get(inter.guild.roles, id=1146253707768504370)
        user_voice = inter.user.voice

        if user_voice is None:
            await inter.response.send_message(
                f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
            return

        cursor.execute("SELECT owner FROM temp_channels WHERE owner = %s AND channel_id = %s",
                       (inter.user.id, user_voice.channel.id))
        owner = cursor.fetchone()

        if not owner:
            await inter.response.send_message(f"Вы не являетесь создателем комнаты!", ephemeral=True)
            return

        selected_option = self.values[0]

        if selected_option == "Низкое качество":
            bitrate = 26000
            await user_voice.channel.edit(bitrate=bitrate)
            await inter.response.send_message(f"Битрейт вашего канала изменён на {str(bitrate).replace('0', '')}кб/с",
                                              ephemeral=True)
        elif selected_option == "Среднее":
            bitrate = 64000
            await user_voice.channel.edit(bitrate=bitrate)
            await inter.response.send_message(f"Битрейт вашего канала изменён на {str(bitrate).replace('0', '')}кб/с",
                                              ephemeral=True)
        elif selected_option == "Хорошее":
            bitrate = 128000
            await user_voice.channel.edit(bitrate=bitrate)
            await inter.response.send_message(f"Битрейт вашего канала изменён на {str(bitrate).replace('0', '')}кб/с",
                                              ephemeral=True)
        elif selected_option == "Высокое":
            if leader_voice not in inter.user.roles:
                em_no_leader = Embed(title="Вы не Лидер Общения!",
                                     description=" Выдаётся самым активным пользователям за 24 часа каждый день.",
                                     color=Colour.from_rgb(0, 226, 241))
                em_no_leader.set_footer(text=f"{inter.guild.name}", icon_url=f"{inter.guild.icon.url}")
                await inter.response.send_message(embed=em_no_leader, ephemeral=True)
            else:
                bitrate = 256000
                await user_voice.channel.edit(bitrate=bitrate)
                await inter.response.send_message(
                    f"Битрейт вашего канала изменён на {str(bitrate).replace('0', '')}кб/с", ephemeral=True)
        elif selected_option == "Наилучшее":
            if boost_role not in inter.user.roles:
                em_no_boost = Embed(title="Вы не бустер сервера!",
                                    description="Для получения роли нужно [**передать бусты**](https://support.discord.com/hc/ru/articles/360028038352-%D0%A7%D0%B0%D0%92%D0%BE-%D0%BF%D0%BE-%D0%B1%D1%83%D1%81%D1%82%D0%B0%D0%BC-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%B0-) на INFINITY",
                                    color=Colour.magenta())
                em_no_boost.add_field(name="Привилегии и дополнительные возможности:",
                                      value=f"<a:dot:1113242361510772786> Роль {boost_role.mention} с дополнительными возможностями.\n<a:dot:1113242361510772786> Отображение отдельно от других участников<a:dot:1113242361510772786> 300.000:coin: экономической валюты Akemi\n<a:dot:1113242361510772786> Услуга VIP на 3 месяца.\nПодробнее: <#1146225235406884894>")
                em_no_boost.set_footer(icon_url=f"{inter.guild.icon.url}", text=f"{inter.guild.name}")
                await inter.response.send_message(embed=em_no_boost, ephemeral=True)
            else:
                bitrate = 384000
                await user_voice.channel.edit(bitrate=bitrate)
                await inter.response.send_message(
                    f"Битрейт вашего канала изменён на {str(bitrate).replace('0', '')}кб/с", ephemeral=True)
