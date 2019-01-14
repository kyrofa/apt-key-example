#!/usr/bin/env python3

import os
from setuptools import find_packages, setup

setup(
	name="apt-key-example",
	packages=find_packages(),
	entry_points={
		"console_scripts": [
			"apt-key-example = apt_key_example.example:main",
		]
	},
	data_files=[(os.path.join("share", "apt-key-example", "keyrings"), ["ros.gpg"])])
