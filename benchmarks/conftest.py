
from pathlib import (
	Path)

import pytest

from pathspec.util import (
	iter_tree_files)


@pytest.fixture(scope='session')
def cpython_dir() -> Path:
	return Path("~/Downloads/cpython").expanduser()


@pytest.fixture(scope='session')
def cpython_files(cpython_dir: Path) -> set[str]:
	return set(iter_tree_files(cpython_dir))


@pytest.fixture(scope='session')
def cpython_gi_file(cpython_dir: Path) -> Path:
	return cpython_dir / ".gitignore"


@pytest.fixture(scope='session')
def cpython_gi_lines_all(cpython_gi_file: Path) -> list[str]:
	return cpython_gi_file.read_text().splitlines()


@pytest.fixture(scope='session')
def cpython_gi_lines_filt(cpython_gi_lines_all: list[str]) -> list[str]:
	return [
		__line
		for __line in cpython_gi_lines_all
		if __line and not __line.startswith("#")
	]
