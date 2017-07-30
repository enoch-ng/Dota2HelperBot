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
WELCOME_CHANNEL_NOT_FOUND = "I wish to post in the designated channel for welcome messages but am unable to, for I lack the required permissions (or else the channel does not exist)."

class General:
	"""General features, including automatic name changing and welcome messages"""

	def __init__(self, bot):
		self.bot = bot

	async def set_nick(self, newnick):
		self.bot.nick = newnick

		serverlist = list(self.bot.servers)
		for server in serverlist:
			try:
				if self.bot.server_settings_list[server.id]["auto_change_nick"]:
					await self.bot.change_nickname(server.me, "%s Bot" % newnick)
			except (discord.Forbidden, KeyError):
				pass

	async def unset_nick(self, server):
		try:
			await self.bot.change_nickname(server.me, None)
		except discord.Forbidden:
			pass

	def choose_nick(self):
		newnick = random.choice(BOTNAMES)
		while newnick == self.bot.nick:
			newnick = random.choice(BOTNAMES) # Keep rerolling until we get a different name
		return newnick

	def welcome_channel(self, server):
		return self.bot.server_settings_list[server.id]["welcome_channel"]

	def welcome_messages(self, server):
		return self.bot.server_settings_list[server.id]["welcome_messages"]

	def auto_change_nick(self, server):
		return self.bot.server_settings_list[server.id]["auto_change_nick"]

	def set_welcome_channel(self, server, channel):
		self.bot.server_settings_list[server.id]["welcome_channel"] = channel.id
		self.bot.save_server_settings()

	def set_welcome_messages(self, server, option):
		self.bot.server_settings_list[server.id]["welcome_messages"] = option
		self.bot.save_server_settings()

	def set_auto_change_nick(self, server, option):
		self.bot.server_settings_list[server.id]["auto_change_nick"] = option
		self.bot.save_server_settings()

	async def say_welcome_channel(self, server, msg):
		welcome_channel = self.bot.server_settings_list[server.id]["welcome_channel"]
		if welcome_channel:
			try:
				await self.bot.send_message(self.bot.get_channel(welcome_channel), msg)
			except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
				await self.bot.send_message(server.default_channel, WELCOME_CHANNEL_NOT_FOUND)
		else:
			await self.bot.send_message(server.default_channel, msg)

	# As auto_change_nick is now off by default, there is no need for an on_server_join() method

	async def on_member_join(self, member):
		serv = member.server
		if self.bot.server_settings_list[serv.id]["welcome_messages"]:
			await self.say_welcome_channel(serv, "%s has joined the server. Welcome!" % member.mention)

	# Change nickname every so often
	async def change_nick(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			serverlist = list(self.bot.servers)
			if len(serverlist) > 0:
				await self.set_nick(self.choose_nick())
			await asyncio.sleep(self.bot.settings["changenick_interval"])

	@commands.command(pass_context = True)
	async def globalnamereset(self, ctx):
		"""Resets the bot's nickname in all servers.

		Can only be used by the bot owner. This command should rarely be used."""
		await self.bot.edit_profile(username = "Dota 2 Helper Bot")

		if self.bot.is_owner(ctx.message.author):
			serverlist = list(self.bot.servers)
			for server in serverlist:
				await self.unset_nick(server)

			await self.bot.say("It is finished. Now others shall know me as I truly am.")
			if self.bot.settings["verbose"]:
				print("Performing global nickname reset!")

		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def welcomechannel(self, ctx, channel = None):
		"""Sets the channel for posting welcome messages.

		When used without an argument, shows current setting. Otherwise, accepts a channel mention, a channel name, or a channel ID."""
		server = ctx.message.server # As no_pm is true here, I am assuming server cannot be None
		if not channel:
			chsetting = self.bot.get_channel(self.welcome_channel(server))
			ch = server.default_channel if chsetting is None else chsetting
			await self.bot.say("%s is currently the designated channel for welcome messages." % ch.mention)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				for ch in server.channels:
					if ch.mention == channel or ch.name == channel or ch.id == channel:
						if ch.type == discord.ChannelType.text:
							self.set_welcome_channel(server, ch)
							await self.bot.say("%s is now the designated channel for welcome messages." % ch.mention)
							return
						else:
							await self.bot.say("That channel cannot be used for such purposes.")
							return
				await self.bot.say("Alas, I know of no such channel.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def welcome(self, ctx, option = None):
		"""Turns the welcome messages on or off.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn welcome messages off. Anything else turns it on."""
		server = ctx.message.server
		if not option:
			wmstate = "enabled" if self.welcome_messages(server) else "disabled"
			await self.bot.say("Welcome messages are currently %s." % wmstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if option == "off" or option == "no" or option == "false":
					self.set_welcome_messages(server, False)
					await self.bot.say("Welcome messages are now disabled.")
				else:
					self.set_welcome_messages(server, True)
					await self.bot.say("Welcome messages are now enabled.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def autochangename(self, ctx, option = None):
		"""Turns the nickname changing feature on or off.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn the nickname changing off. Anything else turns it on. Setting this option to false will also reset the bot's nickname."""
		server = ctx.message.server
		if not option:
			rcnstate = "enabled" if self.auto_change_nick(server) else "disabled"
			await self.bot.say("Automatic nickname changing is currently %s." % rcnstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if option == "off" or option == "no" or option == "false":
					self.set_auto_change_nick(server, False)
					await self.unset_nick(server)
					await self.bot.say("Automatic nickname changing is now disabled.")
				else:
					self.set_auto_change_nick(server, True)
					await self.set_nick(self.choose_nick())
					await self.bot.say("Automatic nickname changing is now enabled.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def changename(self, ctx):
		"""Chooses a random new nickname for the bot (5s cooldown).

		Is not affected by Octarine Core, Refresher Orb, Rearm, or cooldown reduction talents."""
		if self.auto_change_nick(ctx.message.server):
			await self.bot.say("Too long have I endured this moniker. It is time to begin anew.")
			await self.set_nick(self.choose_nick())
		else:
			await self.bot.say("The automatic name changing setting is off. Type `%sautochangename on` to enable it." % self.bot.get_prefix())

	@commands.command()
	async def join(self):
		"""Displays a link where server owners can add this bot."""
		await self.bot.say("Another server? I am but a simple servant. %s" % self.bot.joinurl)

	@commands.command(pass_context = True)
	async def faq(self, ctx):
		"""Displays a basic FAQ."""
		emb = discord.Embed()
		emb.set_author(name = "Frequently Asked Questions")
		emb.add_field(name = "What's with the nicknames? Can I set my own nickname for the bot?", value = "If the `autochangename` setting is on, the bot will automatically change its name periodically the name of a random Dota 2 bot. To set your own nickname for the bot, disable `autochangename` and then right-click the bot and select \"Change Nickname\".")
		emb.add_field(name = "Is The International already on the bot's list or do I need to add it?", value = "It should already be there if you're using my instance of the bot. You can check by looking for \"5401\" in the `%sleagues` command." % self.bot.get_prefix())
		emb.add_field(name = "Will you periodically add new leagues to the bot?", value = "I will on my instance of the bot. If you're running your own instance of the bot, you'll have to add new leagues through the `%saddleague` command." % self.bot.get_prefix())
		emb.add_field(name = "How do I find out what ID a tournament comes under?", value = "You can get league IDs by calling Valve's API (https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v1/?key=YOUR_API_KEY). In the future I hope to have some way to let people know the league IDs of upcoming tournaments more easily.")

		try:
			await self.bot.say(embed = emb)
		except discord.HTTPException:
			await self.bot.say("I require the \"Embed Links\" permission first.")

	@commands.command(pass_context = True)
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def contact(self, ctx, *, message):
		"""Sends a message to the bot owner (60s cooldown).

		Is not affected by Octarine Core, Refresher Orb, Rearm, or cooldown reduction talents."""
		try:
			owner = await self.bot.get_owner()
		except discord.NotFound:
			await self.bot.say("Alas, I know not who my owner is.")
			return

		author = ctx.message.author
		emb = discord.Embed(description = message)
		emb.set_author(name = "Message from %s" % author)

		try:
			await self.bot.send_message(owner, embed = emb)
		except discord.InvalidArgument:
			await self.bot.say("Alas, I know not where my owner is.")
		except discord.HTTPException:
			await self.bot.say("Alas, I could not deliver your message. Perhaps it is too long?")
		except:
			await self.bot.say("Alas, for reasons yet unknown to me, I could not deliver your message.")
		else:
			await self.bot.say("I have delivered your message with utmost haste! I pray it should arrive safely.")

def setup(bot):
	general = General(bot)
	bot.add_cog(general)
	bot.loop.create_task(general.change_nick())
