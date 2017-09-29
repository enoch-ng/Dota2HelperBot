import asyncio
import requests
import time
from json.decoder import JSONDecodeError

try:
	import discord
	from discord.ext import commands
except ImportError:
	print("Unable to load MatchUpdates cog. Check your discord.py installation.")

LIVE_LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
MATCH_DETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"
MATCH_CHANNEL_NOT_FOUND = "I wish to post in the designated channel for match updates but am unable to, for I lack the required permissions (or else the channel does not exist)."

class Match:
	def __init__(self, matchid, radiant_team, dire_team, gameno, seriestype):
		self.matchid = matchid
		self.radiant_team = radiant_team
		self.dire_team = dire_team
		self.gameno = gameno
		self.seriestype = seriestype

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

	def append(self, matchid, radiant_team, dire_team, gameno, seriestype):
		self.matches.append(Match(matchid, radiant_team, dire_team, gameno, seriestype))

	def remove(self, matchid):
		for match in self.matches:
			if match.matchid == matchid:
				self.matches.remove(match)
				return

		raise KeyError

	def clear(self):
		self.matches.clear()

	def get_match_by_id(self, matchid):
		for match in self.matches:
			if match.matchid == matchid:
				return match

		return None

	def match_exists_with_details(self, radiant_team, dire_team, gameno):
		# No need to include the series type as a parameter, as the participating teams and game number should be unique enough
		for match in self.matches:
			if match.radiant_team == radiant_team and match.dire_team == dire_team and match.gameno == gameno:
				return True

		return False

	def purge_duplicates(self, matchid):
		match = self.get_match_by_id(matchid)

		for m in self.matches:
			if m.radiant_team == match.radiant_team and m.dire_team == match.dire_team and m.gameno == match.gameno and m.matchid != match.matchid:
				self.matches.remove(m)

class Dota:
	"""Cog for match updates"""

	def __init__(self, bot):
		self.bot = bot

	def get_matches_channel(self, server):
		return self.bot.server_settings_list[server.id]["matches_channel"]

	def get_victory_messages(self, server):
		return self.bot.server_settings_list[server.id]["victory_messages"]

	def get_show_result(self, server):
		return self.bot.server_settings_list[server.id]["show_result"]

	async def say_match_start(self, msg):
		serverlist = list(self.bot.servers)
		for s in serverlist:
			try: # Catching potential HTTPExceptions here is actually important, because if we don't then the background task will stop
				matches_channel = self.get_matches_channel(s)
				if matches_channel:
					try:
						await self.bot.send_message(self.bot.get_channel(matches_channel), msg)
					except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
						await self.bot.send_message(s.default_channel, MATCH_CHANNEL_NOT_FOUND)
				else:
					await self.bot.send_message(s.default_channel, msg)
			except discord.HTTPException:
				pass
			except Exception as e:
				print("Unable to announce draft: %s" % e)

	async def say_victory_message(self, msg_winner, msg_no_winner):
		serverlist = list(self.bot.servers)
		for s in serverlist:
			if self.get_victory_messages(s):
				try:
					msg = msg_winner if self.get_show_result(s) else msg_no_winner
					matches_channel = self.get_matches_channel(s)
					if matches_channel:
						try:
							await self.bot.send_message(self.bot.get_channel(matches_channel), msg)
						except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
							await self.bot.send_message(s.default_channel, MATCH_CHANNEL_NOT_FOUND)
					else:
						await self.bot.send_message(s.default_channel, msg)
				except discord.HTTPException:
					pass
				except Exception as e:
					print("Unable to announce end of match: %s" % e)

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

	def get_gameno_from_match_details(self, game):
		# I don't know if Valve's API ever returns a match without radiant_score and dire_score fields
		return game["radiant_score"] + game["dire_score"] + 1

	async def show_new_match(self, game, radiant_name, dire_name, gameno):
		if game["series_type"] == 0:
			series_desc = "Best of 1"
		elif game["series_type"] == 1:
			series_desc = "Game %s of 3" % str(gameno)
		elif game["series_type"] == 2:
			series_desc = "Game %s of 5" % str(gameno)
		else:
			series_desc = "unknown series type %s" % str(game["series_type"]) # I don't think this is possible

		await self.say_match_start("The draft for %s vs. %s is now underway (%s)." % (radiant_name, dire_name, series_desc))

	async def show_match_results(self, game):
		# Not to be confused with show_result, the option for toggling whether the bot reveals the winner, duration, and kill score at the end
		matchid = game["match_id"]
		match = self.bot.ongoing_matches.get_match_by_id(matchid) # Look for the game in our list

		if match.seriestype == 0:
			series_string = ""
		else:
			series_string = "Game %s of " % match.gameno
		
		if game["radiant_win"]:
			winner = match.radiant_team
		else:
			winner = match.dire_team

		score = "%s-%s" % (game["radiant_score"], game["dire_score"])

		m, s = divmod(game["duration"], 60)
		min_string = "1 minute" if m == 1 else "%s minutes" % m

		if s == 0:
			sec_string = ""
		elif s == 1:
			sec_string = " and 1 second"
		else:
			sec_string = " and %s seconds" % s

		msg_winner = "%s%s vs. %s has ended in %s victory, %s%s in. The final score was %s. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (series_string, match.radiant_team, match.dire_team, winner, min_string, sec_string, score, matchid)
		msg_no_winner = "%s%s vs. %s has ended. Dotabuff: <https://www.dotabuff.com/matches/%s>" % (series_string, match.radiant_team, match.dire_team, matchid)
		await self.say_victory_message(msg_winner, msg_no_winner)

	def make_request(self, url, matchid = ""):
		try:
			response = requests.get(url, params = {"key": self.bot.get_apikey(), "match_id": matchid})
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
			self.bot.next_interval = self.bot.get_api_interval()
			try:
				response = self.make_request(LIVE_LEAGUE_GAMES_URL)
			except Exception:
				continue # Just try again next time

			current_time = time.time()

			if self.bot.settings["save_match_data"]:
				file = open("matchdata%s.txt" % current_time, "w")
				text = response.text.encode("utf-8")
				file.write(str(text))

			try:
				games = response.json()["result"]["games"]
			except JSONDecodeError:
				continue

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
						seriestype = game["series_type"]

						if self.bot.settings["verbose"]:
							try:
								print("[%s] Adding match %s to list (%s vs. %s, Game %s)" % (current_time, game["match_id"], radiant_name, dire_name, gameno))
							except UnicodeEncodeError:
								print("A new match has been added to the list, but could not be displayed here due to an encoding error")
						
						# This condition is needed to eliminate "duplicate" matches if the no_repeat_matches setting is enabled
						if not (self.bot.settings["no_repeat_matches"] and self.bot.ongoing_matches.match_exists_with_details(radiant_name, dire_name, gameno)):
							await self.show_new_match(game, radiant_name, dire_name, gameno)

						self.bot.ongoing_matches.append(game["match_id"], radiant_name, dire_name, gameno, seriestype)

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

				try:
					game = postgame.json()["result"]
				except JSONDecodeError:
					continue

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
				self.bot.ongoing_matches.purge_duplicates(finished.matchid)
				self.bot.ongoing_matches.remove(finished.matchid)

	@commands.command()
	async def ongoing(self):
		"""Shows matches that are currently being tracked by the bot."""
		if len(self.bot.ongoing_matches) > 0:
			response = "Ongoing games:"
			for match in self.bot.ongoing_matches:
				if match.seriestype == 0:
					series_string = "Best of 1"
				elif match.seriestype == 1:
					series_string = "Game %s of 3" % match.gameno
				elif match.seriestype == 2:
					series_string = "Game %s of 5" % match.gameno
				else:
					series_string = "unknown series type"

				response += "\n%s vs. %s (%s)" % (match.radiant_team, match.dire_team, series_string)
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
	async def addleague(self, ctx, league_id: int):
		"""Adds to the list of notable leagues.

		Can only be used by the bot owner. Does not currently affect the notable_leagues field in settings.json, so any changes made using this command are not persistent between restarts."""
		if self.bot.is_owner(ctx.message.author):
			leagues = self.bot.get_notable_leagues()
			if league_id in leagues:
				await self.bot.say("Oh? I am already tracking that league.")
			else:
				self.bot.add_notable_league(league_id)
				await self.bot.say("I shall keep an eye out for matches in that league.")
		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True)
	async def rmleague(self, ctx, league_id: int):
		"""Removes from the list of notable leagues.

		Can only be used by the bot owner. Does not currently affect the notable_leagues field in settings.json, so any changes made using this command are not persistent between restarts."""
		if self.bot.is_owner(ctx.message.author):
			leagues = self.bot.get_notable_leagues()
			if league_id in leagues:
				self.bot.remove_notable_league(league_id)
				await self.bot.say("So be it. Matches in that league concern me no longer.")
			else:
				await self.bot.say("I am not tracking that league. How can we erase what never existed?")
		else:
			await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def matchchannel(self, ctx, channel = None):
		"""Sets the channel for posting match updates.

		When used without an argument, shows current setting. Otherwise, accepts a channel mention, a channel name, or a channel ID."""
		server = ctx.message.server # As no_pm is true here, I am assuming server cannot be None
		if not channel:
			chsetting = self.bot.get_channel(self.get_matches_channel(server))
			ch = server.default_channel if chsetting is None else chsetting
			await self.bot.say("%s is currently the designated channel for match updates." % ch.mention)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				for ch in server.channels:
					if ch.mention == channel or ch.name == channel or ch.id == channel:
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
	async def victorymessages(self, ctx, option = None):
		"""Turns the victory messages on or off.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn victory messages off. Anything else turns it on."""
		server = ctx.message.server
		if not option:
			vmstate = "enabled" if self.get_victory_messages(server) else "disabled"
			await self.bot.say("Post-game messages are currently %s." % vmstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if option == "off" or option == "no" or option == "false":
					self.bot.set_victory_messages(server, False)
					await self.bot.say("Post-game messages are now disabled.")
				else:
					self.bot.set_victory_messages(server, True)
					await self.bot.say("Post-game messages are now enabled.")
			else:
				await self.bot.say("You have not the authority to issue such a command.")

	@commands.command(pass_context = True, no_pm = True)
	async def showresult(self, ctx, option = None):
		"""Controls whether or not to display match results.

		When used without an argument, shows current setting. Use "off", "no", or "false" to turn this feature off. Anything else turns it on."""
		server = ctx.message.server
		if not option:
			srstate = "enabled" if self.get_show_result(server) else "disabled"
			await self.bot.say("Match results in post-game messages are currently %s." % srstate)
		else:
			author = ctx.message.author
			if self.bot.is_owner(author) or self.bot.is_admin(author):
				if option == "off" or option == "no" or option == "false":
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
	
