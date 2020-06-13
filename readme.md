# PyTeamTalk

A human-friendly wrapper around the Teamtalk 5 TCP API.

It facilitates the process of creating TeamTalk bots and controllers, many times in only a couple lines of code. Forget the logistics, just build.

## What you can do

```
import teamtalk

t = teamtalk.TeamTalkServer("example.com", 10333)

@t.subscribe("messagedeliver")
def message(self, params):
	user = self.get_user(params["srcuserid"])
	if params["type"] == teamtalk.USER_MSG:
		print("private message")
		print("from: "+user["nickname"])
		print("content: "+params["content"])


t.connect()
t.login("bot1", "admin", "password", "TeamTalkBotClient")
t.handle_messages()
```

## Installation

This code has been tested and confirmed to work under python 3.8, though it probably does so just as well under other 3* versions.

Installing from source:

```
git clone http://github.com/cartertemm/pyteamtalk
cd pyteamtalk
pip install .
```

Alternatively, simply copy the directory and start hacking. There are no dependencies.

## Todo

The following still needs to be done

* Handle subscription changes
* Support sending and receiving files
* Support encrypted servers
* Support servers where users are unable to see other users
* Add to pip
