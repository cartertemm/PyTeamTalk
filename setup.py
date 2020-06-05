from setuptools import setup, find_packages


__version__ = 0.1

with open("readme.md", "r") as f:
	long_description = f.read()

setup(
	name="PyTeamTalk",
	version=__version__,
	author="Carter Temm",
	author_email="crtbraille@gmail.com",
	description="A human-friendly wrapper around the TeamTalk 5 TCP API",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="http://github.com/cartertemm/pyteamtalk",
	packages=find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Development Status :: 3 - Alpha",
	],
	python_requires=">=3",
)
