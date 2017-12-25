# Commands
`join` - No arguments. Displays a link where server owners can add this bot.

`ongoing` - No arguments. Shows matches being tracked by the bot.

`leagues` - No arguments. Shows leagues being tracked by the bot.

`matchchannel` - Sets the channel for posting match updates. When used without an argument, shows current setting. Accepts a channel mention, a channel name, or a channel ID.

`victorymessages` - Turns the victory messages on or off. When used without an argument, shows current setting. Use "off", "no", or "false" to turn victory messages off. Anything else turns it on.

`showresult` - Controls whether the bot displays the winner, duration, and final score in the victory message. When used without an argument, shows current setting. Use "off", "no", or "false" to turn this option off. Anything else turns it on.

`untrack` - No arguments. Removes all matches from the tracking list. Can only be used by the bot owner. Note that if this is called while any tracked matches are going on, they will probably be added right back to the list on the next API call!

`addleague` - Adds the given league ID to the list of tracked leagues. Can only be used by the bot owner.

`rmleague` - Removes the given league ID from the list of tracked leagues. Can only be used by the bot owner.

`globalnickreset` - Resets the bot's nickname in all servers. Can only be used by the bot owner.

`usernamereset` - Resets the bot's username. Can only be used by the bot owner.

`faq` - Displays a basic FAQ.

Any action that changes a server-specific setting must be performed by a server admin or the bot owner.
