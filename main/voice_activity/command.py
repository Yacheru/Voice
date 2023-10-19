import discord
import datetime
import json
from discord import app_commands, Embed
from bot import bot
from data.postgresql import cursor

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

@bot.tree.command(name="voice", description="Проверить голосовую активность")
@app_commands.guild_only()
async def voice(inter: discord.Interaction):
    cursor.execute('SELECT h24, d7, all_time FROM activity WHERE member = %s', (inter.user.id,))
    result = cursor.fetchone()

    if result:
        # Всё время:
        all_hours = int(result[2] // 3600)
        all_minutes = int(result[2] % 3600) // 60
        # 7 Дней:
        seven_hours = int(result[1] // 3600)
        seven_minutes = int(result[1] % 3600) // 60
        # 24 Часа:
        day_hours = int(result[0] // 3600)
        day_minutes = int(result[0] % 3600) // 60

        em_voice = Embed(title="", description=f"### Пользователь – {inter.user.mention}", color=discord.Colour.dark_theme(), timestamp=datetime.datetime.now())
        em_voice.add_field(name="> За всё время:", value=f"```{all_hours} ч. {all_minutes} мин.```", inline=True)
        em_voice.add_field(name="> За 7 Дней:", value=f"```{seven_hours} ч. {seven_minutes} мин.```", inline=True)
        em_voice.add_field(name="> За 24 часа:", value=f"```{day_hours} ч. {day_minutes} мин.```", inline=True)
        em_voice.set_thumbnail(url=f"{inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar}")
        em_voice.set_footer(text=f"{inter.guild.name}", icon_url=f"{inter.guild.icon.url}")
        await inter.response.send_message(embed=em_voice, ephemeral=True)
    else:
        await inter.response.send_message(f"Не найден в базе данных голосовой активности", ephemeral=True)