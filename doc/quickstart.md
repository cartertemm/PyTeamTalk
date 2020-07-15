# Quickstart

## Your first bot

The following bot is as simple as they come. It logs into a server, silently echoing back all the private messages it receives.

```
import teamtalk

t = teamtalk.TeamTalkServer("example.com", 10333)

@t.subscribe("messagedeliver")
def message(server, params):
	user = server.get_user(params["srcuserid"])
	if params["type"] == teamtalk.USER_MSG:
		nickname = user["nickname"]
		content = params["content"]
		print("private message")
		print("from: "+nickname)
		print("content: "+params["content"])
		server.user_message(user, content)


t.connect()
t.login("bot1", "admin", "password", "TeamTalkBotClient")
t.handle_messages()
```

The teamtalk.TeamTalkServer class fascilitates the connection and management of a single TeamTalk server. It gets innitialized with both a server's host and TCP port.
You then call connect() to establish a connection to the server, and login along with your nickname, username, password and a short string that identifies your client.
A connection is useless, however, without first having something to do. The preferred method is through an event-based approach.
Subscribe does just this. It can be used as a decorator as shown above, or a standard function call:

```
t.subscribe("messagedeliver", message)
```

In either case, we're telling TeamTalk to call our message function when ever a "messagedeliver" event is fired. Pay attention to the parameters:

```
def message(server, params):
```

Server references the caller, in this case our TeamTalkServer instance. In most cases server == t, unless handling multiple concurrently. It's advised to use the parameter whenever possible.
Params is a dict containing all the parameters passed along with this event.
In this case, a messagedeliver always contains "type" (an int specifying the message type, user/channel/broadcast), "srcuserid" (the ID of the sender), "destuserid" (the ID of the recipient) and "content" (the message's content).

## Attributes

The server instance contains some useful attributes. Some are described below.
Read the code for a more exhaustive list.
Note that, as per the TeamTalk protocol, certain attributes may optionally be excluded when they don't apply. When in doubt, assume this is the case.

* server.channels: A list of dicts containing attributes for every channel on this server.
* server.users: a list of dicts containing attributes for every logged-in user.
* server.me: A dict containing attributes for this user.
* server.server_params: A dict containing info about this server's configuration.

### User Attributes

* userid
* nickname
* username
* ipaddr (if admin). Note this may be IPv4 or IPv6
* statusmode
* statusmsg
* version
* packetprotocol
* usertype
* sublocal
* subpeer
* userdata
* clientname
* chanid (if in a channe)

The following are only included for the current user, unless additional info is requested by an admin. They can be accessed from the me attribute of a server connection along with all of the above.

* ipaddr, even if not an admin. Note this may be IPv4 or IPv6
* userrights
* note
* initchan
* opchannels
* audiocodeclimit
* cmdflood

### Channel Attributes

* channel: The path to this channel, e.g. "/stereo/"
* chanid
* parentid
* password (only present if admin)
* oppassword (only present if admin)
* protected: 1 if a password is required to join, otherwise 0
* topic
* operators
* diskquota
* maxusers
* type
* userdata
* audiocodec (list)
* audiocfg (list)

### Server Attributes

* servername
* maxusers
* maxloginattempts
* autosave
* maxiplogins
* logindelay
* usertimeout
* motd
* voicetxlimit
* videotxlimit
* mediafiletxlimit
* desktoptxlimit
* totaltxlimit
* version
