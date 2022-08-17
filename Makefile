#
# This Makefile is used to manage development and distribution.
#
# Created: 2022-08-11
# Updated: 2022-08-16
#

.PHONY: build create-venv help prebuild publish test test-all update-venv

help:
	@echo "Usage: make [<target>]"
	@echo
	@echo "General Targets:"
	@echo "  help      Display this help message."
	@echo
	@echo "Distribution Targets:"
	@echo "  build     Build the package."
	@echo "  prebuild  Generate files used by distribution."
	@echo "  publish   Publish the package to PyPI."
	@echo
	@echo "Development Targets:"
	@echo "  create-venv  Create the development Python virtual environment."
	@echo "  test         Run tests using Tox for the development virtual environment."
	@echo "  test-all     Run tests using Tox for all virtual environments."
	@echo "  update-venv  Update the development Python virtual environment."

build: dist-build

create-venv: dev-venv-create

prebuild: dist-prebuild

publish: dist-publish

test: dev-test-primary

test-all: dev-test-all

update-venv: dev-venv-install


################################################################################
# Development
################################################################################

SRC_DIR := ./
VENV_DIR := ./dev/venv

PYTHON := python3
VENV := ./dev/venv.sh "${VENV_DIR}"

.PHONY: dev-test-all dev-test-primary dev-venv-base dev-venv-create dev-venv-install

dev-test-all:
	${VENV} python -m tox

dev-test-primary:
	${VENV} python -m tox -e "py$(shell ${PYTHON} -c 'import sys;print(*sys.version_info[:2],sep="")')"

dev-venv-base:
	${PYTHON} -m venv --clear "${VENV_DIR}"

dev-venv-create: dev-venv-base dev-venv-install

dev-venv-install:
	${VENV} pip install --upgrade pip setuptools wheel
	${VENV} pip install --upgrade build sphinx tox twine
	${VENV} pip install -e "${SRC_DIR}"


################################################################################
# Distribution
################################################################################

.PHONY: dist-build dist-prebuild dist-publish

dist-build: dist-prebuild
	find ./dist -type f -delete
	${VENV} python -m build

dist-prebuild:
	${VENV} python ./prebuild.py

dist-publish: dist-build
	${VENV} twine check ./dist/*
	${VENV} twine upload --skip-existing ./dist/*
