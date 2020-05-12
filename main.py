#https://discordapp.com/oauth2/authorize?client_id=642184501245640704&permissions=2080894066&scope=bot

import os
import asyncio
import discord
import datetime

from discord.ext import commands
from dotenv import load_dotenv

from quotes import Quotes
from stats import Stats
from urban import Urban
from shared import *

load_dotenv()

#Must be https://discordapp.com/api/webhooks/your_id with no token after the id
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_ID = WEBHOOK_URL.split('/')[-1]

bot = commands.Bot(command_prefix='/')
bot.add_cog(Quotes(bot))
bot.add_cog(Stats(bot))
bot.add_cog(Urban(bot))

#### Bot event handlers ####

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
@bot.event
async def on_command_error(ctx, error):
	characters = await load_characters()
	if ctx.message.content.split()[0][1:] in characters or ctx.message.content.split()[0][1:][:-4] in characters:
		return
	elif isinstance(error, commands.CommandNotFound):
		await ctx.send('La commande n\'existe pas.', delete_after=3)
		return
	raise error
	
@bot.command()
async def ping(ctx):
	await ctx.message.delete()
	await ctx.send('Yup, I\'m awake.', delete_after=5)

	
#### Utilities functions ####


bot.run(BOT_TOKEN)
