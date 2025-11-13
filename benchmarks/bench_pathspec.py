"""
This module defines benchmarks for :class:`.PathSpec`.
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
from benchmarks.match_pathspec import (
	HyperscanPsR1BlockClosureBackend,
	HyperscanPsR1BlockStateBackend,
	HyperscanPsR1StreamClosureBackend,
	HyperscanPsR1StreamStateBackend)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_def_filtered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_filt,
		backend='simple',
		_test_backend_cls=partial(SimplePsBackend, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_def_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_filt,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_def_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_cls=partial(SimplePsBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_def_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_cls=partial(SimplePsBackend, no_filter=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_def_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_filt,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanPsR1BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanPsR1BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_files)


# TODO BUG: This now fails after restructuring.
@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanPsR1StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


# WARNING: This segfaults.
# @pytest.mark.benchmark(group="PathSpec.match_files")
# def bench_hs_r1_stream_state(
# 	benchmark: BenchmarkFixture,
# 	cpython_files: set[str],
# 	cpython_gi_lines_all: list[str],
# ):
#		spec = PathSpec.from_lines(
#			'gitwildmatch',
#			cpython_gi_lines_all,
#			backend='hyperscan',
#			_test_backend_cls=HyperscanPsR1StreamStateBackend,
#		)
# 	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		'gitwildmatch',
		cpython_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_files)


def run_match(spec: PathSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
