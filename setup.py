"""
This setup script only exists to support installations where pip cannot
be used such as for system packages.
"""

import setuptools
import sys

if int(setuptools.__version__.split(".")[0]) < 61:
	sys.stderr.write((
		"WARNING: Installed version of setuptools, {version}, is too old. "
		"Version 61.0.0 is required for the pyproject.toml configuration "
		"to load. This will most likely build and install as a packaged "
		"named 'UNKNOWN'.\n"
	).format(version=setuptools.__version__))

setuptools.setup()
