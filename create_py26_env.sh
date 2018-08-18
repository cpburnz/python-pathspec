#!/bin/bash
#
# This script creates the Python 2.6 virtual environment for testing at
# ".py26-env". This is required because Tox has removed support for Python
# 2.6.
#
# NOTE: This requires 'python2.6' to be installed and 'virtualenv' for it.
#
set -e

if ! which python2.6 > /dev/null; then
	echo "Command 'python2.6' not found. Please install Python 2.6."
	echo
	echo "On Ubuntu, you can download and install Python 2.6 from the deadsnakes PPA by"
	echo "executing the following:"
	echo
	echo "sudo add-apt-repository ppa:deadsnakes/ppa"
	echo "sudo apt-get update"
	echo "sudo apt-get install python2.6"
	echo
	echo "Once Python 2.6 is installed, please run this script again."
	exit 1
fi

if python2.6 -c 'import virtualenv' 2>&1 | grep -q 'No module named virtualenv'; then
	echo "Module 'virtualenv' not found. Please install virtualenv 15.2.0 for Python 2.6."
	echo
	echo "You can download and install virtualenv from PyPI by executing the following:"
	echo
	echo "wget https://files.pythonhosted.org/packages/b1/72/2d70c5a1de409ceb3a27ff2ec007ecdd5cc52239e7c74990e32af57affe9/virtualenv-15.2.0.tar.gz"
	echo "tar -xzf virtualenv-15.2.0.tar.gz"
	echo "cd virtualenv-15.2.0"
	echo "python2.6 setup.py build"
	echo "sudo python2.6 setup.py install"
	echo
	echo "Once virtualenv is installed, please run this script again."
	exit 1
fi

# Create environment.
python2.6 -m virtualenv .py26-env

# Activate environment.
cd .py26-env
source bin/activate

# Install test dependencies.
pip install unittest2
