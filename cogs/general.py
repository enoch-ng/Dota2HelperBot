import random
import asyncio

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to load General cog. Check your discord.py installation.")

NAME = "Nova"
PERMERR = "You do not have the required permissions for this command."

class General:
	"""General features that don't have anything to do with Dota."""

	def __init__(self, bot):
		self.bot = bot

	async def unset_nick(self, server):
		try:
			await self.bot.change_nickname(server.me, None)
		except discord.Forbidden:
			pass

	@commands.command(pass_context = True)
	async def globalnickreset(self, ctx):
		"""Resets the bot's nickname in all servers.

		Can only be used by the bot owner."""
		if self.bot.is_owner(ctx.message.author):
			if self.bot.settings["verbose"]:
				print("Performing global nickname reset!")

			serverlist = list(self.bot.servers)
			for server in serverlist:
				await self.unset_nick(server)

			await self.bot.say("Successfully reset nickname.")
		else:
			await self.bot.say(PERMERR)

	@commands.command(pass_context = True)
	async def usernamereset(self, ctx):
		"""Resets the bot's username.

		Can only be used by the bot owner."""
		if self.bot.is_owner(ctx.message.author):
			if self.bot.settings["verbose"]:
				print("Performing username reset!")

			try:
				await self.bot.edit_profile(username = NAME)
			except HTTPException:
				await self.bot.say("Could not reset username due to a problem on Discord's end.")

			await self.bot.say("Successfully reset username.")
		else:
			await self.bot.say(PERMERR)

	@commands.command()
	async def join(self):
		"""Displays a link where server owners can add this bot."""
		await self.bot.say("Another server? I am but a simple servant. %s" % self.bot.joinurl)

	@commands.command(pass_context = True)
	async def faq(self, ctx):
		"""Displays a basic FAQ."""
		emb = discord.Embed()
		emb.set_author(name = "Frequently Asked Questions")
		emb.add_field(name = "Nova? Like the cat?", value = "Yes, like the cat.")
		emb.add_field(name = "Why am I not getting updates for matches?", value = "Make sure a channel is set through the `%smatchchannel` command. Also, make sure you've given the bot permissions to talk in that channel." % self.bot.get_prefix())
		emb.add_field(name = "Will you periodically add new leagues to the bot?", value = "I will on my instance of the bot. If you're running your own instance of the bot, you'll have to add new leagues through the `%saddleague` command or by editing the settings.json file." % self.bot.get_prefix())
		emb.add_field(name = "How do I find out what ID a tournament comes under?", value = "You can get league IDs by calling Valve's API (https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v1/?key=YOUR_API_KEY).")
		emb.set_footer(text = "Join the official Nova development server at https://discord.gg/A9mJdxn")

		try:
			await self.bot.say(embed = emb)
		except discord.HTTPException:
			await self.bot.say("I need the \"Embed Links\" permission first.")

def setup(bot):
	general = General(bot)
	bot.add_cog(general)
