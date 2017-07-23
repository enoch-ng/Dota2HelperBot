# Dota2HelperBot, a Discord bot to give live updates on Dota 2 tournament games and more

Dependencies:
* Python >=3.5
* discord.py

To use this bot, you need to create a file named "settings.json" in the data/ folder. The complete list of options is as follows:
```
{
	"token": String that will be the bot's token
	"prefix": String representing the command prefix
	"owner": String representing your Discord user ID
	"default_server": ID of the server to use for channel-specific messages. Leave blank for the bot to always post updates in the default channel
	"join_channel": ID of the channel you want the bot to post welcome messages in
	"matches_channel": ID of the channel you want the bot to post match notifications in
	"changenick_interval": Number of seconds to wait before changing nickname again
	"api_interval": Number of seconds to wait before making another call to Valve's API (recommended to be greater than 1)
	"apikey": String representing your Steam API key
	"filter_matches": Bool, determines whether the bot only reports on important matches (i.e. matches in notable leagues)
	"notable_leagues": Array of ints representing the IDs of leagues you want to track
	"filter_generic": Bool, determines whether the bot filters out matches where neither team has a real name
	"victory_messages": Bool, controls the victory messages setting (see below)
	"no_repeat_matches": Bool, controls the norepeatmatches setting (see below)
	"save_match_data": Bool, controls logging of data obtained from API calls
	"verbose": Bool, enables a bit more information in the program output
}
```

Of these fields, only `token` and `apikey` are required (though putting something in `notable_leagues` is highly recommended unless you are disabling `no_repeat_matches`). `prefix` defaults to semicolon if left blank.

Implemented commands:

`purge` - Purges a user’s messages from the server. Actually, it only searches the last 1000 messages of each channel, so if the user has been in the server for a long time you may need to run the command multiple times if you want to be thorough.

`purgefromchannel` - Purges a user’s messages from the channel the command was issued in. Actually, it only searches the last 1000 messages in the channel, so if the user has been in the server for a long time you may need to run the command multiple times if you want to be thorough.

`changename` - Causes the bot to choose a random new nickname.

`ongoing` - Shows matches that are currently being “tracked” by the bot.

Unimplemented commands:

`norepeatmatches on|off` - When this setting is enabled, the bot will not report on new matches whose participants match the participants of an ongoing match. Useful for handling duplicate “ghost” matches that occasionally appear in Valve’s match data.

`victorymessages on|off` - When this setting is enabled, the bot will report the winner of a match once it ends, along with some details and a Dotabuff link.

`untrack` - Removes all matches from the tracking list.

`status` - Shows the game state of all currently tracked matches.

`predict radiant|dire` - Sets your prediction for the specified team.

`score` - Shows the given user’s prediction record.
