import random
import asyncio
import json

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to start Nova. Check your discord.py installation.")

DESC = "Nova, a Discord bot to give live updates on Dota 2 tournament games"
REQUIRED_PERMISSIONS = 3072
BOT_DEFAULTS = {
	"token": "",
	"prefix": ";",
	"owner": "",
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
	"matches_channel": "",
	"victory_messages": True,
	"show_result": True,
}

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
	print("You need to create a file named settings.json in the data folder. Please see the README for more information.")
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
		self.formatter = commands.formatter.HelpFormatter()
		self.settings = {}
		self.server_settings_list = {}
		# Maybe put the above code in this block, so the bot.settings = settings line is not needed? But I would need a way to change the prefix

	async def send_cmd_help(self, ctx):
		pages = self.formatter.format_help_for(ctx, ctx.command)
		for page in pages:
			await self.send_message(ctx.message.channel, page)

	def is_owner(self, user):
		return user.id == self.settings["owner"]

	def is_admin(self, member):
		return member.server_permissions.administrator

	async def get_owner(self):
		return await self.get_user_info(self.settings["owner"])

	def get_notable_leagues(self):
		return self.settings["notable_leagues"]

	def get_prefix(self):
		return self.settings["prefix"]

	def get_apikey(self):
		return self.settings["apikey"]

	def get_api_interval(self):
		return self.settings["api_interval"]
	
	def save_settings(self):
		with open("data/settings.json", "w") as bot_set:
			json.dump(self.settings, bot_set, indent = 4)

	def save_server_settings(self):
		with open("data/server_settings.json", "w") as serv_set:
			json.dump(self.server_settings_list, serv_set, indent = 4)

	def autogenerate_server_settings(self, server):
		if server.id not in self.server_settings_list:
			if self.settings["verbose"]:
				print("Generating server-specific settings for %s..." % server.name)
			self.server_settings_list[server.id] = dict(SERVER_DEFAULTS)
			self.save_server_settings()
		else:
			for setting, default in SERVER_DEFAULTS.items():
				if setting not in self.server_settings_list[server.id]:
					self.server_settings_list[server.id][setting] = default
					self.save_server_settings()

	def set_matches_channel(self, server, channel):
		self.server_settings_list[server.id]["matches_channel"] = channel.id
		self.save_server_settings()

	def set_victory_messages(self, server, option):
		self.server_settings_list[server.id]["victory_messages"] = option
		self.save_server_settings()

	def set_show_result(self, server, option):
		self.server_settings_list[server.id]["show_result"] = option
		self.save_server_settings()

	def add_notable_league(self, league):
		self.settings["notable_leagues"].append(league)
		self.save_settings()

	def remove_notable_league(self, league):
		self.settings["notable_leagues"].remove(league)
		self.save_settings()

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

@bot.event
async def on_ready():
	if not bot.settings["owner"]:
		appinfo = await bot.application_info()
		bot.settings["owner"] = appinfo.owner.id

	try:
		await bot.get_owner()
	except discord.NotFound:
		print("The bot owner could not be determined. Please manually enter the owner's ID in the settings.json file.")
		print()

	bot.save_settings()
	for server in bot.servers:
		bot.autogenerate_server_settings(server)

	bot.joinurl = "https://discordapp.com/oauth2/authorize?&client_id=%s&scope=bot&permissions=%s" % (bot.user.id, REQUIRED_PERMISSIONS)

	print()
	print(DESC)
	print()
	print("Connected to the following servers:")
	for server in bot.servers:
		print(server.name)
	print()
	print("To add this bot to a server, go to: %s" % bot.joinurl)
	print()

@bot.event
async def on_server_join(server):
	bot.autogenerate_server_settings(server)

@bot.event
async def on_command_error(error, ctx):
	channel = ctx.message.channel
	if isinstance(error, commands.MissingRequiredArgument):
		await bot.send_cmd_help(ctx)
	elif isinstance(error, commands.BadArgument):
		await bot.send_message(channel, "Your command could not be processed because one or more arguments was invalid.")
	elif isinstance(error, commands.CommandNotFound):
		# This is almost as ugly as Manta on Medusa
		await bot.send_message(channel, "A command matching \"%s\" was not found." % ctx.message.content[len(bot.settings["prefix"]):].partition(' ')[0])
	elif isinstance(error, commands.NoPrivateMessage):
		await bot.send_message(channel, "That command cannot be used in DMs.")
	else:
		await bot.send_message(channel, "An unexpected error has occurred. Please report this incident to the developer.")
		if isinstance(error, commands.CommandInvokeError):
			print(repr(error.original))
		else:
			print(repr(error))

bot.load_extension("cogs.general")
bot.load_extension("cogs.dota")
try:
	bot.run(bot.settings["token"])
except discord.errors.LoginFailure:
	print("The token provided in data/settings.json was not accepted. Please make sure it is valid.")

