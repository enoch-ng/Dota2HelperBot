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
	def __init__(self, matchid, radiant_team, dire_team):
		self.matchid = matchid
		self.radiant_team = radiant_team
		self.dire_team = dire_team

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

	def append(self, matchid, radiant_team, dire_team):
		self.matches.append(Match(matchid, radiant_team, dire_team))

	def remove(self, matchid):
		for match in self.matches:
			if match.matchid == matchid:
				self.matches.remove(match)
				return

		raise KeyError

	def match_exists_with_teams(radiant_team, dire_team):
		for match in self.matches:
			if match.radiant_team == radiant_team and match.dire_team == dire_team:
				return True

		return False

with open("data/settings.json") as json_data:
	settings = json.load(json_data)
	OWNER = settings["owner"]
	TOKEN = settings["token"]
	DEFAULT_SERVER = settings["default_server"]
	JOIN_CHANNEL = settings["join_channel"]
	MATCHES_CHANNEL = settings["matches_channel"]
	PREFIX = settings["prefix"]
	CHANGENICK_INTERVAL = settings["changenick_interval"]
	API_INTERVAL = settings["api_interval"]
	APIKEY = settings["apikey"]
	FILTER_MATCHES = settings["filter_matches"]
	notable_leagues = settings["notable_leagues"]
	filtergeneric = settings["filtergeneric"]
	victorymessages = settings["victorymessages"]
	norepeatmatches = settings["norepeatmatches"]

DESC = "Dota2HelperBot, a Discord bot created by Blanedale"
BOTNAMES = ["Agnes", "Alfred", "Archy", "Barty", "Benjamin", "Bertram",
	"Bruni", "Buster", "Edith", "Ester", "Flo", "Francis", "Francisco", "Gil",
	"Gob", "Gus", "Hank", "Harold", "Harriet", "Henry", "Jacques", "Jorge",
	"Juan", "Kitty", "Lionel", "Louie", "Lucille", "Lupe", "Mabel", "Maeby",
	"Marco", "Marta", "Maurice", "Maynard", "Mildred", "Monty", "Mordecai",
	"Morty", "Pablo", "Seymour", "Stan", "Tobias", "Vivian", "Walter", "Wilbur"]
LIVE_LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
MATCH_DETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"

bot = commands.Bot(command_prefix = PREFIX, description = DESC)
bot.ongoing_matches = MatchList()
bot.next_interval = API_INTERVAL

async def set_nick(newnick):
	for server in bot.servers:
		await bot.change_nickname(server.me, "%s Bot" % newnick)

# Change nickname every 10 minutes
async def change_nick():
	await bot.wait_until_ready()
	while not bot.is_closed:
		current_nick = list(bot.servers)[0].me.nick # Since the nickname should be the same for all servers, it shouldn't matter that bot.servers isn't always in the same order
		newnick = random.choice(BOTNAMES)
		while newnick == current_nick:
			newnick = random.choice(BOTNAMES) # Keep rerolling until we get a different name
		await set_nick(newnick)
		await asyncio.sleep(CHANGENICK_INTERVAL)

async def say_all_servers(channelid, msg):
	for s in bot.servers:
		if s.id == DEFAULT_SERVER:
			await bot.send_message(bot.get_channel(channelid), msg)
		else:
			await bot.send_message(s.default_channel, msg)

async def show_new_match(game, radiant_name, dire_name):
	if game["series_type"] == 0:
		series_desc = ""
	elif game["series_type"] == 1:
		series_desc = " (Game %s of 3)" % str(game["radiant_series_wins"] + game["dire_series_wins"] + 1)
	elif game["series_type"] == 2:
		series_desc = " (Game %s of 5)" % str(game["radiant_series_wins"] + game["dire_series_wins"] + 1)
	else:
		series_desc = " (unknown series type %s)" % str(game["series_type"]) # I don't think this is possible

	await say_all_servers(MATCHES_CHANNEL, "The draft for %s vs. %s is now underway%s." % (radiant_name, dire_name, series_desc))

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

	await say_all_servers(MATCHES_CHANNEL, "%s vs. %s has ended in %s victory, %s%s in. The final score was %s. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (radiant_name, dire_name, winner, min_string, sec_string, score, game["match_id"]))

# Get live game data from Valve's web API
async def get_match_data():
	await bot.wait_until_ready()
	while not bot.is_closed:
		await asyncio.sleep(bot.next_interval)
		bot.next_interval = API_INTERVAL
		response = requests.get(LIVE_LEAGUE_GAMES_URL, params = {"key": APIKEY})
		try:
			response.raise_for_status() # Raise an exception if the request was unsuccessful (anything other than status code 200)
		except requests.exceptions.HTTPError as err:
			print(err)
			continue

		# THIS SECTION FOR LOGGING
		###############################
		current_time = time.time()
		file = open("matchdata%s.txt" % current_time, "w")
		text = response.text.encode("utf-8")
		file.write(str(text))
		###############################

		games = response.json()["result"]["games"]
		finished_matches = MatchList(bot.ongoing_matches)
		for game in games:
			league_ok = not FILTER_MATCHES or game["league_id"] in notable_leagues
			generic_ok = not filtergeneric or "radiant_team" in game or "dire_team" in game
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

					if not (norepeatmatches and bot.ongoing_matches.match_exists_with_teams(radiant_name, dire_name)):
						# THIS SECTION FOR LOGGING
						#############################
						print("[%s] Adding match %s to list (%s vs. %s)" % (current_time, game["match_id"], radiant_name, dire_name))
						#############################

						bot.ongoing_matches.append(game["match_id"], radiant_name, dire_name)
						await show_new_match(game, radiant_name, dire_name)

		for finished in finished_matches:
			await asyncio.sleep(2)
			# Subtract the extra time waited to preserve the 20-second interval, but not if doing so would cause the time until the next call to be less than 2 seconds
			if bot.next_interval > 4:
				bot.next_interval -= 2

			# Fetch specific game data
			try:
				postgame = requests.get(MATCH_DETAILS_URL, params = {"match_id": finished.matchid, "key": APIKEY})
				postgame.raise_for_status()
			except (ConnectionError, requests.exceptions.HTTPError) as err:
				print(err)
				continue # Just try again next time

			game = postgame.json()["result"]

			# It seems that sometimes the match disappears from the GetLiveLeagueGames listing, but hasn't actually ended yet. I don't know why...
			if "radiant_win" not in game or "duration" not in game:
				#print("Could not find match %s in GetLiveLeagueGames call, but it doesn't seem to have ended" % finished.matchid)
				continue

			# THIS SECTION FOR LOGGING
			#############################
			if "radiant_name" in game:
				radiant_name = game["radiant_name"]
			else:
				radiant_name = "Radiant"

			if "dire_name" in game:
				dire_name = game["dire_name"]
			else:
				dire_name = "Dire"

			print("[%s] Match %s (%s vs. %s) finished" % (current_time, finished.matchid, radiant_name, dire_name))
			#############################

			if victorymessages:
				await show_match_results(game)
			bot.ongoing_matches.remove(finished.matchid)

@bot.event
async def on_ready():
	print()
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
	if member.server.id == DEFAULT_SERVER:
		channel = bot.get_channel(JOIN_CHANNEL)
	else:
		channel = member.server.default_channel
	await bot.send_message(channel, "%s has joined the server. Welcome!" % member.mention)

def is_allowed_by_hierarchy(server, mod, user):
	is_special = mod == server.owner or mod.id == OWNER
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
	current_nick = list(bot.servers)[0].me.nick
	newnick = random.choice(BOTNAMES)
	while newnick == current_nick:
		newnick = random.choice(BOTNAMES)
	await set_nick(newnick)

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
		await bot.send_message(channel, "I fear I know not of this '%s'. Is it perchance a new Hero?" % ctx.message.content[len(PREFIX):])
	else:
		owner = await bot.get_user_info(OWNER)
		await bot.send_message(channel, "I fear some unprecedented disaster has occurred which I cannot myself resolve. Methinks you would do well to consult %s on this matter." % owner.mention)

bot.loop.create_task(get_match_data())
bot.loop.create_task(change_nick())
bot.run(TOKEN)
