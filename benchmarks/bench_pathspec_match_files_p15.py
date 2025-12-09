"""
This module benchmarks `PathSpec.match_files()` using 15 pattern.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	PathSpec)

GROUP = "PathSpec.match_files(): 15 lines, 6.5k files"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_15: list[str],
):
	spec = PathSpec.from_lines(
		'gitignore',
		cpython_gi_lines_15,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_files)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_15: list[str],
):
	spec = PathSpec.from_lines(
		'gitignore',
		cpython_gi_lines_15,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_files)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_15: list[str],
):
	spec = PathSpec.from_lines(
		'gitignore',
		cpython_gi_lines_15,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


def run_match(spec: PathSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
