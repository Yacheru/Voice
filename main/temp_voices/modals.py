import discord
from discord import TextStyle, Embed, Colour
from discord.ui import Modal, TextInput


class NewNameChannel(Modal, title="Изменить название"):
    new_name = TextInput(label="Новое название", placeholder="Введите новое название вашего канала",
                         style=TextStyle.short, max_length=99)

    async def on_submit(self, inter: discord.Interaction):
        await inter.user.voice.channel.edit(name=f"{self.new_name.value}")

        em_name = Embed(title="", description=f"Успешно изменено на: **{self.new_name.value}**",
                        color=Colour.dark_embed())

        await inter.response.send_message(embed=em_name, ephemeral=True)


class NewLimitChannel(Modal, title="Изменить лимит"):
    new_limit = TextInput(label="Новое значение", placeholder="0-99", style=TextStyle.short, max_length=2)

    async def on_submit(self, inter: discord.Interaction):
        try:
            await inter.user.voice.channel.edit(user_limit=f"{self.new_limit.value}")
            em_limit = Embed(title="", description=f"Успешно изменено на: **{self.new_limit.value}**",
                             color=Colour.dark_embed())
            await inter.response.send_message(embed=em_limit, ephemeral=True)
        except discord.errors.HTTPException as e:
            if e.status == 400 and e.code == 50035 and 'user_limit' in str(e):
                await inter.response.send_message("Укажите целочисленное значение!> `от 0 до 99`", ephemeral=True)
