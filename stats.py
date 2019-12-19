import discord
import asyncio
from collections import defaultdict

from discord.ext import commands
from discord.ext.commands import CommandNotFound

class Stats(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
#### Commands ####

	@commands.command(description='Génère les statistiques du serveur. La commande peut prendre en paramètre des mentions d\'utilisateurs ou de channels\nExemple : !stats @user1 @user2 #channel2 génèrera les statistiques du channel2 pour les user1 et user2.')
	async def stats(self, ctx):
		message = await ctx.send("Cette opération peut prendre de quelques secondes à quelques minutes.")
		
		users_mentions = ctx.message.mentions
		channels_mentions = ctx.message.channel_mentions
		# If no channels are mentionned, we take all text channels
		text_channels = ctx.guild.text_channels if not channels_mentions else channels_mentions
		
		embed = await self.stats_all(text_channels=text_channels, user=users_mentions, all=(not channels_mentions and not users_mentions))

		embed.set_thumbnail(url=ctx.guild.icon_url)
		
		await message.delete()
		await ctx.send(embed=embed)
		
#### Utilities functions ####

	async def stats_all(self, *, text_channels, user=[], all=False):
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