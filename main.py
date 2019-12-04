#https://discordapp.com/oauth2/authorize?client_id=642184501245640704&permissions=2080894066&scope=bot

import os
import asyncio
import discord
import random
import datetime
from collections import defaultdict

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
		
@bot.command(description='Génère les statistiques du serveur. La commande peut prendre en paramètre des mentions d\'utilisateurs ou de channels\nExemple : !stats @user1 @user2 #channel2 génèrera les statistiques du channel2 pour les user1 et user2.')
async def stats(ctx):
	
	message = await ctx.send("Cette opération peut prendre de quelques secondes à quelques minutes.")
	
	users_mentions = ctx.message.mentions
	channels_mentions = ctx.message.channel_mentions
	# If no channels are mentionned, we take all text channels
	text_channels = ctx.guild.text_channels if not channels_mentions else channels_mentions
	
	embed = await stats_all(text_channels=text_channels, user=users_mentions, all=(not channels_mentions and not users_mentions))

	embed.set_thumbnail(url=ctx.guild.icon_url)
	
	await message.delete()
	await ctx.send(embed=embed)

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
	elif isinstance(error, commands.CommandNotFound):
		await ctx.send('La commande n\'existe pas.', delete_after=3)
		return
	raise error
	
@add.error
async def add_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		await ctx.send('Mooordu! Mooordu! Mordu mordu mordu mordu la ligne !!!!')
	

#### Utilities functions ####

async def stats_all(*, text_channels, user=[], all=False):
	msg_by_person = defaultdict(lambda: 0)
	msg_by_channel = defaultdict(lambda: 0)
	reactions = defaultdict(lambda: 0)
	
	for channel in text_channels:
		async for message in channel.history(limit=None):
			if (not user or message.author in user) and not message.author.bot:
				msg_by_person[message.author] += 1
				msg_by_channel[channel] += 1
			
			#Emoji are calculated per user. If a user is given, it count the most used reaction by this user.
			msg_reaction = message.reactions
			for reaction in msg_reaction:
				async for u in reaction.users():
					if (not user or u in user):
						reactions[reaction.emoji] += reaction.count
	
	#Sort to find most actives channels/users/reactions
	msg_by_person = sorted(msg_by_person.items(), key=lambda kv: kv[1], reverse=True)
	msg_by_channel = sorted(msg_by_channel.items(), key=lambda kv: kv[1], reverse=True)
	reactions = sorted(reactions.items(), key=lambda kv: kv[1], reverse=True)

	embed = discord.Embed(title='Statistiques du serveur', type='rich')
	
	total_msg = sum([u[1] for u in msg_by_person])
	
	#If we have at least one user mention (not user == no users specified)
	if all or not user or len(user) > 1:
		most_active_users = ''
		for i in range(min(len(msg_by_person), 10)):
			most_active_users += msg_by_person[i][0].mention + ' : ' + str(msg_by_person[i][1]) + ' m. (' + str(round(100*msg_by_person[i][1]/total_msg)) + '%)\n'
		
		embed.add_field(name='Membres les plus actifs', value=most_active_users, inline=True)
	
	if all or len(text_channels) > 1:
		most_active_channels = ''
		for i in range(min(len(msg_by_channel), 10)):
			most_active_channels += msg_by_channel[i][0].mention + ' : ' + str(msg_by_channel[i][1]) + ' m. (' + str(round(100*msg_by_channel[i][1]/total_msg)) + '%)\n'
		
		embed.add_field(name='Channels les plus actifs', value=most_active_channels, inline=True)
		
	most_used_reactions = ''
	for i in range(min(len(reactions), 10)):
		most_used_reactions += str(reactions[i][1]) + ' ' + str(reactions[i][0]) + '\n'
	if most_used_reactions:
		embed.add_field(name='Réactions les plus utilisées', value=most_used_reactions, inline=True)
	
	embed.add_field(name='Total des messages', value=str(total_msg) + ' m.', inline=True)
	
	footer_text = 'Ces statistiques ont été générées pour '
	if all:
		footer_text += 'l\'ensemble du serveur.'
	elif user:
		footer_text += '{0} dans les channels {1}.'.format(', '.join([u[0].name for u in msg_by_person]), ', '.join([c[0].name for c in msg_by_channel]))
	else:
		footer_text += 'les channels {0}.'.format(', '.join([c[0].name for c in msg_by_channel]))
	
	embed.set_footer(text=footer_text)
	
	return embed
			  
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
		
async def update_hour_nickname():
	while not bot.is_closed:
		with open('ressources/hour', 'r') as f:
			line = f.readline()
			while line:
				member, hour = line.split(',')
				
				guild = discord.utils.get(bot.guilds, id=550631040826343427)

				if guild is not None:
					member = guild.get_member_named(member)
					nickname = member.nick.split('(')[0][:-1]
					hour = datetime.datetime.now() + datetime.timedelta(hours=int(hour))
					new_nick = nickname + ' (' + str(hour.hour) + 'h)'
					
					await member.edit(nick=new_nick)
				
				line = f.readline()
		await asyncio.sleep(3600)
			
bot.loop.create_task(update_hour_nickname())
bot.run(BOT_TOKEN)
