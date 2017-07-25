# Dota2HelperBot, a Discord bot to give live updates on Dota 2 tournament games and more

Dependencies:
* Python >=3.5
* discord.py

Get Python here: https://www.python.org/downloads/

For more information on installing discord.py, go here: https://github.com/Rapptz/discord.py

To use this bot, you need to create a file named "settings.json" in the data/ folder, like so:

```
{
	"token": <your token here>
	"apikey": <your Steam user API key here>
}
```

In order to obtain a token, create a new bot user here: https://discordapp.com/developers/applications/me

In order to obtain a Steam user API key, go here: https://steamcommunity.com/dev/apikey

The complete list of options is as follows:
```
{
	"token": String that will be the bot's token
	"prefix": String representing the command prefix
	"owner": String representing your Discord user ID
	"changenick_interval": Int, number of seconds to wait before changing nickname again
	"api_interval": Int, number of seconds to wait before making another call to Valve's API (recommended to be greater than 1)
	"apikey": String representing your Steam API key
	"filter_matches": Bool, determines whether the bot only reports on important matches (i.e. matches in notable leagues)
	"notable_leagues": Array of ints representing the IDs of leagues you want to track
	"filter_generic": Bool, determines whether the bot filters out matches where neither team has a real name
	"no_repeat_matches": Bool, controls whether the bot filters out matches with the same teams and series score as a previous one
	"save_match_data": Bool, controls logging of data obtained from API calls
	"verbose": Bool, enables a bit more information in the program output
}
```

Of these fields, only `token` and `apikey` are required. `prefix` defaults to semicolon if left blank or not provided. The bot will attempt to determine its owner automatically if `owner` is not provided.

## Implemented commands

`changename` - Causes the bot to choose a random new nickname.

`ongoing` - Shows matches that are currently being “tracked” by the bot.

`welcomechannel` - Sets the channel for posting welcome messages. When used without an argument, uses the current channel. Otherwise, accepts a channel mention, a channel name, or a channel ID.

`matchchannel` - Sets the channel for posting match updates. When used without an argument, uses the current channel. Otherwise, accepts a channel mention, a channel name, or a channel ID.

`greetnewmembers` - Turns the welcome messages on or off. When used without an argument, shows current setting. Use "off", "no", or "false" to turn welcome messages off. Anything else turns it on.

`victorymessages` - Turns the victory messages on or off. When used without an argument, shows current setting. Use "off", "no", or "false" to turn victory messages off. Anything else turns it on.

`hidewinner` - Controls whether the bot omits the winner, duration, and final score from the victory message. When used without an argument, shows current setting. Use "off", "no", or "false" to turn welcome messages off. Anything else turns it on.

Any action that changes a server-specific setting must be performed by a server admin or the bot owner.

## Unimplemented commands

`contact` - Sends a message to the bot owner.

`untrack` - Removes all matches from the tracking list. Can only be used by the bot owner.

`status` - Shows the game state of all currently tracked matches.

`predict radiant|dire` - Sets your prediction for the specified team.

`score` - Shows the given user’s prediction record.

`restart` - Restarts the bot. Can only be used by the bot owner.

`addleague` - Adds to the list of notable leagues. Can only be used by the bot owner.

`leagues` - Shows the list of notable leagues.

## Tips

I recommend that you set the PYTHONIOENCODING environment variable to utf-8 in order to give the program an easier time when trying to print team names with special characters, especially in verbose mode. On Linux, try `export PYTHONIOENCODING="utf-8"`. On Windows, try `set PYTHONIOENCODING="utf-8"`.

## Todo

* Implement unimplemented commands
* Better error messages when a command is used incorrectly
* Ensure that the bot behaves as expected when invalid token or Steam API key values are used
* Implement a better way to change server-specific setting features without having to discard existing server-specific settings
* Twitch streams
* Fetch and save kill score and net worth difference periodically
