# Dota2HelperBot, a Discord bot to give live updates on Dota 2 tournament games and more

Dependencies:
* Python >=3.5
* discord.py

To use this bot, you need to create a file named "settings.json" in the data/ folder with the following fields:
```
{
	"owner": String representing your Discord user ID
	"token: String that will be the bot's token
	"join_channel": String representing the ID of the channel you want the bot to post welcome messages in
	"matches_channel": String representing the ID of the channel you want the bot to post match notifications in
	"prefix": String representing the command prefix
	"changenick_interval": Number of seconds to wait before changing nickname again
	"api_interval": Number of seconds to wait before making another call to Valve's API (recommended to be greater than 1)
	"apikey": String representing your Steam API key
	"notable_leagues": Array of ints representing the IDs of leagues you want to track
}
```
