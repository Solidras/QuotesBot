#https://discordapp.com/api/oauth2/authorize?client_id=550628745816440842&permissions=2080894066&scope=bot

import os
import asyncio
import discord
import random

import json
from urllib import request
from urllib.error import HTTPError

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_ID = os.getenv('WEBHOOK_ID')

bot = commands.Bot(command_prefix='!')

characters = {'perceval': 'https://cdn.discordapp.com/attachments/550631040826343431/642161266286264320/perceval.jpg',
			  'loth':'https://i.imgur.com/0KSpe7H.jpg'}
				#'loth', 'leodagan', 'merlin', 'roi_burgonde', 'karadoc', 'arthur', 'kadoc', 'seli', 'yvain', 'bohort']

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
async def get_webhook(ctx):
	webhooks = await ctx.guild.webhooks()
	webhook = None
	for w in webhooks:
		if w.id == int(WEBHOOK_ID):
			webhook = w
			
	return webhook

async def change_webhook_channel(id):
	payload = {
		'channel_id': str(id)
	}
	
	headers = {
		'Content-Type': 'application/json',
		'user-agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11',
		'Authorization': 'Bot ' + BOT_TOKEN
	}
	req = request.Request(url=WEBHOOK_URL,
                      data=json.dumps(payload).encode('utf-8'),
                      headers=headers,
                      method='PATCH')
					  
	response = request.urlopen(req)

async def random_quotes(character):
	character = character.lower()
	
	if not character in characters:
		character = characters[0]
		
	f = open('quotes/' + character + '.txt', 'r')
	quotes = f.read().split('#')
	f.close()

	response = random.choice(quotes)
	return response

async def send_webhook_message(ctx, character):
	webhook = await get_webhook(ctx)
	if webhook != None:
		await change_webhook_channel(ctx.channel.id)
		content = await random_quotes(character)
		await webhook.send(content=content, username=character.capitalize(), avatar_url=characters[character])
	

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return

	if message.content.startswith('!'):
		content = message.content[1:]
		arg = content.split()
		if arg[0] in characters:
			await message.delete()
			await send_webhook_message(message, arg[0])
			
	await bot.process_commands(message)

bot.run(BOT_TOKEN)
