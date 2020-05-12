import discord
import asyncio
import requests

from discord.ext import commands
from discord.ext.commands import CommandNotFound

class Urban(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
#### Commands ####

	@commands.command(aliases=['urban'], description='Cherche les mots ou l\'abréviation demandés sur le site UrbanDictionnary.')
	async def claudio_translator(self, ctx, *, words):
#		await ctx.message.delete()
		
		url = 'http://api.urbandictionary.com/v0/define?term=' + words
		res = requests.get(url).json()["list"]
		
		embed = discord.Embed(title=words, type='rich')
		embed.set_footer(text="Définition(s) provenant de UrbanDictionnary.")
		
		if(not res):
			embed.description = "No result found."
		else:
			# Add maximum of 6 definitions
			i = 1
			for d in res:
				embed.add_field(name='Définition '+str(i), value=d["definition"], inline=True)
				i+=1
				if i >= 6:
					break
			
		
		await ctx.send(embed=embed)

