# Dota2HelperBot, a Discord bot created by Blanedale

import random
import asyncio
import json

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to start Dota2HelperBot. Check your discord.py installation.")

DESC = "Dota2HelperBot, a Discord bot created by Blanedale"
BOT_DEFAULTS = {
	"token": "",
	"prefix": ";",
	"owner": "",
	"changenick_interval": 600,
	"api_interval": 20,
	"apikey": "",
	"filter_matches": True,
	"notable_leagues": [],
	"filter_generic": True,
	"no_repeat_matches": True,
	"save_match_data": False,
	"verbose": True
}
SERVER_DEFAULTS = {
	"welcome_channel": "",
	"matches_channel": "",
	"welcome_messages": False,
	"victory_messages": True,
	"show_result": True
}
CDMESSAGES = ["It is not time yet.", "'Tis not yet time.",
	"I need more time.", "I am not ready.", "It is not yet time."]

settings = {}

try:
	with open("data/settings.json") as json_data:
		file = json.load(json_data)
		for key in BOT_DEFAULTS:
			if key in file:
				settings[key] = file[key]
			else:
				settings[key] = BOT_DEFAULTS[key]
except FileNotFoundError:
	print("You need to create a file named settings.json in the data folder (if there is none, create one). Please see the README for more information.")
	raise SystemExit
except json.decoder.JSONDecodeError:
	print("Could not load settings.json. Please make sure the syntax is correct.")

if not settings["token"]:
	print("No valid token was found. Please make sure a Discord bot user token is supplied in data/settings.json.")
	raise SystemExit

if not settings["apikey"]:
	print("No valid API key was found. Please make sure a Steam user API key is supplied in data/settings.json.")
	raise SystemExit

if not settings["prefix"]:
	settings["prefix"] = ";"

# A blank "owner" field can be handled later, when the bot is up and running

class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = {}
		self.server_settings_list = {}
		# Maybe put the above code in this block, so the bot.settings = settings line is not needed? But I would need a way to change the prefix T.T

	def is_owner(self, user):
		return user.id == bot.settings["owner"]

	def is_admin(self, member):
		return member.server_permissions.administrator

	async def get_owner(self):
		return await bot.get_user_info(bot.settings["owner"])
	
	def save_server_settings(self):
		with open("data/server_settings.json", "w") as serv_set:
			json.dump(bot.server_settings_list, serv_set, indent = 4)

bot = Bot(command_prefix = settings["prefix"], description = DESC)
bot.settings = settings
bot.next_interval = bot.settings["api_interval"]

try:
	with open("data/server_settings.json") as json_data:
		file = json.load(json_data)
		for serv, serv_settings in file.items():
			bot.server_settings_list[serv] = serv_settings
except FileNotFoundError:
	pass
except json.decoder.JSONDecodeError:
	print("Could not load server_settings.json. Please make sure the syntax is correct, or delete the file and restart the bot to generate a new one.")

def set_welcome_channel(server, channel):
	bot.server_settings_list[server.id]["welcome_channel"] = channel.id
	bot.save_server_settings()

def set_welcome_messages(server, option):
	bot.server_settings_list[server.id]["welcome_messages"] = option
	bot.save_server_settings()

async def say_welcome_channel(server, msg):
	welcome_channel = bot.server_settings_list[server.id]["welcome_channel"]
	if welcome_channel:
		try:
			await bot.send_message(bot.get_channel(welcome_channel), msg)
		except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
			await bot.send_message(server.default_channel, "I wish to post in the designated channel for welcome messages but am unable to, for I lack the required permissions (or else the channel does not exist).")
			await bot.send_message(server.default_channel, msg)
	else:
		await bot.send_message(server.default_channel, msg)

@bot.event
async def on_ready():
	if not bot.settings["owner"]:
		appinfo = await bot.application_info()
		bot.settings["owner"] = appinfo.owner.id

	try:
		await bot.get_owner()
	except discord.NotFound:
		print("The bot owner could not be determined. Please check your settings.json file.")
		print()

	any_new_servers = False
	for server in bot.servers:
		if server.id not in bot.server_settings_list:
			if bot.settings["verbose"]:
				print("Generating server-specific settings for %s..." % server.name)
			bot.server_settings_list[server.id] = dict(SERVER_DEFAULTS)
			any_new_servers = True

	if any_new_servers:
		bot.save_server_settings()
		if bot.settings["verbose"]:
			print()

	bot.joinurl = "https://discordapp.com/oauth2/authorize?&client_id=%s&scope=bot" % bot.user.id

	print("Dota2HelperBot, a Discord bot created by Blanedale")
	print()
	print("Connected to the following servers:")
	for server in bot.servers:
		print(server.name)
	print()
	print("To add this bot to a server, go to: %s" % bot.joinurl)
	print()

	await bot.change_presence(game = discord.Game(name = "Type %shelp" % bot.settings["prefix"]))

@bot.event
async def on_member_join(member):
	serv = member.server
	if bot.server_settings_list[serv.id]["welcome_messages"]:
		await say_welcome_channel(serv, "%s has joined the server. Welcome!" % member.mention)

@bot.command(pass_context = True, no_pm = True)
async def welcomechannel(ctx, argument = None):
	"""Sets the channel for posting welcome messages.

	When used without an argument, uses the current channel. Otherwise, accepts a channel mention, a channel name, or a channel ID."""
	author = ctx.message.author
	if bot.is_owner(author) or bot.is_admin(author):
		server = ctx.message.server
		if not argument:
			channel = ctx.message.channel
			set_welcome_channel(server, channel)
			await bot.say("%s is now the designated channel for welcome messages." % channel.mention)
		else:
			for ch in server.channels:
				if ch.mention == argument or ch.name == argument or ch.id == argument:
					if ch.type == discord.ChannelType.text:
						set_welcome_channel(server, ch)
						await bot.say("%s is now the designated channel for welcome messages." % ch.mention)
						return
					else:
						await bot.say("That channel cannot be used for such purposes.")
						return
			await bot.say("Alas, I know of no such channel.")
	else:
		await bot.say("You have not the authority to issue such a command.")

@bot.command(pass_context = True, no_pm = True)
async def greetnewmembers(ctx, argument = None):
	"""Turns the welcome messages on or off.

	When used without an argument, shows current setting. Use "off", "no", or "false" to turn welcome messages off. Anything else turns it on."""
	server = ctx.message.server
	if not argument:
		if bot.server_settings_list[server.id]["welcome_messages"]:
			await bot.say("Welcome messages are currently enabled.")
		else:
			await bot.say("Welcome messages are currently disabled.")
	else:
		author = ctx.message.author
		if bot.is_owner(author) or bot.is_admin(author):
			if argument == "off" or argument == "no" or argument == "false":
				set_welcome_messages(server, False)
				await bot.say("Welcome messages are now disabled.")
			else:
				set_welcome_messages(server, True)
				await bot.say("Welcome messages are now enabled.")
		else:
			await bot.say("You have not the authority to issue such a command.")

@bot.event
async def on_command_error(error, ctx):
	channel = ctx.message.channel
	if isinstance(error, commands.MissingRequiredArgument):
		await bot.send_message(channel, "Truly, your wish is my command, but I cannot carry out your orders without a suitable argument.")
	elif isinstance(error, commands.BadArgument):
		await bot.send_message(channel, "Truly, your wish is my command, but I cannot make head nor tail of the argument you do provide.")
	elif isinstance(error, commands.CommandNotFound):
		await bot.send_message(channel, "I fear I know not of this \"%s\". Is it perchance a new Hero?" % ctx.message.content[len(bot.settings["prefix"]):])
	elif isinstance(error, commands.CommandOnCooldown):
		await bot.send_message(channel, random.choice(CDMESSAGES))
	elif isinstance(error, commands.NoPrivateMessage):
		await bot.send_message(channel, "Truly, your wish is my command, but that order is not to be issued in secret. It must be invoked in a server.")
	else:
		try:
			await bot.send_message(channel, "I fear some unprecedented disaster has occurred which I cannot myself resolve. Methinks you would do well to consult %s on this matter." % (await bot.get_owner()).mention)
		except discord.NotFound:
			await bot.send_message(channel, "I fear some unprecedented disaster has occurred which I cannot myself resolve.")
		if isinstance(error, commands.CommandInvokeError):
			print(repr(error.original))
		else:
			print(repr(error))

bot.load_extension("cogs.general")
bot.load_extension("cogs.matchupdates")
bot.run(bot.settings["token"])
