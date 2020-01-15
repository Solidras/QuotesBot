import discord
import asyncio
import os
import random

import json
from urllib import request
from urllib.error import HTTPError

from discord.ext import commands
from discord.ext.commands import CommandNotFound

from shared import *

class Quotes(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
		self.BOT_TOKEN = os.getenv('BOT_TOKEN')
		self.WEBHOOK_URL = os.getenv('WEBHOOK_URL')
		self.WEBHOOK_ID = self.WEBHOOK_URL.split('/')[-1]
		
#### Commands ####

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return

		if message.content.startswith('/'):
			characters = await load_characters()
			content = message.content[1:]
			arg = content.split()
			if arg[0] in characters:
				await message.delete()
				await self.send_webhook_message(message, arg[0], ' '.join(arg[1:]) if len(arg) > 1 else '')
			# Command : character_all -> shows all quotes from this character
			elif arg[0][:-4] in characters and arg[0][-4:] == '_all':
				await self.show_all_quotes(message.channel, arg[0][:-4], ' '.join(arg[1:]) if len(arg) > 1 else '')
				
		#await self.bot.process_commands(message)
	
	@commands.command(description="Affiche la liste des personnages disponibles")
	async def characters(self, ctx):
		characters = await load_characters()
		embed = discord.Embed(title='Liste des personnages', type='rich', description='\n'.join([c.capitalize() for c in characters]), colour=discord.Color.dark_green())
		await ctx.send(embed=embed)
		await ctx.send('*Vous pouvez également ajouter un _all après le nom du personnage pour voir toutes les citations. La recherche par mot est également disponible avec le _all.*')	
			
	@commands.command(description='Permet d\'ajouter une citation à un personnage. Le premier paramètre est le personnage et les suivants sont la citation (sans "")')
	async def add(self, ctx, character, *, quote):
		characters = await load_characters()
		await ctx.message.delete()
		if character in characters:
			with open('quotes/' + character + '.txt', 'a') as f:
				f.write('#' + quote)
			await ctx.send(quote, delete_after = 5)
		else:
			await ctx.send("Le personnage n'existe pas.", delete_after = 5)	

	@commands.command(description='La commande prend 2 paramètres : un personnage et un lien vers une image de profil (de préference imgur) avec l\'extension jpg.')
	async def add_character(self, ctx, character, image_url):
		characters = await load_characters()
		character = character.lower()
		if character in characters:
			await ctx.send("Le personnage existe déjà.", delete_after = 5)
		else:
			with open('characters.txt', 'a') as f:
				f.write(character + ',' + image_url + '\n')
			f = open('quotes/' + character + '.txt', 'w+')
			
#### Utilities functions ####
		
	async def get_webhook(self, ctx):
		webhooks = await ctx.guild.webhooks()
		webhook = None
		for w in webhooks:
			if w.id == int(self.WEBHOOK_ID):
				webhook = w
				
		return webhook

	async def change_webhook_channel(self, id):
		payload = {
			'channel_id': str(id)
		}
		
		headers = {
			'Content-Type': 'application/json',
			'user-agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11',
			'Authorization': 'Bot ' + self.BOT_TOKEN
		}
		req = request.Request(url=self.WEBHOOK_URL,
						  data=json.dumps(payload).encode('utf-8'),
						  headers=headers,
						  method='PATCH')
						  
		response = request.urlopen(req)
		
	async def show_all_quotes(self, ctx, character, words=''):
		characters = await load_characters()
		character = character.lower()
		
		if not character in characters:
			character = characters[0]
			
		f = open('quotes/' + character + '.txt', 'r')
		quotes = f.read().split('#')
		f.close()
		
		#Remove empty string
		quotes = list(filter(lambda q : q != '', quotes))
		
		tmp = []
		for q in quotes:
			if words.lower() in q.lower():
				tmp.append(q)
		quotes = tmp
		nb_embed = ((sum(map(len, quotes)) + 4*len(quotes))//2048)+1
		c = 1
		
		while quotes:
			description=''
			while len(quotes[0]) + 4 >= 2048:
				del quotes[0]
			while len(description) + len(quotes[0]) + 4 < 2048:
				description += '- ' + quotes[0] + '\n'
				del quotes[0]
				if not quotes:
					break
				
			title = 'Citations de ' + character.capitalize() + ' ' + str(c) + '/' + str(nb_embed)
			embed = discord.Embed(title=title, description=description, type='rich')

			await ctx.send(embed=embed)
			c += 1

	async def random_quotes(self, character, words=''):
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

	async def send_webhook_message(self, ctx, character, words=''):
		characters = await load_characters()
			
		webhook = await self.get_webhook(ctx)
		if webhook != None and character in characters:
			await self.change_webhook_channel(ctx.channel.id)
			content = await self.random_quotes(character, words)
			await webhook.send(content=content, username=character.capitalize(), avatar_url=characters[character])
