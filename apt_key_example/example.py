#!/usr/bin/env python3

import apt
import contextlib
import os
import platform
import shutil
import sys
import textwrap


def apt_sources():
	ros_repo = "http://packages.ros.org/ros/ubuntu/"
	ubuntu_repo = "http://archive.ubuntu.com/ubuntu/"
	security_repo = "http://security.ubuntu.com/ubuntu/"

	return textwrap.dedent(
		"""
		deb {ros_repo} {codename} main
		deb {ubuntu_repo} {codename} main universe
		deb {ubuntu_repo} {codename}-updates main universe
		deb {ubuntu_repo} {codename}-security main universe
		deb {security_repo} {codename}-security main universe
		""".format(
			ros_repo=ros_repo,
			ubuntu_repo=ubuntu_repo,
			security_repo=security_repo,
			codename=platform.linux_distribution()[2],
		)
	)


def apt_cache():
	root_dir = "/tmp/apt-test-root-dir"
	with contextlib.suppress(FileNotFoundError):
		shutil.rmtree(root_dir)

	# Don't install recommends
	apt.apt_pkg.config.set("Apt::Install-Recommends", "False")

	# Ensure repos are signed
	apt.apt_pkg.config.set("Acquire::AllowInsecureRepositories", "False")

	# Not running on the system, don't execute post-invoke-success
	apt.apt_pkg.config.clear("APT::Update::Post-Invoke-Success")

	# We want to use the system apt's GPG config, but also want the ability
	# to trust other keys file fetching packages without sudo. To enable this,
	# we'll redirect TrustedParts to somewhere we can write, and symlink to all
	# of the system's existing trusted parts.
	trusted_parts_path = apt.apt_pkg.config.find_file("Dir::Etc::TrustedParts")
	unpriv_trusted_parts = os.path.join(root_dir, trusted_parts_path.lstrip("/"))
	os.makedirs(unpriv_trusted_parts, exist_ok=True)

	# Symlink in system's trusted parts
	for trusted_part in os.scandir(trusted_parts_path):
		os.symlink(trusted_part.path, os.path.join(unpriv_trusted_parts, trusted_part.name))

	# Now redirect TrustedParts to our unpriv one
	apt.apt_pkg.config.set("Dir::Etc::TrustedParts", unpriv_trusted_parts)

	# Now add our own trusted part
	shutil.copy2(os.path.join(sys.prefix, "share", "apt-key-example", "keyrings", "ros.gpg"), unpriv_trusted_parts)

	sources_list_file = os.path.join(root_dir, "etc", "apt", "sources.list")
	os.makedirs(os.path.dirname(sources_list_file), exist_ok=True)
	with open(sources_list_file, "w") as f:
		f.write(apt_sources())

	apt_cache = apt.Cache(rootdir=root_dir, memonly=True)
	apt_cache.update(fetch_progress=apt.progress.text.AcquireProgress(), sources_list=sources_list_file)
	return apt_cache


def main():
	cache = apt_cache()


if __name__ == "__name__":
	main()
