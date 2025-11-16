#
# This justfile is used to manage development and distribution.
#

_default:
	@just --list

# Run benchmarks.
[group('Development')]
bench: _bench

# Run tests using the CPython virtual environment.
[group('Development')]
test: _test_primary

# Run tests using Tox for all virtual environments.
[group('Development')]
test-all: _test_all

# Run tests using Tox for just documentation."
[group('Development')]
test-docs: _test_docs

# Create the CPython venv.
[group('Development')]
venv-cpy-create: _venv_cpy_base _venv_cpy_install

# Update the CPython venv.
[group('Development')]
venv-cpy-update: _venv_cpy_install

# Create the PyPy venv.
[group('Development')]
venv-pypy-create: _venv_pypy_base _venv_pypy_install

# Update the PyPy venv.
[group('Development')]
venv-pypy-update: _venv_pypy_install

# Build the package.
[group('Distribution')]
dist-build: _dist_build

# Generate files used by distribution.
[group('Distribution')]
dist-prebuild: _dist_prebuild

# Publish the package to PyPI.
[group('Distribution')]
dist-publish: _dist_publish


################################################################################
# Development
################################################################################

cpy_bin := 'python3'
cpy_run := 'dev/venv.sh dev/venv-cpy'
pypy_bin := 'pypy3'
pypy_run := 'dev/venv.sh dev/venv-pypy'

_bench:
	{{cpy_run}} pytest -q -c benchmarks/pytest.ini

_test_all:
	{{cpy_run}} tox

_test_docs:
	{{cpy_run}} tox -e docs

_test_primary:
	{{cpy_run}} python -m unittest -v

_venv_cpy_base:
	{{cpy_bin}} -m venv --clear dev/venv-cpy

_venv_cpy_install:
	{{cpy_run}} pip install --upgrade build google-re2 google-re2-stubs hyperscan pip pytest pytest-benchmark setuptools sphinx tomli tox twine typing-extensions wheel
	{{cpy_run}} pip install -e .

_venv_pypy_base:
	{{pypy_bin}} -m venv --clear dev/venv-pypy

_venv_pypy_install:
	{{pypy_run}} pip install --upgrade hyperscan pip pytest pytest-benchmark setuptools wheel
	{{pypy_run}} pip install -e .


################################################################################
# Distribution
################################################################################

_dist_build: _dist_prebuild
	find ./dist -type f -delete
	{{cpy_run}} python -m build

_dist_prebuild:
	{{cpy_run}} python prebuild.py

_dist_publish:
	{{cpy_run}} twine check ./dist/*
	{{cpy_run}} twine upload -r pathspec --skip-existing ./dist/*
