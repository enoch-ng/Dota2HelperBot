# Dota2HelperBot, a Discord bot created by Blanedale

import random
import asyncio
import requests

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to start Dota2HelperBot. Check your discord.py installation.")

OWNER = 
TOKEN = 
PREFIX = ";"
DESC = "Dota2HelperBot, a Discord bot created by Blanedale"
BOTNAMES = ["Agnes", "Alfred", "Archy", "Barty", "Benjamin", "Bertram",
	"Bruni", "Buster", "Edith", "Ester", "Flo", "Francis", "Francisco", "Gil",
	"Gob", "Gus", "Hank", "Harold", "Harriet", "Henry", "Jacques", "Jorge",
	"Juan", "Kitty", "Lionel", "Louie", "Lucille", "Lupe", "Mabel", "Maeby",
	"Marco", "Marta", "Maurice", "Maynard", "Mildred", "Monty", "Mordecai",
	"Morty", "Pablo", "Seymour", "Stan", "Tobias", "Vivian", "Walter", "Wilbur"]
CHANGENICK_INTERVAL = 600
API_INTERVAL = 20
APIKEY = 
LIVE_LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
MATCH_DETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"
NOTABLE_LEAGUES = [5504, 5336, 5401]

bot = commands.Bot(command_prefix = PREFIX, description = DESC)
bot.ongoing_matches = []

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

# Get live game data from Valve's web API
async def get_match_data():
	await bot.wait_until_ready()
	while not bot.is_closed:
		response = requests.get(LIVE_LEAGUE_GAMES_URL, params = {"key": APIKEY})
		response.raise_for_status() # Raise an exception if the request was unsuccessful (anything other than status code 200)
		games = response.json()["result"]["games"]
		finished_matches = list(bot.ongoing_matches)
		for game in games:
			#if game["league_id"] in NOTABLE_LEAGUES:
			if True: # Lowering our standards
				if game["match_id"] in bot.ongoing_matches:
					finished_matches.remove(game["match_id"])
				else:
					print("Adding match %s to list" % game["match_id"])
					if "radiant_team" in game:
						radiant_name = game["radiant_team"]["team_name"]
					else:
						radiant_name = "Radiant"

					if "dire_team" in game:
						dire_name = game["dire_team"]["team_name"]
					else:
						dire_name = "Dire"

					bot.ongoing_matches.append(game["match_id"])

					if game["series_type"] == 0:
						series_desc = ""
					elif game["series_type"] == 1:
						series_desc = " (Game %s of 3)" % str(game["radiant_series_wins"] + game["dire_series_wins"] + 1)
					elif game["series_type"] == 2:
						series_desc = " (Game %s of 5)" % str(game["radiant_series_wins"] + game["dire_series_wins"] + 1)
					else:
						series_desc = " (unknown series type %s)" % str(game["series_type"])

					await bot.send_message(bot.get_channel("330452442401734666"), "The draft for %s vs. %s is now underway%s." % (radiant_name, dire_name, series_desc))

		interval = API_INTERVAL
		for finished in finished_matches:
			await asyncio.sleep(1.5)
			# Subtract the extra time waited to preserve the 20-second interval, but not if doing so would cause the time until the next call to be less than 1.5 seconds
			if interval > 3:
				interval -= 1.5

			# Fetch specific game data
			postgame = requests.get(MATCH_DETAILS_URL, params = {"match_id": finished, "key": APIKEY})
			postgame.raise_for_status()
			game = postgame.json()["result"]

			# It seems that sometimes the match disappears from the GetLiveLeagueGames listing, but hasn't actually ended yet. I don't know why...
			if "radiant_win" not in game or "duration" not in game:
				print("Could not find match %s in GetLiveLeagueGames call, but it doesn't seem to have ended" % finished)
				continue

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

			m, s = divmod(game["duration"], 60)
			if s == 0:
				readable_duration = "%s minutes" % m
			elif s == 1:
				readable_duration = "%s minutes and 1 second" % m
			else:
				readable_duration = "%s minutes and %s seconds" % (m, s)

			await bot.send_message(bot.get_channel("330452442401734666"), "%s vs. %s has ended in %s victory, %s in." % (radiant_name, dire_name, winner, readable_duration))
			bot.ongoing_matches.remove(finished)
			print("Match %s finished" % finished)
		await asyncio.sleep(interval)

@bot.event
async def on_ready():
	await set_nick(random.choice(BOTNAMES))
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
	if member.server.id == "330451340826509312":
		channel = bot.get_channel("330451482455572493")
	else:
		channel = member.server.default_channel
	await bot.send_message(channel, "%s has joined the server. Welcome!" % member.mention)

def is_allowed_by_hierarchy(server, mod, user):
	is_special = mod == server.owner or mod.id == OWNER

	return mod.top_role.position > user.top_role.position or is_special

@bot.command(pass_context = True)
async def purge(ctx, user: discord.Member):
	server = ctx.message.server
	author = ctx.message.author

	if not is_allowed_by_hierarchy(server, author, user):
		await bot.say("Oh? But you have not the authority to issue such a command. I require instruction from a higher power in order to purge %s's messages." % user.mention)
		return

	try:
		any_to_delete = False
		for channel in server.channels:
			async for message in bot.logs_from(channel, before = ctx.message):
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
async def purge_from_channel(ctx, user: discord.Member):
	server = ctx.message.server
	author = ctx.message.author

	if not is_allowed_by_hierarchy(server, author, user):
		await bot.say("Oh? But you have not the authority to issue such a command. I require instruction from a higher power in order to purge %s's messages." % user.mention)
		return

	try:
		channel = ctx.message.channel
		any_to_delete = False
		async for message in bot.logs_from(channel, before = ctx.message):
			if message.author == user:
				await bot.delete_message(message)
				any_to_delete = True

		if any_to_delete:
			await bot.say("Done. Let their name be forgotten like the dust which blows in the wind.")
		else:
			await bot.say("They bear no record here. How can we erase that which never existed?")
	except discord.Forbidden:
		await bot.say("I fear the limitations bestowed upon me are too great for such a task.")

@bot.event
async def on_command_error(error, ctx):
	if isinstance(error, commands.CommandNotFound):
		await bot.send_message(ctx.message.channel, "I fear I know not of this '%s'. Is it perchance a new Hero?" % ctx.message.content[len(PREFIX):])

bot.loop.create_task(get_match_data())
bot.loop.create_task(change_nick())
bot.run(TOKEN)