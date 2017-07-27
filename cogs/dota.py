import asyncio
import requests
import time

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to load MatchUpdates cog. Check your discord.py installation.")

LIVE_LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
MATCH_DETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"
MATCH_CHANNEL_NOT_FOUND = "I wish to post in the designated channel for match updates but am unable to, for I lack the required permissions (or else the channel does not exist)."

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

	def clear(self):
		self.matches.clear()

	def match_exists_with_teams(self, radiant_team, dire_team, gameno):
		for match in self.matches:
			if match.radiant_team == radiant_team and match.dire_team == dire_team and match.gameno == gameno:
				return True

		return False

class Dota:
	"""Cog for match updates"""

	def __init__(self, bot):
		self.bot = bot

	async def say_match_start(self, msg):
		for s in self.bot.servers:
			try: # Catching potential HTTPExceptions here is actually important, because if we don't then the background task will stop
				matches_channel = self.bot.server_settings_list[s.id]["matches_channel"]
				if matches_channel:
					try:
						await self.bot.send_message(self.bot.get_channel(matches_channel), msg)
					except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
						await self.bot.send_message(s.default_channel, MATCH_CHANNEL_NOT_FOUND)
				else:
					await self.bot.send_message(s.default_channel, msg)
			except discord.HTTPException:
				pass

	async def say_victory_message(self, msg_winner, msg_no_winner):
		for s in self.bot.servers:
			if self.bot.server_settings_list[s.id]["victory_messages"]:
				try:
					msg = msg_winner if self.bot.server_settings_list[s.id]["show_result"] else msg_no_winner
					matches_channel = self.bot.server_settings_list[s.id]["matches_channel"]
					if matches_channel:
						try:
							await self.bot.send_message(self.bot.get_channel(matches_channel), msg)
						except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
							await self.bot.send_message(s.default_channel, MATCH_CHANNEL_NOT_FOUND)
					else:
						await self.bot.send_message(s.default_channel, msg)
				except discord.HTTPException:
					pass

	def get_names_from_league_game(self, game):
		# Gets team names from a game provided by a GetLiveLeagueGames call. If a team has no name, it is "Radiant" or "Dire".
		if "radiant_team" in game:
			radiant_name = game["radiant_team"]["team_name"]
		else:
			radiant_name = "Radiant"

		if "dire_team" in game:
			dire_name = game["dire_team"]["team_name"]
		else:
			dire_name = "Dire"

		return (radiant_name, dire_name)

	def get_names_from_match_details(self, game):
		# Gets team names from a game provided by a GetMatchDetails call. If a team has no name, it is "Radiant" or "Dire".
		if "radiant_name" in game:
			radiant_name = game["radiant_name"]
		else:
			radiant_name = "Radiant"

		if "dire_name" in game:
			dire_name = game["dire_name"]
		else:
			dire_name = "Dire"

		return (radiant_name, dire_name)

	async def show_new_match(self, game, radiant_name, dire_name, gameno):
		if game["series_type"] == 0:
			series_desc = ""
		elif game["series_type"] == 1:
			series_desc = " (Game %s of 3)" % str(gameno)
		elif game["series_type"] == 2:
			series_desc = " (Game %s of 5)" % str(gameno)
		else:
			series_desc = " (unknown series type %s)" % str(game["series_type"]) # I don't think this is possible

		await self.say_match_start("The draft for %s vs. %s is now underway%s." % (radiant_name, dire_name, series_desc))

	async def show_match_results(self, game):
		# Not to be confused with show_result, the option for toggling whether the bot reveals the winner, duration, and kill score at the end
		radiant_name, dire_name = self.get_names_from_match_details(game)
		
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

		msg_winner = "%s vs. %s has ended in %s victory, %s%s in. The final score was %s. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (radiant_name, dire_name, winner, min_string, sec_string, score, game["match_id"])
		msg_no_winner = "%s vs. %s has ended. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (radiant_name, dire_name, game["match_id"])
		await self.say_victory_message(msg_winner, msg_no_winner)

	def make_request(self, url, matchid = ""):
		try:
			response = requests.get(url, params = {"key": self.bot.settings["apikey"], "match_id": matchid})
			response.raise_for_status() # Raise an exception if the request was unsuccessful (anything other than status code 200)
			return response
		except Exception as err:
			if self.bot.settings["verbose"]:
				print(err)
			if response.status_code == 403:
				print("The API key provided in data/settings.json was not accepted. Please make sure it is valid.")
			raise

	async def get_match_data(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			await asyncio.sleep(self.bot.next_interval)
			self.bot.next_interval = self.bot.settings["api_interval"]
			try:
				response = self.make_request(LIVE_LEAGUE_GAMES_URL)
			except Exception:
				continue # Just try again next time

			current_time = time.time()

			if self.bot.settings["save_match_data"]:
				file = open("matchdata%s.txt" % current_time, "w")
				text = response.text.encode("utf-8")
				file.write(str(text))

			games = response.json()["result"]["games"]
			finished_matches = MatchList(self.bot.ongoing_matches)
			for game in games:
				league_ok = not self.bot.settings["filter_matches"] or game["league_id"] in self.bot.settings["notable_leagues"]
				generic_ok = not self.bot.settings["filter_generic"] or "radiant_team" in game or "dire_team" in game
				if league_ok and generic_ok and game["match_id"] > 0: # Valve's API occasionally gives us the dreaded "Match 0"
					if game["match_id"] in self.bot.ongoing_matches:
						finished_matches.remove(game["match_id"])
					else:
						radiant_name, dire_name = self.get_names_from_league_game(game)
						gameno = game["radiant_series_wins"] + game["dire_series_wins"] + 1

						if self.bot.settings["verbose"]:
							try:
								print("[%s] Adding match %s to list (%s vs. %s, Game %s)" % (current_time, game["match_id"], radiant_name, dire_name, gameno))
							except UnicodeEncodeError:
								print("A new match has been added to the list, but could not be displayed here due to an encoding error")
						
						if not (self.bot.settings["no_repeat_matches"] and self.bot.ongoing_matches.match_exists_with_teams(radiant_name, dire_name, gameno)):
							await self.show_new_match(game, radiant_name, dire_name, gameno)

						self.bot.ongoing_matches.append(game["match_id"], radiant_name, dire_name, gameno)

			for finished in finished_matches:
				await asyncio.sleep(2)
				# Subtract the extra time waited to preserve the 20-second interval, but not if doing so would cause the time until the next call to be less than 2 seconds
				if self.bot.next_interval > 4:
					self.bot.next_interval -= 2

				# Fetch specific game data
				try:
					postgame = self.make_request(MATCH_DETAILS_URL, matchid = finished.matchid)
				except Exception:
					continue

				game = postgame.json()["result"]

				# It seems that sometimes the match disappears from the GetLiveLeagueGames listing, but hasn't actually ended yet. I don't know why...
				if "radiant_win" not in game or "duration" not in game:
					continue

				if self.bot.settings["verbose"]:
					radiant_name, dire_name = self.get_names_from_match_details(game)

					try:
						print("[%s] Match %s (%s vs. %s) finished" % (current_time, finished.matchid, radiant_name, dire_name))
					except UnicodeEncodeError:
						print("A match has finished, but could not be displayed here due to an encoding error")

				await self.show_match_results(game)
				self.bot.ongoing_matches.remove(finished.matchid)

	@commands.command()
	async def ongoing(self):
		"""Shows matches that are currently being tracked by the bot."""
		if len(self.bot.ongoing_matches) > 0:
			response = "Ongoing games:"
			for match in self.bot.ongoing_matches:
				response += "\n%s vs. %s (Match %s)" % (match.radiant_team, match.dire_team, match.matchid)
			await self.bot.say(response)
		else:
			await self.bot.say("There are as yet no ongoing games.")

	@commands.command()
	async def leagues(self):
		"""Displays leagues being tracked by the bot."""
		leagues = self.bot.get_notable_leagues()
		if len(leagues) > 0:
			response = "Tracked leagues: " + ", ".join([str(item) for item in leagues])
			await self.bot.say(response)
		else:
			await self.bot.say("There are as yet no leagues being tracked.")

	@commands.command(pass_context = True)
	async def untrack(self, ctx):
		"""Stops tracking all ongoing matches.

		Can only be used by the bot owner. Note that if this is called while any tracked matches are going on, they will probably be added right back to the list on the next API call."""
		if self.bot.is_owner(ctx.message.author):
			if len(self.bot.ongoing_matches) > 0:
				self.bot.ongoing_matches.clear()
				await self.bot.say("Done. Let them be forgotten like the dust which blows in the wind.")
			else:
				await self.bot.say("There are no ongoing matches. How can we erase what never existed?")
		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True)
	async def addleague(self, ctx, league: int):
		"""Adds to the list of notable leagues.

		Can only be used by the bot owner. Does not currently affect the notable_leagues field in settings.json, so any changes made using this command are not persistent between restarts."""
		if self.bot.is_owner(ctx.message.author):
			leagues = self.bot.get_notable_leagues()
			if league in leagues:
				await self.bot.say("Oh? I am already tracking that league.")
			else:
				self.bot.add_notable_league(league)
				await self.bot.say("I shall keep an eye out for matches in that league.")
		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True)
	async def rmleague(self, ctx, league: int):
		"""Removes from the list of notable leagues.

		Can only be used by the bot owner. Does not currently affect the notable_leagues field in settings.json, so any changes made using this command are not persistent between restarts."""
		if self.bot.is_owner(ctx.message.author):
			leagues = self.bot.get_notable_leagues()
			if league in leagues:
				self.bot.remove_notable_league(league)
				await self.bot.say("So be it. Matches in that league concern me no longer.")
			else:
				await self.bot.say("I am not tracking that league. How can we erase what never existed?")
		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def matchchannel(self, ctx, argument = None):
		"""Sets the channel for posting match updates.

		When used without an argument, shows current setting. Otherwise, accepts a channel mention, a channel name, or a channel ID."""
		server = ctx.message.server # As no_pm is true here, I am assuming server cannot be None
		if not argument:
			chsetting = self.bot.get_channel(self.bot.get_matches_channel(server))
			channel = server.default_channel if chsetting is None else chsetting
			await self.bot.say("%s is currently the designated channel for match updates." % channel.mention)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				for ch in server.channels:
					if ch.mention == argument or ch.name == argument or ch.id == argument:
						if ch.type == discord.ChannelType.text:
							self.bot.set_matches_channel(server, ch)
							await self.bot.say("%s is now the designated channel for match updates." % ch.mention)
							return
						else:
							await self.bot.say("That channel cannot be used for such purposes.")
							return
				await self.bot.say("Alas, I know of no such channel.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def victorymessages(self, ctx, argument = None):
		"""Turns the victory messages on or off.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn victory messages off. Anything else turns it on."""
		server = ctx.message.server
		if not argument:
			vmstate = "enabled" if self.bot.get_victory_messages(server) else "disabled"
			await self.bot.say("Post-game messages are currently %s." % vmstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if argument == "off" or argument == "no" or argument == "false":
					self.bot.set_victory_messages(server, False)
					await self.bot.say("Post-game messages are now disabled.")
				else:
					self.bot.set_victory_messages(server, True)
					await self.bot.say("Post-game messages are now enabled.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def showresult(self, ctx, argument = None):
		"""Controls whether or not to display match results.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn this feature off. Anything else turns it on."""
		server = ctx.message.server
		if not argument:
			srstate = "enabled" if self.bot.get_show_result(server) else "disabled"
			await self.bot.say("Match results in post-game messages are currently %s." % srstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if argument == "off" or argument == "no" or argument == "false":
					self.bot.set_show_result(server, False)
					await self.bot.say("Match results in post-game messages are now disabled.")
				else:
					self.bot.set_show_result(server, True)
					await self.bot.say("Match results in post-game messages are now enabled.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

def setup(bot):
	dota = Dota(bot)
	bot.add_cog(dota)
	bot.ongoing_matches = MatchList()
	bot.loop.create_task(dota.get_match_data())
	