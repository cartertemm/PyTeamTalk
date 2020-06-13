"""Simple TeamTalk bot that summarizes users on a collection of TeamTalk
servers and promptly logs out. This was meant to address a concern from many
administrators that felt uncomfortable with a program continuously intercepting
events. There was a similar service offered by Chris Nestrud a couple years
back, but to my knowledge it no longer exists.

This example is slightly more involved, as it implements quick configuration handling and thread pooling."""

# A part of PyTeamTalk
# author: Carter Temm
# License: MIT

import sys
import threading
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import teamtalk

spec = """# TT server listener configuration
# Sections starting with # are comments and not processed directly
# Uncomment the following, copy it as many times as you like and modify fields

# Replace with a memorable server name
# [server_name]
# host = example.com
# tcpport = 10333
# nickname = me
# username = admin
# password = password
"""

config = None
client_name = "TeamTalkUserLister"


def load_config(file="config.ini"):
	global config
	try:
		config = configparser.ConfigParser()
	except configobj.Error as exc:
		print("There was an error validating the config")
		print(exc)
	loaded = config.read(file)
	if not loaded:
		print(file + " does not exist")
		# messy but gets the job done for now
		with open(file, "w") as f:
			f.write(spec)
		print("Created a configuration file")
		print("Edit it and try running again")
		sys.exit(1)
	sections = config.sections()
	if not sections:
		# no servers
		print("No servers found in the config")
		print("Add one and try again")
		sys.exit()


def get(section, option, default=None):
	"""Gets a value from the config, but works like you'd expect
	If option is not found in section, use default"""
	try:
		val = config.get(section, option)
	except configparser.NoOptionError:
		val = default
	return val


def wait_for_info(section, server):
	"""Waits for a TeamTalk server to complete the login sequence, then disconnects.
	Meant to run in a thread"""
	username = get(section, "username", "")
	password = get(section, "password", "")
	nickname = get(section, "nickname", "")
	server.connect()
	server.login(nickname, username, password, client_name)

	def cb(server, event, params):
		if server.users and server.channels and not server.logging_in:
			# we have what we need
			server.disconnect()
			return
		if event and event == "error":
			print("Skipping " + section)
			self.disconnect()
			return

	server.handle_messages(0.5, cb)


def summarize_server(section, server):
	"""Summarizes activity on the provided server"""
	connected_users = len(server.users) - 1  # exclude our login
	if connected_users > 0:
		print(section + " (" + str(connected_users) + " connected)")
		# include the lobby
		for channel in server.channels + [None]:
			users = server.get_users_in_channel(channel)
			# exclude ourselves
			users = [i for i in users if not i["userid"] == server.me["userid"]]
			if len(users) > 0:
				if channel:
					print(f"{channel['channel']}, {len(users)}: ")
				else:
					print(f"not in a channel, {len(users)}: ")
				text = ""
				for user in users:
					role = server.get_role(user)
					text += f"{user['nickname']} ({role}), "
				# remove trailing ", "
				text = text[:-2]
				print(text)


def main():
	load_config()
	executor = ThreadPoolExecutor()
	tasks = {}
	for section in config.sections():
		host = get(section, "host")
		tcpport = get(section, "tcpport")
		server = teamtalk.TeamTalkServer(host, tcpport)
		tasks[executor.submit(wait_for_info, section, server)] = (section, server)
	print(str(len(tasks)) + " servers loaded")
	for future in as_completed(tasks):
		section = tasks[future][0]
		server = tasks[future][1]
		summarize_server(section, server)


if __name__ == "__main__":
	main()
