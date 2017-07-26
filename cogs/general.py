import random
import asyncio

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to load General cog. Check your discord.py installation.")

BOTNAMES = ["Agnes", "Alfred", "Archy", "Barty", "Benjamin", "Bertram",
	"Bruni", "Buster", "Edith", "Ester", "Flo", "Francis", "Francisco", "Gil",
	"Gob", "Gus", "Hank", "Harold", "Harriet", "Henry", "Jacques", "Jorge",
	"Juan", "Kitty", "Lionel", "Louie", "Lucille", "Lupe", "Mabel", "Maeby",
	"Marco", "Marta", "Maurice", "Maynard", "Mildred", "Monty", "Mordecai",
	"Morty", "Pablo", "Seymour", "Stan", "Tobias", "Vivian", "Walter", "Wilbur"]

class General:
	"""Name changing"""

	def __init__(self, bot):
		self.bot = bot

	async def set_nick(self, newnick):
		for server in self.bot.servers:
			await self.bot.change_nickname(server.me, "%s Bot" % newnick)

	def choose_nick(self):
		current_nick = list(self.bot.servers)[0].me.nick # Since the nickname should be the same for all servers, it shouldn't matter that self.bot.servers isn't always in the same order
		newnick = random.choice(BOTNAMES)
		while newnick == current_nick:
			newnick = random.choice(BOTNAMES) # Keep rerolling until we get a different name
		return newnick

	# Change nickname every 10 minutes
	async def change_nick(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			serverlist = list(self.bot.servers)
			if len(serverlist) > 0:
				await self.set_nick(self.choose_nick())
			await asyncio.sleep(self.bot.settings["changenick_interval"])

	async def on_server_join(self, server):
		await self.set_nick(self.choose_nick())

	@commands.command()
	async def changename(self):
		"""Chooses a random new nickname for the bot."""
		await self.bot.say("Too long have I endured this moniker. It is time to begin anew.")
		await self.set_nick(self.choose_nick())

	@commands.command()
	async def join(self):
		"""Displays a link where server owners can add this bot."""
		await self.bot.say("Another server? I am but a simple servant. %s" % self.bot.joinurl)

def setup(bot):
	general = General(bot)
	bot.add_cog(general)
	bot.loop.create_task(general.change_nick())
