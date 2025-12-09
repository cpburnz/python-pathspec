"""
This module benchmarks `GitIgnoreSpec.match_files()` using 150 patterns.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec)

GROUP = "GitIgnoreSpec.match_files(): 150 lines, 6.5k files"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_files: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_files)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1(
	benchmark: BenchmarkFixture,
	cpython_files: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_files)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1(
	benchmark: BenchmarkFixture,
	cpython_files: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


def run_match(spec: GitIgnoreSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
