#
# This Makefile is used to manage development and distribution.
#

.PHONY: build create-venv help prebuild publish test test-all test-docs update-venv

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
	@echo "  test         Run tests using the development virtual environment."
	@echo "  test-all     Run tests using Tox for all virtual environments."
	@echo "  test-docs    Run tests using Tox for just documentation."
	@echo "  update-venv  Update the development Python virtual environment."

build: dist-build

create-venv: dev-venv-create

prebuild: dist-prebuild

publish: dist-publish

test: dev-test-primary

test-all: dev-test-all

test-docs: dev-test-docs

update-venv: dev-venv-install


################################################################################
# Development
################################################################################

SRC_DIR := ./
VENV_DIR := ./dev/venv

PYTHON := python3
VENV := ./dev/venv.sh "${VENV_DIR}"

.PHONY: dev-test-all dev-test-docs dev-test-primary dev-venv-base dev-venv-create dev-venv-install

dev-test-all:
	${VENV} tox

dev-test-docs:
	${VENV} tox -e docs

dev-test-primary:
	${VENV} python -m unittest -v

dev-venv-base:
	${PYTHON} -m venv --clear "${VENV_DIR}"

dev-venv-create: dev-venv-base dev-venv-install

dev-venv-install:
	${VENV} pip install --upgrade pip setuptools wheel
	${VENV} pip install --upgrade build sphinx tomli tox twine typing-extensions
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
	${VENV} twine upload -r pathspec --skip-existing ./dist/*
