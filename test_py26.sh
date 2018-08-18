#!/bin/bash
#
# This script tests Python 2.6 using the virtual environment at ".py26-env".
# This is required because Tox has removed support for Python 2.6.
#
set -e

# Activate environment.
cd .py26-env
source bin/activate

# Install pathspec.
cd ..
python setup.py clean --all
python setup.py build
python setup.py install

# Test pathspec.
python setup.py test
