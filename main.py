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

#Must be https://discordapp.com/api/webhooks/your_id with no token after the id
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_ID = WEBHOOK_URL.split('/')[-1]

bot = commands.Bot(command_prefix='!')


#### Commands ####

@bot.command(description="Affiche la liste des personnages disponibles")
async def characters(ctx):
	characters = await load_characters()
	embed = discord.Embed(title='Liste des personnages', type='rich', description='\n'.join([c.capitalize() for c in characters]), colour=discord.Color.dark_green())
	await ctx.send(embed=embed)
	
@bot.event
async def on_message(message):
	if message.author == bot.user:
		return

	if message.content.startswith('!'):
		characters = await load_characters()
		content = message.content[1:]
		arg = content.split()
		if arg[0] in characters:
			await message.delete()
			await send_webhook_message(message, arg[0], ' '.join(arg[1:]) if len(arg) > 1 else '')
			
	await bot.process_commands(message)
		
@bot.command(description='Permet d\'ajouter une citation à un personnage. Le premier paramètre est le personnage et les suivants sont la citation (sans "")')
async def add(ctx, character, *, quote):
	characters = await load_characters()
	await ctx.message.delete()
	if character in characters:
		quote = quote[0].upper() + quote[1:]
		with open('quotes/' + character + '.txt', 'a') as f:
			f.write('#' + quote)
		await ctx.send(quote, delete_after = 5)
	else:
		await ctx.send("Le personnage n'existe pas.", delete_after = 5)
		

@bot.command(description='La commande prend 2 paramètres : un personnage et un lien vers une image de profil (de préference imgur) avec l\'extension jpg.')
async def add_character(ctx, character, image_url):
	characters = await load_characters()
	character = character.lower()
	if character in characters:
		await ctx.send("Le personnage existe déjà.", delete_after = 5)
	else:
		with open('characters.txt', 'a') as f:
			f.write(character + ',' + image_url + '\n')
		f = open('quotes/' + character + '.txt', 'w+')
		
		

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
	if ctx.message.content.split()[0][1:] in characters:
		return
	raise error
	
@add.error
async def add_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		await ctx.send('Mooordu! Mooordu! Mordu mordu mordu mordu la ligne !!!!')
		

#### Utilities functions ####
			  
async def load_characters():
	c = {}
	f = open('characters.txt', 'r')
	for line in f.readlines():
		character,url = line.split(',')
		c[character] = url
	f.close()
	return c
	
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

async def random_quotes(character, words=''):
	characters = await load_characters()
	character = character.lower()
	
	if not character in characters:
		character = characters[0]
		
	f = open('quotes/' + character + '.txt', 'r')
	quotes = f.read().split('#')
	f.close()
	
	#Remove empty string
	quotes = list(filter(lambda q : q != '', quotes))
	
	#If a word is in more than 1 quote, it doesn't always be the same quote.
	random.shuffle(quotes)
	
	notFindText = ["Ouais, c'est pas faux.", "Non mais je connais pas ce mot là."]
	
	response = ''
	if not words:
		response = random.choice(quotes)
	else:
		for q in quotes:
			if words.lower() in q.lower():
				response = q
	if not response:
		response = random.choice(notFindText)

	return response

async def send_webhook_message(ctx, character, words=''):
	characters = await load_characters()
		
	webhook = await get_webhook(ctx)
	if webhook != None and character in characters:
		await change_webhook_channel(ctx.channel.id)
		content = await random_quotes(character, words)
		await webhook.send(content=content, username=character.capitalize(), avatar_url=characters[character])

bot.run(BOT_TOKEN)
