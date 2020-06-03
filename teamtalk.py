"""PyTeamTalk

A wrapper around the TeamTalk 5 TCP API.

author: Carter Temm
license: MIT
http://github.com/cartertemm/pyteamtalk
"""


import shlex
import time
import threading
import telnetlib
import functools


# constants
## MSG Types
NONE_MSG = 0
USER_MSG = 1
CHANNEL_MSG = 2
BROADCAST_MSG = 3
CUSTOM_MSG = 4

## User rights (from library/teamTalkLib/teamtalk/common.h)
USERRIGHT_NONE = 0x00000000
USERRIGHT_MULTI_LOGIN = 0x00000001
USERRIGHT_VIEW_ALL_USERS = 0x00000002
USERRIGHT_CREATE_TEMPORARY_CHANNEL = 0x00000004
USERRIGHT_MODIFY_CHANNELS = 0x00000008
USERRIGHT_TEXTMESSAGE_BROADCAST = 0x00000010
USERRIGHT_KICK_USERS = 0x00000020
USERRIGHT_BAN_USERS = 0x00000040
USERRIGHT_MOVE_USERS = 0x00000080
USERRIGHT_OPERATOR_ENABLE = 0x00000100
USERRIGHT_UPLOAD_FILES = 0x00000200
USERRIGHT_DOWNLOAD_FILES = 0x00000400
USERRIGHT_UPDATE_SERVERPROPERTIES = 0x00000800
USERRIGHT_TRANSMIT_VOICE = 0x00001000
USERRIGHT_TRANSMIT_VIDEOCAPTURE = 0x00002000
USERRIGHT_TRANSMIT_DESKTOP = 0x00004000
USERRIGHT_TRANSMIT_DESKTOPINPUT = 0x00008000
USERRIGHT_TRANSMIT_MEDIAFILE_AUDIO = 0x00010000
USERRIGHT_TRANSMIT_MEDIAFILE_VIDEO = 0x00020000
USERRIGHT_TRANSMIT_MEDIAFILE = (
	USERRIGHT_TRANSMIT_MEDIAFILE_AUDIO | USERRIGHT_TRANSMIT_MEDIAFILE_VIDEO
)
USERRIGHT_LOCKED_NICKNAME = 0x00040000
USERRIGHT_LOCKED_STATUS = 0x00080000
USERRIGHT_RECORD_VOICE = 0x00100000
USERRIGHT_DEFAULT = (
	USERRIGHT_MULTI_LOGIN
	| USERRIGHT_VIEW_ALL_USERS
	| USERRIGHT_CREATE_TEMPORARY_CHANNEL
	| USERRIGHT_UPLOAD_FILES
	| USERRIGHT_DOWNLOAD_FILES
	| USERRIGHT_TRANSMIT_VOICE
	| USERRIGHT_TRANSMIT_VIDEOCAPTURE
	| USERRIGHT_TRANSMIT_DESKTOP
	| USERRIGHT_TRANSMIT_DESKTOPINPUT
	| USERRIGHT_TRANSMIT_MEDIAFILE
)
USERRIGHT_ALL = 0x0013FFFF
USERRIGHT_KNOWN_MASK = 0x001FFFFF


def parse_tt_message(message):
	"""Parses a message sent by Teamtalk.
	Also preserves datatypes.
	Returns a tuple of (event, parameters)"""
	params = {}
	message = message.strip()
	message = shlex.split(message)
	event = message[0]
	message.remove(event)
	for item in message:
		k, v = item.split("=")
		# Lists take the form [x,y,z]
		if "[" in v and "]" in v:
			v = v.strip("[]")
			# Make sure we aren't dealing with a blank list
			if v:
				v = v.split(",")
				lst = []
				for val in v:
					if val.isdigit():
						lst.append(int(val))
					# I've never once seem values take a form other than int
					# better to assume it is possible, however
					else:
						lst.append(val)
				v = lst
			else:
				v = []
		# preserve ints
		elif v.isdigit():
			v = int(v)
		params[k] = v
	return event, params


def build_tt_message(event, params):
	"""Given an event and dictionary containing parameters, builds a TeamTalk message.
	Also preserves datatypes.
	inverse of parse_tt_message"""
	message = event
	for key, val in params.items():
		message += " " + key + "="
		# integers aren't encapsulated in quotes
		if isinstance(val, int) or isinstance(val, str) and val.isdigit():
			message += str(val)
		# nor are lists
		elif isinstance(val, list):
			message += "["
			for v in val:
				if isinstance(v, int) or isinstance(v, str) and v.isdigit():
					message += str(v) + ","
				else:
					message += '"' + v + '",'
			# get rid of the trailing ",", if necessary
			if len(val) > 0:
				message = message[:-1]
			message += "]"
		else:
			message += '"' + val + '"'
	return message


class TeamTalkServer:
	"""Represents a single TeamTalk server."""

	def __init__(self, host, tcpport=10333):
		self.host = host
		self.tcpport = tcpport
		self.con = None
		self.pinger_thread = None
		self.message_thread = None
		self.disconnecting = False
		self.logging_in = False
		self.current_id = 0
		self.last_id = 0
		self.subscriptions = {}
		self.channels = []
		self.users = []
		self.me = {}
		self.server_params = {}
		self._subscribe_to_internal_events()

	def connect(self):
		"""Initiates the connection to this server
		Raises an exception on failure"""
		self.con = telnetlib.Telnet(self.host, self.tcpport)
		# the first thing we should get is a welcome message
		welcome = self.read_line(timeout=3)
		if not welcome:
			raise TimeoutError("Server failed to send welcome message in time")
		welcome = welcome.decode()
		event, params = parse_tt_message(welcome)
		if event != "teamtalk":
			# error
			# could mean we're working with a TT 4 server, or different protocol entirely
			return
		self.server_params = params

	def login(self, nickname, username, password, client, protocol="5.6", version="1.0"):
		"""Attempts to log in to the server.
		This should be called immediately after connect to prevent timing out"""
		message = build_tt_message(
			"login",
			{
				"nickname": nickname,
				"username": username,
				"password": password,
				"clientname": client,
				"protocol": protocol,
				"version": version,
				"id": 1,
			},
		)
		self.send(message)
		self.start_threads()

	def start_threads(self):
		self.pinger_thread = threading.Thread(target=self.handle_pings)
		self.pinger_thread.daemon = True
		self.pinger_thread.start()

	def read_line(self, timeout=None):
		"""Reads and returns a line from the server"""
		if self.disconnecting:
			return False
		return self.con.read_until(b"\r\n", timeout)

	def send(self, line):
		"""Sends a line to the server"""
		if self.disconnecting:
			return False
		if isinstance(line, str):
			line = line.encode()
		if not line.endswith(b"\r\n"):
			line += b"\r\n"
		self.con.write(line)

	def disconnect(self):
		"""Disconnect from this server.
		Signals all threads to stop"""
		self.disconnecting = True
		self.con.close()

	def handle_messages(self, timeout=None, callback=None):
		"""Processes all incoming messages
		If callback is specified, it will be ran every time a new line is received from the server (or timeout seconds) along with an instance of this class, the event name, and parameters.
		Please note: If timeout is None (or unspecified), the callback function may take a while to execute in instances when we aren't getting packets. This behavior may not be desireable for many applications.
			If in doubt, set a timeout.
			Also be wary of extremely small timeouts when handling larger lines
		"""
		while not self.disconnecting:
			line = self.read_line(timeout)
			if line == b"pong":
				# response to ping, which is handled internally
				# we don't actually care about getting something back, we just send them to make the server happy
				line = b"" # drop it
			try:
				line = line.decode()
			except UnicodeDecodeError:
				print("failed to decode line: " + line)
				if callable(callback):
					callback(self, "", {})
				continue
			if not line:
				if callable(callback):
					callback(self, "", {})
				continue # nothing to do
			event, params = parse_tt_message(line)
			event = event.lower()
			# Call messages for the event if necessary
			for func in self.subscriptions.get(event, []):
				func(self, params)
			# finally, call the callback
			if callable(callback):
				callback(self, event, params)


	def _sleep(self, seconds):
		"""Like time.sleep, but immediately halts execution if we need to disconnect from a server"""
		t = time.time()
		while not self.disconnecting and not time.time() - t >= seconds:
			pass

	def handle_pings(self):
		"""Handles pinging the server at a reasonable interval.
		Intervals are calculated based on the server's usertimeout value.
		This function always runs in it's own thread."""
		pingtime = 0
		while not self.disconnecting:
			self.send("ping")
			# in case usertimeout was changed somehow
			# logic from TTCom, which had a preferable approach to TT clients for what we're doing
			# better safe than sorry
			pingtime = float(self.server_params["usertimeout"])
			if pingtime < 1:
				pingtime = 0.3
			elif pingtime < 1.5:
				pingtime = 0.5
			else:
				pingtime *= 0.75
			self._sleep(pingtime)

	def subscribe(self, event, func=None):
		"""Starts calling func every time event is encountered, passing along a copy of this class as well as the parameters from the TT message
		This can also be used as a decorator
		"""

		def wrapper(_func):
			evt = event.lower()
			subs = self.subscriptions.get(evt)
			# events are added as we subscribe to them
			if subs:
				self.subscriptions[evt].append(_func)
			else:
				self.subscriptions[evt] = [_func]
			return _func

		if func:
			return wrapper(func)
		else:
			return wrapper

	def unsubscribe(self, event, func):
		"""Stops calling func when event is encountered
		Raises a KeyError or ValueError on failure"""
		event = event.lower()
		self.subscriptions[event].remove(func)

	def _subscribe_to_internal_events(self):
		"""Subscribes to all internal events that keep track of the server's state.
			self.users, self.me, self.channels, self.server_params, etc.
		Called automatically
		"""
		self.subscribe("error", self._error)
		self.subscribe("begin", self._begin)
		self.subscribe("end", self._end)
		self.subscribe("loggedin", self._loggedin)
		self.subscribe("accepted", self._accepted)
		self.subscribe("serverupdate", self._serverupdate)
		self.subscribe("addchannel", self._addchannel)

	def get_channel(self, id, index=False):
		"""Retrieves attributes for channels with the requested id.
		If index is False, returns a dict. Otherwise, returns the channel's index in self.channels
		If id is of type str, look for matching names
		If id is an int, look for matching chanid's
		If id is a dict, we assume params are lazily being passed and try searching for a chanid"""
		if isinstance(id, dict):
			id = id.get("chanid")
			if not id:
				return
		found = False
		for index, channel in enumerate(self.channels):
			if isinstance(id, int) and channel["chanid"] == id:
				found = True
			elif isinstance(id, str) and channel["channel"] == id:
				found = True
			if found:
				if index:
					return index
				else:
					return channel

	def get_user(self, id, index=False):
		"""Retrieves attributes for users with the requested id.
		If index is False, returns a dict. Otherwise, returns the user's index in self.users
		If id is of type str, look for matching names
			Be careful, though, as teamtalk imposes no limit on users with identical names.
		If id is an int, look for matching userid's
		If id is a dict, we assume params are lazily being passed and try searching for a userid
		"""
		if isinstance(id, dict):
			id = id.get("userid")
			if not id:
				return
		found = False
		for index, user in enumerate(self.users):
			if isinstance(id, int) and user["userid"] == id:
				found = True
			elif isinstance(id, str) and user["userid"] == id:
				found = True
			if found:
				if index:
					return index
				else:
					return user

	# Internal event responses
	# We subscribe to these to ensure we have the latest info
	# These take precedence over custom responses
	# methods are static because instances of this class are sent along to every response already, adding self would
	# be a redundancy

	@staticmethod
	def _error(self, params):
		"""Event fired when something goes wrong.
		params["number"] contains the code, and params["message"] is a human-friendly explanation of what went wrong"""
		print(f"error ({params['number']}): {params['message']}")

	@staticmethod
	def _begin(self, params):
		"""Event fired to acknowledge the start of an ordered response.
		When a sent message contains the field "id=*", responses take the form:
			begin id=*
			contents
			end id=*
		Messages are sent this way when ordering needs to be preserved.
		"""
		self.current_id = params["id"]
		# Logging in sends a flood of "loggedin" and "addchannel" packets
		# Handle these differently
		if self.current_id == 1:
			self.logging_in = True

	@staticmethod
	def _end(self, params):
		"""Event fired to acknowledge the end of an ordered response.
		When a sent message contains the field "id=*", responses take the form:
			begin id=*
			contents
			end id=*
		Messages are sent this way when ordering needs to be preserved.
		"""
		self.current_id = 0
		# Logging in sends a flood of "loggedin" and "addchannel" packets
		# Make it so these events can be handled differently if necessary
		if params["id"] == 1:
			self.logging_in = False

	@staticmethod
	def _loggedin(self, params):
		"""Event fired when a user has just logged in.
		Is also sent during login for every currently logged in user"""
		user_index = self.get_user(params["userid"], index=True)
		if not user_index:
			self.users.append(params)
		else:
			# something was updated
			# I don't think this should happen, but just to be sure
			self.users[user_index].update(params)

	@staticmethod
	def _accepted(self, params):
		"""Event fired immediately after an accepted login.
		Contains information about the current user"""
		self.me.update(params)

	@staticmethod
	def _serverupdate(self, params):
		"""Event fired after login that exposes more info to a client
		May also mean that attributes of this server have changed"""
		self.server_params.update(params)

	@staticmethod
	def _addchannel(self, params):
		"""Event fired when a new channel has been created
		Can also be used to tell a newly connected user about a channel"""
		chan_index = self.get_channel(params["chanid"], index=True)
		if not chan_index:
			self.channels.append(params)
		else:
			# shouldn't happen
			self.channels[chan_index].update(params)
