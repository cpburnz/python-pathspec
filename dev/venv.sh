#!/bin/sh
#
# This script activates the given Python virtual environment, and then
# executes the given command.
#
# Author: Caleb P. Burns
# License: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
# Version: 1.0.0
#

if [ "$1" = '-h' ] || [ "$1" = '--help' ] || [ "$#" -lt 2 ]; then
	echo 'Usage: venv.sh [-h] <venv> <command> [<args>...]'
	echo
	echo 'Activate the Python virtual environment, and then execute the command.'
	echo
	echo 'Arguments:'
	echo '  <venv>      The Python virtual environment directory to activate.'
	echo '  <command>   The command to execute.'
	echo '  <args>...   Any arguments for the command.'
	echo '  -h, --help  Show this help message and exit.'
	exit 1
fi

# Pop venv argument.
venv="$1"
shift

# Activate venv.
. "$venv/bin/activate"

# Execute command.
"$@"
