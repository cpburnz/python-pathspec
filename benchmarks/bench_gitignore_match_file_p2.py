"""
This module benchmarks `GitIgnoreSpec.match_file()` using 2 patterns.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec)

GROUP = "GitIgnoreSpec.match_file(): 2 lines, one file"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_end(
	benchmark: BenchmarkFixture,
	flit_file_match_end: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_none(
	benchmark: BenchmarkFixture,
	flit_file_match_none: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1_start(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_file_match_start)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_end(
	benchmark: BenchmarkFixture,
	flit_file_match_end: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='re2',
	)
	benchmark(run_match, spec, flit_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_none(
	benchmark: BenchmarkFixture,
	flit_file_match_none: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='re2',
	)
	benchmark(run_match, spec, flit_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1_start(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='re2',
	)
	benchmark(run_match, spec, flit_file_match_start)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_end(
	benchmark: BenchmarkFixture,
	flit_file_match_end: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='simple',
	)
	benchmark(run_match, spec, flit_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_none(
	benchmark: BenchmarkFixture,
	flit_file_match_none: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='simple',
	)
	benchmark(run_match, spec, flit_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1_start(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_5: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		flit_gi_lines_5,
		backend='simple',
	)
	benchmark(run_match, spec, flit_file_match_start)


def run_match(spec: GitIgnoreSpec, file: str):
	_match = spec.match_file(file)
