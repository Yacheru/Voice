import discord
import asyncio
import datetime
import time
import json
import logging
from bot import bot
from discord.ext import commands
from discord import Embed, Colour, ButtonStyle, PermissionOverwrite
from discord.ui import View, Button
from discord.utils import get

from data.postgresql import cursor
from .modals import NewNameChannel, NewLimitChannel
from .selectmenu import *
from .buttons import Patterns, DeletePattern
from .func import checkChannels, not_owner, not_in_voice, proverkaCheck, mostActiveVoice, adminSessions, teammate_search
from .utils import *


with open('main/temp_voices/icons.json', 'r', encoding='utf-8') as fa:
    icons = json.load(fa)

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):

    # await mostActiveVoice(member=member)
    await adminSessions(member=member, after=after, before=before)
    await checkChannels(member, before.channel, after.channel)
    await proverkaCheck(member=member, after=after)
    await teammate_search(member=member, after=after)

class Temp(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        last_button_usage = {}
        clicks = {}                            
        
        button = Button(label="", emoji=arrowup, style=ButtonStyle.gray, custom_id='ArrowUp')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return

            elif not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                if inter.user.voice.channel.user_limit == 99:
                    await inter.response.send_message("Лимит участников равен **99**. Вы не можете увеличить ещё!", ephemeral=True)
                else:
                    await inter.user.voice.channel.edit(user_limit = inter.user.voice.channel.user_limit + 1)
                    await inter.response.send_message("Успешно изменено!", ephemeral=True)
        button.callback = button_callback
            
        button = Button(label="", emoji=arrowdown, style=ButtonStyle.gray, row=1, custom_id='ArrowDown')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):

            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return

            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                if inter.user.voice.channel.user_limit == 0:
                    await inter.response.send_message("Лимит участников равен **0**. Вы не можете уменьшить ещё!", ephemeral=True)
                else:
                    await inter.user.voice.channel.edit(user_limit=inter.user.voice.channel.user_limit - 1)
                    await inter.response.send_message("Успешно изменено!", ephemeral=True)
        button.callback = button_callback
        
        button = Button(label="", emoji=show, style=ButtonStyle.gray, custom_id='Show')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):

            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return

            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                if inter.user.id not in clicks:
                    clicks[inter.user.id] = "first"

                if clicks[inter.user.id] == "first":
                    await inter.user.voice.channel.set_permissions(inter.guild.default_role, read_messages=False)
                    await inter.response.send_message("Ваш канал больше не отображается в списке каналов", ephemeral=True)
                    clicks[inter.user.id] = "second"

                elif clicks[inter.user.id] == "second":
                    await inter.user.voice.channel.set_permissions(inter.guild.default_role, read_messages=True)
                    await inter.response.send_message("Теперь ваш канал будет отображаться в списке каналов", ephemeral=True)
                    clicks[inter.user.id] = "first"
       
        button.callback = button_callback

        
        button = Button(label="", emoji=unlock, style=ButtonStyle.gray, custom_id='Unlock')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):            
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return

            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else: 
                if inter.user.id not in clicks:
                    clicks[inter.user.id] = "first"
                if clicks[inter.user.id] == "first":
                    await inter.user.voice.channel.set_permissions(inter.guild.default_role, connect = False)
                    await inter.response.send_message("Вы закрыли свой канал", ephemeral=True)
                    clicks[inter.user.id] = "second"
                elif clicks[inter.user.id] == "second":
                    await inter.user.voice.channel.set_permissions(inter.guild.default_role, connect = True)
                    await inter.response.send_message("Вы открыли свой канал", ephemeral = True)
                    clicks[inter.user.id] = "first"
        button.callback = button_callback

        
        button = Button(label="", emoji=login, style=ButtonStyle.gray, custom_id='Login')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                await inter.response.send_message(view=LogInView(), ephemeral=True)

        button.callback = button_callback

        
        button = Button(label="", emoji=voice, style=ButtonStyle.gray, custom_id='Voice')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else: 
                await inter.response.send_message(view=VoiceView(), ephemeral=True)

        button.callback = button_callback
        
        button = Button(label="", emoji=limit, style=ButtonStyle.gray, custom_id='Three_User')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):                                   
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
                
            else:
                await inter.response.send_modal(NewLimitChannel())
        button.callback = button_callback

        
        button = Button(label="", emoji=edit, style=ButtonStyle.gray, custom_id='Edit')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                last_usage_time = last_button_usage.get(inter.user.id, 0)
                current_time = time.time()

                if current_time - last_usage_time < 30:
                    await inter.response.send_message("Пожалуйста, подождите некоторое время перед повторным использованием кнопки.", ephemeral=True)
                else:
                    last_button_usage[inter.user.id] = current_time
                    await inter.response.send_modal(NewNameChannel())
        button.callback = button_callback
        

        button = Button(label="", emoji=star, style=ButtonStyle.gray, custom_id='Star')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):                                   
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            elif not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                await inter.response.send_message(view=ChangeOwnerView(), ephemeral=True)
        button.callback = button_callback

        
        button = Button(label="", emoji=settings, style=ButtonStyle.gray, custom_id='Setting')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return

            else:
                cursor.execute("SELECT owner FROM temp_channels WHERE channel_id = %s", (inter.user.voice.channel.id,))
                result = cursor.fetchone()

                owner = await bot.fetch_user(result[0])             
                    
                participants = [f"{i}) {user.mention} {star}" if result and user.id == result[0] else f"{i}) {user.mention}" for i, user in enumerate(inter.user.voice.channel.members, start=1)]
                    
                em_info = Embed(title=f"Информация о канале - {inter.user.voice.channel.name}", color=Colour.dark_embed(), timestamp=datetime.datetime.now())
                em_info.set_author(name=f"{inter.user.name}", icon_url=f"{inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar.url}")
                em_info.set_thumbnail(url=f"{inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar.url}")
                em_info.add_field(name="Настройки:", value=f"Название: **{inter.user.voice.channel.name}**\nЛимит участников: **{len(inter.user.voice.channel.members)}/{inter.user.voice.channel.user_limit if inter.user.voice.channel.user_limit != 0 else 'Без ограничений'}**\nБитрейт: **{inter.user.voice.channel.bitrate}**\nСоздатель: {owner.mention}", inline=False)
                em_info.add_field(name="Участники:", value="\n".join(participants), inline=False)
                em_info.set_footer(text=f"{inter.user.guild.name}", icon_url=f"{inter.user.guild.icon.url}")
                await inter.response.send_message(embed=em_info, ephemeral=True)          
        button.callback = button_callback


        button = Button(label="", emoji=folder, style=ButtonStyle.gray, custom_id='Folder')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):
            if not_in_voice(inter=inter) == False:
                await inter.response.send_message(f"Вы не находитесь в голосовом канале - <#{cfg['voices']['create-voice']}>", ephemeral=True)
                return
            
            if not_owner(inter=inter) == False:
                await inter.response.send_message("Вы не являетесь создателем комнаты!", ephemeral=True)
                return
            
            else:
                cursor.execute("SELECT * FROM patterns WHERE owner = %s", (inter.user.id,))
                patterns = cursor.fetchone()
                if patterns:
                    owner = bot.get_user(patterns[1])
                    em = Embed(title="Шаблоны", description=f"> **У вас уже создан шаблон, вы не можете создать ещё!**")
                    em.add_field(name="Настройки:", value=f"- Создатель: {owner.mention}\n- Название: **{patterns[2]}**\n- Лимит: **{patterns[3]}**\n- Битрейт: **{patterns[4]}кб/с**")
                    await inter.response.send_message(embed=em, view=DeletePattern(), ephemeral=True)
                else:
                    em = Embed(title="Создание шаблона", description="> **Создание своего шаблона!**")
                    em.add_field(name="Вы действительно хотите создать шаблон с такими настройками?", value=f"- Название: **{inter.user.voice.channel.name}**\n- Лимит: **{inter.user.voice.channel.user_limit}**\n- Битрейт: **{inter.user.voice.channel.bitrate}кб/с**")
                    await inter.response.send_message(embed=em, view=Patterns(), ephemeral=True)
        button.callback = button_callback

        
        button = Button(label="", emoji=filter, style=ButtonStyle.blurple, custom_id='Filter')
        self.add_item(button)
        async def button_callback(inter: discord.Interaction):                
            em_about_button = Embed(title="", description="### Подробности о каждом взаимодействии", color=Colour.dark_embed())
            em_about_button.add_field(name="О кнопках:", value=f"- {arrowdown} / {arrowup} - Данные кнопки изменяют лимит соответствующего канала на 1 в + или -.\n- {show} - Данная кнопка скрывает/показывает ваш канал в списке каналов\n- {unlock} - Данная кнопка открывает/скрывает ваш канал. Его видят, но не могут зайти.\n- {login} - Благодаря этой кнопке вы можете пригласить участника в канал или удалить с него\n- {voice} - Включить или выключить пользователю в вашей комнате микрофон.", inline=False)
            em_about_button.add_field(name="", value=f"- {limit} - Поможет вам изменить лимит участников канала до желаемого\n- {edit} - Используйте, если нужно изменить название своего канала\n- {star} - Вы можете передать владение каналом другому участнику.\n- {settings} - Узнать информацию о канале в котором вы находитесь.\n- {folder} - Создать свой шаблон.", inline=False)          
            em_about_button.add_field(name="Меню выбора:", value="Шаблоны каналов - создание каналов по шаблону. Нельзя изменить кнопками.\nКачество звука - Изменяет bitrate вашего канала. Чем больше - тем лучше!", inline = False)
            em_about_button.set_author(name=f"{inter.user.name}", icon_url=f"{inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar.url}")
            em_about_button.set_footer(text=f"{inter.guild.name} × {datetime.datetime.now().strftime('%H:%M %d/%m/%Y')}", icon_url=f"{inter.guild.icon.url}")
            await inter.response.send_message(embed = em_about_button, ephemeral=True)
        button.callback = button_callback
        
        self.add_item(Wabloni())
        self.add_item(Bitrate())

@bot.command(name="temp")
@commands.has_permissions(administrator = True)
async def temp(ctx: commands.Context):
    await ctx.channel.purge(limit = 1)

    em_temp_img = Embed(title="", color=Colour.from_rgb(235, 192, 52))
    em_temp_img.set_image(url="https://cdn.discordapp.com/attachments/1129601347352809532/1159560783429111838/195fa6c7da1d6a2e.png")

    em_temp = Embed(
        title="", 
        description=f"Это приватные комнаты, которые создаются при входе в триггерный канал и удаляются, если в них нет участников.\n\n<#{cfg['voices']['create-voice']}>\nИзменяйте конфигурацию вашей комнаты благодаря кнопкам ниже. Изменяйте лимит - {limit}, Закрывайте/Открывайте канал кнопками - {unlock} и многое другое. Подробнее по кнопке {filter}",
        color=Colour.from_rgb(235, 192, 52))
    em_temp.set_author(name="Приватные комнаты", icon_url=f"{clock}")
    em_temp.set_image(url="https://cdn.discordapp.com/attachments/1129601347352809532/1150299828098707487/yacherumade.png")
    em_temp.set_footer(text="Присоединитесь к голосовому каналу для взаимодействия с кнопками")
    await ctx.send(embeds= [em_temp_img, em_temp], view=Temp())