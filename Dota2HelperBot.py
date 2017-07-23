# Dota2HelperBot, a Discord bot created by Blanedale

import random
import asyncio
import requests
import json
import time # For logging

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to start Dota2HelperBot. Check your discord.py installation.")

class Match:
	def __init__(self, matchid, radiant_team, dire_team, gameno):
		self.matchid = matchid
		self.radiant_team = radiant_team
		self.dire_team = dire_team
		self.gameno = gameno

class MatchList:
	def __init__(self, original = None):
		self.matches = []
		if original is not None:
			for original_match in original:
				self.matches.append(original_match)

	def __len__(self):
		return len(self.matches)

	def __getitem__(self, key):
		if not isinstance(key, int):
			raise TypeError
		if key >= len(self.matches):
			raise IndexError
		return self.matches[key]

	def __missing__(self):
		pass # I don't know what this does

	def __setitem__(self):
		pass # Is this really necessary?

	def __delitem__(self, key):
		if not isinstance(key, int):
			raise TypeError
		if key >= len(self.matches):
			raise IndexError
		del self.matches[key]

	def __iter__(self):
		for match in self.matches:
			yield match

	def __contains__(self, matchid):
		for match in self.matches:
			if match.matchid == matchid:
				return True

		return False

	def append(self, matchid, radiant_team, dire_team, gameno):
		self.matches.append(Match(matchid, radiant_team, dire_team, gameno))

	def remove(self, matchid):
		for match in self.matches:
			if match.matchid == matchid:
				self.matches.remove(match)
				return

		raise KeyError

	def match_exists_with_teams(self, radiant_team, dire_team, gameno):
		for match in self.matches:
			if match.radiant_team == radiant_team and match.dire_team == dire_team and match.gameno == gameno:
				return True

		return False

DESC = "Dota2HelperBot, a Discord bot created by Blanedale"
BOTNAMES = ["Agnes", "Alfred", "Archy", "Barty", "Benjamin", "Bertram",
	"Bruni", "Buster", "Edith", "Ester", "Flo", "Francis", "Francisco", "Gil",
	"Gob", "Gus", "Hank", "Harold", "Harriet", "Henry", "Jacques", "Jorge",
	"Juan", "Kitty", "Lionel", "Louie", "Lucille", "Lupe", "Mabel", "Maeby",
	"Marco", "Marta", "Maurice", "Maynard", "Mildred", "Monty", "Mordecai",
	"Morty", "Pablo", "Seymour", "Stan", "Tobias", "Vivian", "Walter", "Wilbur"]
LIVE_LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
MATCH_DETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"

defaults = {
	"token": "",
	"prefix": ";",
	"owner": "",
	"default_server": "",
	"join_channel": "",
	"matches_channel": "",
	"changenick_interval": 600,
	"api_interval": 20,
	"apikey": "",
	"filter_matches": True,
	"notable_leagues": [],
	"filter_generic": True,
	"victory_messages": True,
	"no_repeat_matches": True,
	"save_match_data": False,
	"verbose": True
}

settings = {}

with open("data/settings.json") as json_data:
	file = json.load(json_data)
	keys = ["token", "prefix", "owner", "default_server", "join_channel",
		"matches_channel", "changenick_interval", "api_interval", "apikey",
		"filter_matches", "notable_leagues", "filter_generic",
		"victory_messages", "no_repeat_matches", "save_match_data", "verbose"]
	for key in keys:
		if key in file:
			settings[key] = file[key]
		else:
			settings[key] = defaults[key]

if not settings["token"]:
	print("No valid token was found. Please make sure a Discord bot user token is supplied in data/settings.json.")
	raise SystemExit

if not settings["apikey"]:
	print("No valid API key was found. Please make sure a Steam user API key is supplied in data/settings.json.")
	raise SystemExit

if not settings["prefix"]:
	settings["prefix"] = ";"

# A blank "owner" field can be handled later, when the bot is up and running

bot = commands.Bot(command_prefix = settings["prefix"], description = DESC)

bot.ongoing_matches = MatchList()
bot.next_interval = settings["api_interval"]

async def set_nick(newnick):
	for server in bot.servers:
		await bot.change_nickname(server.me, "%s Bot" % newnick)

def choose_nick():
	current_nick = list(bot.servers)[0].me.nick # Since the nickname should be the same for all servers, it shouldn't matter that bot.servers isn't always in the same order
	newnick = random.choice(BOTNAMES)
	while newnick == current_nick:
		newnick = random.choice(BOTNAMES) # Keep rerolling until we get a different name
	return newnick

# Change nickname every 10 minutes
async def change_nick():
	await bot.wait_until_ready()
	while not bot.is_closed:
		serverlist = list(bot.servers)
		if len(serverlist) > 0:
			await set_nick(choose_nick())
		await asyncio.sleep(settings["changenick_interval"])

async def say_all_servers(channelid, msg):
	for s in bot.servers:
		if s.id == settings["default_server"] and channelid:
			await bot.send_message(bot.get_channel(channelid), msg)
		else:
			await bot.send_message(s.default_channel, msg)

async def show_new_match(game, radiant_name, dire_name, gameno):
	if game["series_type"] == 0:
		series_desc = ""
	elif game["series_type"] == 1:
		series_desc = " (Game %s of 3)" % str(gameno)
	elif game["series_type"] == 2:
		series_desc = " (Game %s of 5)" % str(gameno)
	else:
		series_desc = " (unknown series type %s)" % str(game["series_type"]) # I don't think this is possible

	await say_all_servers(settings["matches_channel"], "The draft for %s vs. %s is now underway%s." % (radiant_name, dire_name, series_desc))

async def show_match_results(game):
	if "radiant_name" in game:
		radiant_name = game["radiant_name"]
	else:
		radiant_name = "Radiant"

	if "dire_name" in game:
		dire_name = game["dire_name"]
	else:
		dire_name = "Dire"
	
	if game["radiant_win"]:
		winner = radiant_name
	else:
		winner = dire_name

	score = "%s-%s" % (game["radiant_score"], game["dire_score"])

	m, s = divmod(game["duration"], 60)
	min_string = "1 minute" if m == 1 else "%s minutes" % m

	if s == 0:
		sec_string = ""
	elif s == 1:
		sec_string = " and 1 second"
	else:
		sec_string = " and %s seconds" % s

	await say_all_servers(settings["matches_channel"], "%s vs. %s has ended in %s victory, %s%s in. The final score was %s. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (radiant_name, dire_name, winner, min_string, sec_string, score, game["match_id"]))

# Get live game data from Valve's web API
async def get_match_data():
	await bot.wait_until_ready()
	while not bot.is_closed:
		await asyncio.sleep(bot.next_interval)
		bot.next_interval = settings["api_interval"]
		try:
			response = requests.get(LIVE_LEAGUE_GAMES_URL, params = {"key": settings["apikey"]})
			response.raise_for_status() # Raise an exception if the request was unsuccessful (anything other than status code 200)
		except Exception as err:
			if settings["verbose"]:
				print(err)
			continue

		current_time = time.time()

		if settings["save_match_data"]:
			file = open("matchdata%s.txt" % current_time, "w")
			text = response.text.encode("utf-8")
			file.write(str(text))

		games = response.json()["result"]["games"]
		finished_matches = MatchList(bot.ongoing_matches)
		for game in games:
			league_ok = not settings["filter_matches"] or game["league_id"] in settings["notable_leagues"]
			generic_ok = not settings["filter_generic"] or "radiant_team" in game or "dire_team" in game
			if league_ok and generic_ok and game["match_id"] > 0: # Valve's API occasionally gives us the dreaded "Match 0"
				if game["match_id"] in bot.ongoing_matches:
					finished_matches.remove(game["match_id"])
				else:
					if "radiant_team" in game:
						radiant_name = game["radiant_team"]["team_name"]
					else:
						radiant_name = "Radiant"

					if "dire_team" in game:
						dire_name = game["dire_team"]["team_name"]
					else:
						dire_name = "Dire"

					gameno = game["radiant_series_wins"] + game["dire_series_wins"] + 1

					if settings["verbose"]:
						print("[%s] Adding match %s to list (%s vs. %s, Game %s)" % (current_time, game["match_id"], radiant_name, dire_name, gameno))
					
					if not (settings["no_repeat_matches"] and bot.ongoing_matches.match_exists_with_teams(radiant_name, dire_name, gameno)):
						await show_new_match(game, radiant_name, dire_name, gameno)

					bot.ongoing_matches.append(game["match_id"], radiant_name, dire_name, gameno)

		for finished in finished_matches:
			await asyncio.sleep(2)
			# Subtract the extra time waited to preserve the 20-second interval, but not if doing so would cause the time until the next call to be less than 2 seconds
			if bot.next_interval > 4:
				bot.next_interval -= 2

			# Fetch specific game data
			try:
				postgame = requests.get(MATCH_DETAILS_URL, params = {"match_id": finished.matchid, "key": settings["apikey"]})
				postgame.raise_for_status()
			except Exception as err:
				if settings["verbose"]:
					print(err)
				continue # Just try again next time

			game = postgame.json()["result"]

			# It seems that sometimes the match disappears from the GetLiveLeagueGames listing, but hasn't actually ended yet. I don't know why...
			if "radiant_win" not in game or "duration" not in game:
				continue

			if settings["verbose"]:
				if "radiant_name" in game:
					radiant_name = game["radiant_name"]
				else:
					radiant_name = "Radiant"

				if "dire_name" in game:
					dire_name = game["dire_name"]
				else:
					dire_name = "Dire"

				print("[%s] Match %s (%s vs. %s) finished" % (current_time, finished.matchid, radiant_name, dire_name))

			if settings["victory_messages"]:
				await show_match_results(game)
			bot.ongoing_matches.remove(finished.matchid)

@bot.event
async def on_ready():
	if not settings["owner"]:
		appinfo = await bot.application_info()
		owner = appinfo.owner

	print("Dota2HelperBot, a Discord bot created by Blanedale")
	print()
	print("Connected to the following servers:")
	for server in bot.servers:
		print(server.name)
	print()
	print("To add this bot to a server, go to: https://discordapp.com/oauth2/authorize?&client_id=%s&scope=bot" % bot.user.id)
	print()

@bot.event
async def on_member_join(member):
	if member.server.id == settings["default_server"] and settings["join_channel"]:
		channel = bot.get_channel(settings["join_channel"])
	else:
		channel = member.server.default_channel
	await bot.send_message(channel, "%s has joined the server. Welcome!" % member.mention)

@bot.event
async def on_server_join(server):
	await set_nick(choose_nick())

def is_allowed_by_hierarchy(server, mod, user):
	is_special = mod == server.owner or mod.id == settings["owner"]
	return mod.top_role.position > user.top_role.position or is_special

@bot.command(pass_context = True)
async def purge(ctx, user: discord.Member):
	"""Purges a user's messages from the server.

	It doesn't search from the beginning of message history, so you may need to run it multiple times if you want to be thorough."""
	server = ctx.message.server
	author = ctx.message.author

	if not is_allowed_by_hierarchy(server, author, user):
		await bot.say("Oh? But you have not the authority to issue such a command. I require instruction from a higher power in order to purge %s's messages." % user.mention)
		return

	try:
		any_to_delete = False
		for channel in server.channels:
			async for message in bot.logs_from(channel, limit = 1000, before = ctx.message):
				if message.author == user:
					await bot.delete_message(message)
					any_to_delete = True

		if any_to_delete:
			await bot.say("Done. Let their name be forgotten like the dust which blows in the wind.")
		else:
			await bot.say("They bear no record here. How can we erase that which never existed?")
	except discord.Forbidden:
		await bot.say("I fear the limitations bestowed upon me are too great for such a task.")

@bot.command(pass_context = True)
async def purgefromchannel(ctx, user: discord.Member):
	"""Purges a user's messages from the channel.

	It doesn't search from the beginning of message history, so you may need to run it multiple times if you want to be thorough."""
	server = ctx.message.server
	author = ctx.message.author

	if not is_allowed_by_hierarchy(server, author, user):
		await bot.say("Oh? But you have not the authority to issue such a command. I require instruction from a higher power in order to purge %s's messages." % user.mention)
		return

	try:
		channel = ctx.message.channel
		any_to_delete = False
		async for message in bot.logs_from(channel, limit = 1000, before = ctx.message):
			if message.author == user:
				await bot.delete_message(message)
				any_to_delete = True

		if any_to_delete:
			await bot.say("Done. Let their name be forgotten like the dust which blows in the wind.")
		else:
			await bot.say("They bear no record here. How can we erase that which never existed?")
	except discord.Forbidden:
		await bot.say("I fear the limitations bestowed upon me are too great for such a task.")

@bot.command()
async def changename():
	"""Chooses a random new nickname for the bot."""
	await bot.say("Too long have I endured this moniker. It is time to begin anew.")
	await set_nick(choose_nick())

@bot.command()
async def ongoing():
	"""Shows matches that are currently being tracked by the bot."""
	if len(bot.ongoing_matches) == 0:
		await bot.say("There are as yet no ongoing games.")
	else:
		response = "Ongoing games: "
		for match in bot.ongoing_matches:
			response += "\n%s vs. %s (Match %s)" % (match.radiant_team, match.dire_team, match.matchid)

		await bot.say(response)

@bot.event
async def on_command_error(error, ctx):
	channel = ctx.message.channel
	if isinstance(error, commands.CommandNotFound):
		await bot.send_message(channel, "I fear I know not of this '%s'. Is it perchance a new Hero?" % ctx.message.content[len(settings["prefix"]):])
	else:
		owner = await bot.get_user_info(settings["owner"])
		await bot.send_message(channel, "I fear some unprecedented disaster has occurred which I cannot myself resolve. Methinks you would do well to consult %s on this matter." % owner.mention)

bot.loop.create_task(get_match_data())
bot.loop.create_task(change_nick())
bot.run(settings["token"])
