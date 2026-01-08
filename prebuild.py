"""
This script generates files required for source and wheel distributions, and
legacy installations.
"""

import argparse
import configparser
import re
import sys
from pathlib import (
	Path)
try:
	import tomllib  # Added in 3.11.
except ModuleNotFoundError:
	import tomli as tomllib

CHANGES_0_IN_RST = Path("CHANGES_0.in.rst")
CHANGES_1_IN_RST = Path("CHANGES_1.in.rst")
CHANGES_RST = Path("CHANGES.rst")
PYPROJECT_IN_TOML = Path("pyproject.in.toml")
PYPROJECT_TOML = Path("pyproject.toml")
README_DIST_RST = Path("README-dist.rst")
README_RST = Path("README.rst")
SETUP_CFG = Path("setup.cfg")
VERSION_PY = Path("pathspec/_version.py")


def generate_changes_rst() -> None:
	"""
	Generate the "CHANGES.rst" file from "CHANGES_0.in.rst" and
	"CHANGES_1.in.rst".
	"""
	output: list[str] = []
	output.append("Change History\n")
	output.append("=" * 14)
	output.append("\n\n")

	print(f"Read: {CHANGES_1_IN_RST}")
	output.append(CHANGES_1_IN_RST.read_text())

	print(f"Read: {CHANGES_0_IN_RST}")
	output.append("\n")
	output.append(CHANGES_0_IN_RST.read_text())

	print(f"Write: {CHANGES_RST}")
	CHANGES_RST.write_text("".join(output))


def generate_pyproject_toml() -> None:
	"""
	Generate the "pyproject.toml" file from "pyproject.in.toml".
	"""
	# Flit will only statically extract the version from a predefined list of
	# files for an editable install for some odd reason.
	# - See <https://github.com/pypa/flit/issues/386>.

	print(f"Read: {PYPROJECT_IN_TOML}")
	output = PYPROJECT_IN_TOML.read_text()

	print(f"Read: {VERSION_PY}")
	version_input = VERSION_PY.read_text()
	version = re.search(
		'^__version__\\s*=\\s*["\'](.+)["\']', version_input, re.M,
	).group(1)

	# Replace version.
	output = output.replace("__VERSION__", version)

	print(f"Write: {PYPROJECT_TOML}")
	PYPROJECT_TOML.write_text(output)


def generate_readme_dist() -> None:
	"""
	Generate the "README-dist.rst" file from "README.rst" and "CHANGES_1.in.rst".
	"""
	output: list[str] = []

	print(f"Read: {README_RST}")
	output.append(README_RST.read_text())

	print(f"Read: {CHANGES_1_IN_RST}")
	output.append("\n\n")
	output.append("Change History\n")
	output.append("=" * 14)
	output.append("\n\n")
	output.append(CHANGES_1_IN_RST.read_text())

	print(f"Write: {README_DIST_RST}")
	README_DIST_RST.write_text("".join(output))


def generate_setup_cfg() -> None:
	"""
	Generate the "setup.cfg" file from "pyproject.toml" in order to support legacy
	installation with "setup.py".
	"""
	print(f"Read: {PYPROJECT_TOML}")
	with PYPROJECT_TOML.open('rb') as fh:
		config = tomllib.load(fh)

	print(f"Write: {SETUP_CFG}")
	output = configparser.ConfigParser()
	output['metadata'] = {
		'author': config['project']['authors'][0]['name'],
		'author_email': config['project']['authors'][0]['email'],
		'classifiers': "\n" + "\n".join(config['project']['classifiers']),
		'description': config['project']['description'],
		'license': config['project']['license']['text'],
		'long_description': f"file: {config['project']['readme']}",
		'long_description_content_type': "text/x-rst",
		'name': config['project']['name'],
		'url': config['project']['urls']['Source Code'],
		'version': "attr: pathspec._version.__version__",
	}
	output['options'] = {
		'packages': "find:",
		'python_requires': config['project']['requires-python'],
		'setup_requires': "setuptools>=40.8.0",
		'test_suite': "tests",
	}
	output['options.packages.find'] = {
		'include': "pathspec, pathspec.*",
	}

	with SETUP_CFG.open('w') as fh:
		output.write(fh)


def main() -> int:
	"""
	Run the script.
	"""
	# Parse command-line arguments.
	parser = argparse.ArgumentParser(description=__doc__)
	parser.parse_args()

	generate_changes_rst()
	generate_readme_dist()
	generate_pyproject_toml()
	generate_setup_cfg()

	return 0


if __name__ == '__main__':
	sys.exit(main())
