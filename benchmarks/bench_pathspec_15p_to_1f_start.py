"""
This module benchmarks :class:`.PathSpec` using ~15 patterns against one file
matching at the start of the patterns.
"""

from functools import (
	partial)

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	PathSpec)
from pathspec._backends.simple.pathspec import (
	SimplePsBackend)

from benchmarks.hyperscan_pathspec_r1 import (
	HyperscanPsR1BlockClosureBackend,
	HyperscanPsR1BlockStateBackend,
	HyperscanPsR1StreamClosureBackend)

GROUP = "PathSpec.match_file(): 15 lines, one file (start)"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1BlockClosureBackend,
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1BlockStateBackend,
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1StreamClosureBackend,
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_file_match_start)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_v1(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='re2',
	)
	benchmark(run_match, spec, flit_file_match_start)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_reverse=True)
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered_reversed(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='simple',
		_test_backend_factory=SimplePsBackend,
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_filter=True)
	)
	benchmark(run_match, spec, flit_file_match_start)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1(
	benchmark: BenchmarkFixture,
	flit_file_match_start: str,
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		flit_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, flit_file_match_start)


def run_match(spec: PathSpec, file: str):
	_match = spec.match_file(file)
