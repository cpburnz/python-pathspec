"""
This script mangles the version in "pyproject.toml" to work around deficiencies
with TestPyPI.
"""

import argparse
import copy
import re
import subprocess
import sys
from pathlib import (
	Path)

from packaging.version import (
	Version)

PYPROJECT_TOML = Path("pyproject.toml")
VERSION_PY = Path("pathspec/_version.py")


def update_pyproject_toml() -> None:
	"""
	Update "pyproject.toml" by mangling its version.
	"""
	print("Get last tag.")
	tag = subprocess.check_output([
		'git', 'rev-list', '--tags', '--max-count=1',
	], text=True).strip()

	print("Get commit count.")
	count = subprocess.check_output([
		'git', 'rev-list', f'{tag}..HEAD', '--count',
	], text=True).strip()

	print(f"Read: {VERSION_PY}")
	version_input = VERSION_PY.read_text()
	raw_version = re.search(
		'^__version__\\s*=\\s*["\'](.+)["\']', version_input, re.M,
	).group(1)
	version = Version(raw_version)
	if not version.is_postrelease:
		version = copy.replace(version, post=1)

	version = copy.replace(version, dev=count)

	print(f"Read: {PYPROJECT_TOML}")
	output = PYPROJECT_TOML.read_text()

	# Mangle version.
	output = re.sub(
		'^version\\s*=\\s*".+"', f'version = "{version}"', output, count=1, flags=re.M,
	)

	print(f"Write: {PYPROJECT_TOML}")
	PYPROJECT_TOML.write_text(output)


def main() -> int:
	"""
	Run the script.
	"""
	# Parse command-line arguments.
	parser = argparse.ArgumentParser(description=__doc__)
	parser.parse_args()

	update_pyproject_toml()

	return 0


if __name__ == '__main__':
	sys.exit(main())
