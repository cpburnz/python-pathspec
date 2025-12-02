"""
This module benchmarks `PathSpec.match_file()` using ~25 patterns.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	PathSpec)

GROUP = "PathSpec.match_file(): 25 lines, one file"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_end(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_middle(
	benchmark: BenchmarkFixture,
	cpython_file_match_middle: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_middle)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_none(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_start(
	benchmark: BenchmarkFixture,
	cpython_file_match_start: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_start)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_end(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_middle(
	benchmark: BenchmarkFixture,
	cpython_file_match_middle: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_file_match_middle)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_none(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_start(
	benchmark: BenchmarkFixture,
	cpython_file_match_start: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='re2',
	)
	benchmark(run_match, spec, cpython_file_match_start)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_end(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_middle(
	benchmark: BenchmarkFixture,
	cpython_file_match_middle: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_middle)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_none(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_start(
	benchmark: BenchmarkFixture,
	cpython_file_match_start: str,
	cpython_gi_lines_25: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_25,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_start)


def run_match(spec: PathSpec, file: str):
	_match = spec.match_file(file)
