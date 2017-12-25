# Nova
A Discord bot to give live updates on Dota 2 tournament games.

## Getting the bot on your server
You can invite my instance of the bot to your server here: https://discordapp.com/oauth2/authorize?&client_id=330848586399088641&scope=bot&permissions=3072

## Getting started
Once the bot is on your server and has permissions to talk, set your preferred channel for updates with the `;matchchannel` command. This can be a channel mention, a channel name, or a channel ID.

To see all the commands, type `help`. For information about a specific command, type `help` followed by the command name. A list of all the commands and their uses can also be found in the docs/ folder.

## Running your own instance
Dependencies:
* Python >=3.5
* discord.py

Get Python here: https://www.python.org/downloads/

For more information on installing discord.py, go here: https://github.com/Rapptz/discord.py

To use this bot, go to the data/ folder, copy the `settings_example.json` to a file named `settings.json`, and fill in your token and Steam API key.

In order to obtain a token, create a new bot user here: https://discordapp.com/developers/applications/me

In order to obtain a Steam user API key, go here: https://steamcommunity.com/dev/apikey

Only `token` and `apikey` are required. The bot will attempt to determine its owner automatically if `owner` is blank or not provided. Upon starting for the first time, the bot will autogenerate default settings if you have omitted any optional fields.

Make sure you add tournaments you want to track with the ;addleague command.

## Tips
* I recommend that you set the PYTHONIOENCODING environment variable to utf-8 in order to give the program an easier time when trying to print team names with special characters, especially in verbose mode. On Linux, try `export PYTHONIOENCODING="utf-8"`. On Windows, try `set PYTHONIOENCODING="utf-8"`.
* Valve's API occasionally sends multiple matches with the same data but different match IDs. Although the bot should filter out the duplicates (with no_repeat_matches enabled), it will still track all of them, since it has no way of knowing which is the "real" one. After a while, there might be a slowly growing pile of duplicate matches that will never finish. Therefore, it's a good idea to run `ongoing` (to make sure no real matches are going on) and `untrack` from time to time to clean them up. In the future the program will be able to clean up these duplicates automatically.

## Bugs, feature requests, and development updates
To report a bug or offer a suggestion, feel free to open an issue on this repository or join our Discord server here:

## FAQ
**Why am I not getting updates for matches?**

Make sure a channel is set through the `;matchchannel` command. Also, make sure you've given the bot permissions to talk in that channel.

**Will you periodically add new leagues to the bot?**

I will on my instance of the bot. If you're running your own instance of the bot, you'll have to add new leagues through the `;addleague` command or by editing the settings.json file.

**How do I find out what ID a tournament comes under?**

You can get league IDs by calling Valve's API (https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v1/?key=YOUR_API_KEY). In the future I hope to have some way to let people know the league IDs of upcoming tournaments more easily.
