
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
def cpython_gi_lines_25(cpython_gi_lines_all: list[str]) -> list[str]:
	return cpython_gi_lines_all[::6][:25]


@pytest.fixture(scope='session')
def cpython_gi_lines_50(cpython_gi_lines_all: list[str]) -> list[str]:
	return cpython_gi_lines_all[::3][:50]


@pytest.fixture(scope='session')
def cpython_gi_lines_100(cpython_gi_lines_all: list[str]) -> list[str]:
	return cpython_gi_lines_all[:100]


@pytest.fixture(scope='session')
def cpython_file_match_end() -> str:
	"""
	File matching pattern near the end of cpython ".gitignore".
	"""
	return "CLAUDE.local.md"


@pytest.fixture(scope='session')
def cpython_file_match_middle() -> str:
	"""
	File matching pattern near the middle of cpython ".gitignore".
	"""
	return "Modules/config.c"


@pytest.fixture(scope='session')
def cpython_file_match_none() -> str:
	"""
	File not matching any pattern in cpython ".gitignore".
	"""
	return "Unladen Swallow"


@pytest.fixture(scope='session')
def cpython_file_match_start() -> str:
	"""
	File matching pattern near the beginning of cpython ".gitignore".
	"""
	return "spam.cover"


@pytest.fixture(scope='session')
def flit_dir() -> Path:
	return Path("~/Downloads/flit").expanduser()


@pytest.fixture(scope='session')
def flit_files(flit_dir: Path) -> set[str]:
	return set(iter_tree_files(flit_dir))


@pytest.fixture(scope='session')
def flit_gi_file(flit_dir: Path) -> Path:
	return flit_dir / ".gitignore"


@pytest.fixture(scope='session')
def flit_gi_lines_all(flit_gi_file: Path) -> list[str]:
	return flit_gi_file.read_text().splitlines()


@pytest.fixture(scope='session')
def flit_gi_lines_1() -> list[str]:
	return [
		"/dist/",
	]


@pytest.fixture(scope='session')
def flit_gi_lines_2() -> list[str]:
	return [
		"/dist/",
		"*.pyc",
	]

@pytest.fixture(scope='session')
def flit_gi_lines_5() -> list[str]:
	return [
		"/dist/",
		"__pycache__/",
		"/htmlcov/",
		"*.pyc",
		".python-version",
	]


@pytest.fixture(scope='session')
def flit_file_match_end() -> str:
	"""
	File matching pattern near the end of flit ".gitignore".
	"""
	return "green.pyc"


@pytest.fixture(scope='session')
def flit_file_match_middle() -> str:
	"""
	File matching pattern near the middle of flit ".gitignore".
	"""
	return "htmlcov/eggs"


@pytest.fixture(scope='session')
def flit_file_match_none() -> str:
	"""
	File not matching any pattern in flit ".gitignore".
	"""
	return "Unladen Swallow"


@pytest.fixture(scope='session')
def flit_file_match_start() -> str:
	"""
	File matching pattern near the beginning of flit ".gitignore".
	"""
	return "dist/ham"
