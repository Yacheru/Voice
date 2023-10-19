import sys
sys.dont_write_bytecode = True
from bot import bot, TOKEN

from main.temp_voices import *
from main.voice_activity import command

bot.run(TOKEN)