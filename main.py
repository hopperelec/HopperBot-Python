from time import time; starttime = time(); starttime = time()
import discord
from dotenv import load_dotenv
from os import getenv
from discord.ext import commands
from common import Common

from logging import getLogger,INFO,FileHandler
logger = getLogger('discord')
logger.setLevel(INFO)
logger.addHandler(FileHandler(filename='discord.log',encoding='utf-8',mode='a'))

intents = discord.Intents.default()
intents.members = True; intents.presences = True
bot = commands.Bot(command_prefix=["!","?","$","£","&","/","~"],intents=intents,case_insensitive=True)
bot.remove_command('help')
bot.main = Common(bot)
bot.starttime = starttime

bot.extensiontime = time()
for extension in bot.main.config["enabled_extensions"]:
    bot.load_extension("Cogs."+extension)
for addon,config in bot.main.config["enabled_addons"].items():
    if not config["parent"] in bot.main.config["enabled_extensions"]:
        print("Addon",addon,"has been enabled but not it's parent",config["parent"],"so will not be used")

load_dotenv()
bot.run(getenv("TOKEN"),reconnect=True)
