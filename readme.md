# PyTeamTalk

A human-friendly wrapper around the Teamtalk 5 TCP API.

It facilitates the process of creating TeamTalk bots and controllers, many times in only a couple lines of code. Forget the logistics, just build.

## Installation

This code has been tested and confirmed to work under python 3.8, though it probably does so just as well under other 3* versions. I make no promises about examples.

From a terminal or command prompt, just do:

```
pip install pyteamtalk
```

Or to install from source:

```
git clone http://github.com/cartertemm/pyteamtalk
cd pyteamtalk
pip install .
```

Alternatively, simply copy the directory and start hacking. There are no dependencies.

## Getting started

Documentation is a work in progress at the moment. The code largely speaks for itself, though there is a basic [quickstart](https://github.com/cartertemm/PyTeamTalk/blob/master/doc/quickstart.md) as well as some working [bots](https://github.com/cartertemm/PyTeamTalk/blob/master/doc/bots.md) to try out, found in the examples directory.

## See Also

* [TeamTalk Spotify Bot](https://github.com/cartertemm/teamtalk-spotify-bot): A feature packed controller for Spotify, originally an example that has since branched off due to size and scope

## Contributing

Build something cool? Did I break things? I'd love to hear about it and/or list it here.
For feature additions and bug fixes, start out with an issue and we can work from there.
Sample bot PRs will be merged in most cases, so long as the purpose and usage is clearly documented in [doc/bots.md](https://github.com/cartertemm/PyTeamTalk/blob/master/doc/bots.md).
While not a requirement, I would also appreciate it if you could stick to the existing all be it unofficial code style for clarity, PEP8 with tabs.
Having trouble? Need something else? Give me a shout on [twitter](https://twitter.com/cartertemm).

## Todo

The following still needs to be done

- [x] Support encrypted servers
- [x] Publish to PyPI
- [ ] Support sending and receiving files
- [ ] Support servers where users are unable to see other users
