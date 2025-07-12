
from pathlib import (
	Path)

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec.util import (
	iter_tree_entries,
	iter_tree_files)


@pytest.mark.benchmark(group="iter_tree_entries", warmup=True)
def bench_iter_tree_entries(benchmark: BenchmarkFixture, cpython_dir: Path):
	benchmark(run_iter_tree_entries, cpython_dir)


@pytest.mark.benchmark(group="iter_tree_files", warmup=True)
def bench_iter_tree_files_v0(benchmark: BenchmarkFixture, cpython_dir: Path):
	benchmark(run_iter_tree_files_v0, cpython_dir)


@pytest.mark.benchmark(group="iter_tree_files", warmup=True)
def bench_iter_tree_files_v1(benchmark: BenchmarkFixture, cpython_dir: Path):
	benchmark(run_iter_tree_files_v1, cpython_dir)


def run_iter_tree_entries(path: Path):
	for _ in iter_tree_entries(path):
		pass


def run_iter_tree_files_v0(path: Path):
	for entry in iter_tree_entries(path):
		if not entry.is_dir():
			pass


def run_iter_tree_files_v1(path: Path):
	for _ in iter_tree_files(path):
		pass
