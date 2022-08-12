"""
This script generates files required for source and wheel distributions.
"""

import argparse
import sys


def generate_readme_dist() -> None:
	"""
	Generate the "README-dist.rst" file from "README.rst" and
	"CHANGES.rst".
	"""
	print("Read: README.rst")
	with open("README.rst", 'r', encoding='utf8') as fh:
		output = fh.read()

	print("Read: CHANGES.rst")
	with open("CHANGES.rst", 'r', encoding='utf8') as fh:
		output += "\n\n"
		output += fh.read()

	print("Write: README-dist.rst")
	with open("README-dist.rst", 'w', encoding='utf8') as fh:
		fh.write(output)


def main() -> int:
	"""
	Run the script.
	"""
	# Parse command-line arguments.
	parser = argparse.ArgumentParser(description=__doc__)
	parser.parse_args(sys.argv[1:])

	generate_readme_dist()

	return 0


if __name__ == '__main__':
	sys.exit(main())
