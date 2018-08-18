#!/bin/bash
#
# This script creates the Python 2.6 virtual environment for testing at
# ".py26-env". This is required because Tox has removed support for Python
# 2.6.
#
set -e

# Create environment.
python2.6 -m virtualenv .py26-env

# Activate environment.
cd .py26-env
source bin/activate

# Install test dependencies.
pip install unittest2
