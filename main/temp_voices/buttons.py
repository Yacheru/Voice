import discord
from discord.ui import View, Button
from data.postgresql import cursor


class Patterns(View):
    def __init__(self):
        super().__init__(timeout=None)

        button = Button(style=discord.ButtonStyle.green, label="Да")
        self.add_item(button)

        async def button_callback(inter: discord.Interaction):
            cursor.execute("INSERT INTO patterns (owner, name, ulimit, bitrate) VALUES (%s, %s, %s, %s)", (
                inter.user.id, inter.user.voice.channel.name, inter.user.voice.channel.user_limit,
                inter.user.voice.channel.bitrate,))
            await inter.response.send_message("Ваш шаблон успешно создан!", ephemeral=True)

        button.callback = button_callback


class DeletePattern(View):
    def __init__(self):
        super().__init__(timeout=None)

        button = Button(style=discord.ButtonStyle.red, label="Удалить")
        self.add_item(button)

        async def button_callback(inter: discord.Interaction):
            cursor.execute("DELETE FROM patterns WHERE owner = %s", (inter.user.id,))
            await inter.response.send_message("Ваш шаблон успешно удалён!", ephemeral=True)

        button.callback = button_callback
