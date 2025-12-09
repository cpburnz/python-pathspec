
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
	return [
		__line for __line in cpython_gi_file.read_text().splitlines()
		if __line and not __line.startswith('#')
	]


@pytest.fixture(scope='session')
def cpython_gi_lines_1(cpython_gi_lines_all: list[str]) -> list[str]:
	return [
		"*.cover",
	]


@pytest.fixture(scope='session')
def cpython_gi_lines_5(cpython_gi_lines_all: list[str]) -> list[str]:
	return [
		"*.cover",
		"*.iml",
		"Modules/config.c",
		"CLAUDE.local.md",
		"Doc/data/python*.abi",
	]


@pytest.fixture(scope='session')
def cpython_gi_lines_15(cpython_gi_lines_all: list[str]) -> list[str]:
	return (
		cpython_gi_lines_all[:5]
		+ cpython_gi_lines_all[82:87]
		+ cpython_gi_lines_all[-5:]
	)


@pytest.fixture(scope='session')
def cpython_gi_lines_25(cpython_gi_lines_all: list[str]) -> list[str]:
	return (
		cpython_gi_lines_all[:10]
		+ cpython_gi_lines_all[82:87]
		+ cpython_gi_lines_all[-10:]
	)


@pytest.fixture(scope='session')
def cpython_gi_lines_50(cpython_gi_lines_all: list[str]) -> list[str]:
	return (
		cpython_gi_lines_all[:20]
		+ cpython_gi_lines_all[80:90]
		+ cpython_gi_lines_all[-20:]
	)


@pytest.fixture(scope='session')
def cpython_gi_lines_100(cpython_gi_lines_all: list[str]) -> list[str]:
	return (
		cpython_gi_lines_all[:40]
		+ cpython_gi_lines_all[80:100]
		+ cpython_gi_lines_all[-40:]
	)


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
