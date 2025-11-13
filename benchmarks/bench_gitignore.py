"""
This module defines benchmarks for :class:`.GitIgnoreSpec`.
"""

# TODO: Hatchling uses GitIgnoreSpec.match_file(). Benchmark individual files.

from functools import (
	partial)

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec)
from pathspec._backends.simple.gitignore import (
	SimpleGiBackend)
from benchmarks.match_gitignore import (
	HyperscanGiR1BlockClosureBackend,
	HyperscanGiR1BlockStateBackend,
	HyperscanGiR1StreamClosureBackend,
	HyperscanGiR1StreamStateBackend,
	HyperscanGiR2BlockClosureBackend,
	HyperscanGiR2BlockStateBackend,
	HyperscanGiR2StreamClosureBackend)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_filtered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_filt,
		backend='simple',
		_test_backend_cls=partial(SimpleGiBackend, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_filt,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_cls=partial(SimpleGiBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_cls=partial(SimpleGiBackend, no_filter=True)
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR1BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR1BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_files)


# TODO BUG: This now fails after restructuring.
@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR1StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


# WARNING: This segfaults.
# @pytest.mark.benchmark(group="GitIgnore.match_files")
# def bench_hs_r1_stream_state(
# 	benchmark: BenchmarkFixture,
# 	cpython_files: set[str],
# 	cpython_gi_lines_all: list[str],
# ):
# 	spec = GitIgnoreSpec.from_lines(
# 		cpython_gi_lines_all,
# 		backend='hyperscan',
#			_test_backend_cls=GiHyperscanStreamStateBackend,
# 	)
# 	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR2BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR2BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_files)


# TODO BUG: This now fails after restructuring.
@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_cls=HyperscanGiR2StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_files)


def run_match(spec: GitIgnoreSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
