"""
This module benchmarks :class:`.PathSpec` using many patterns against one file
not matching any patterns.
"""

from functools import (
	partial)

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	PathSpec)
from pathspec._backends.re2.pathspec import (
	Re2PsBackend)
from pathspec._backends.simple.pathspec import (
	SimplePsBackend)
from benchmarks.match_pathspec import (
	HyperscanPsR1BlockClosureBackend,
	HyperscanPsR1BlockStateBackend,
	HyperscanPsR1StreamClosureBackend)

GROUP = "PathSpec.match_file(): 180 lines, one file (none)"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanPsR1StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_none)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP)
def bench_re2_filtered(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='re2',
		_test_backend_factory=partial(Re2PsBackend, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='re2',
		_test_backend_factory=Re2PsBackend,
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='re2',
		_test_backend_factory=partial(Re2PsBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_re2_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='re2',
		_test_backend_factory=partial(Re2PsBackend, no_filter=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


# Simple backend.

@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=SimplePsBackend,
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimplePsBackend, no_filter=True)
	)
	benchmark(run_match, spec, cpython_file_match_none)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1(
	benchmark: BenchmarkFixture,
	cpython_file_match_none: str,
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_none)


def run_match(spec: PathSpec, file: str):
	_match = spec.match_file(file)
