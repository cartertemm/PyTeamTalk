# Bots

Each of the following are meant to show how a functional bot is made.
In most cases, you'll need to directly edit the scripts to enter your desired server credentials, consult the code to see how this is done.

## Numbers Bot (numbers.py)

This bot retrieves facts from the Numbers API and displays them.

usage: Valid keywords: trivia, math, date or year followed by a number
Numbers can be integers (duh), dates (month/day), or random for anything. if none is provided, random is assumed.
For example, sending a PM with "year 2001" will spit out a fact pertaining to the year 2001. Likewise, sending "trivia" will reply with something useless you're bound to forget.

## Server Checker (check_servers.py)

A simple bot that summarizes users on a collection of servers and promptly logs out.
This example is slightly more involved, as it implements quick messy configuration handling and thread pooling, but demonstrates a different use case.

To use:

```
python check_servers.py
```

If this is your first time running, you'll get a message informing you that a configuration file was created.
You may now open up config.ini, add all the servers you wish to track, and run the program again.
