"""
This module benchmarks :class:`.GitIgnoreSpec` using many patterns against one
file matching at the end of the patterns.
"""

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
	HyperscanGiR2BlockClosureBackend,
	HyperscanGiR2BlockStateBackend,
	HyperscanGiR2StreamClosureBackend)

GROUP = "GitIgnore.match_file(): 180 lines, one file (end)"


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR1BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR1BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR1StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r2_block_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR2BlockClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r2_block_state(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR2BlockStateBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_r2_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
		_test_backend_factory=HyperscanGiR2StreamClosureBackend,
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimpleGiBackend, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimpleGiBackend, no_filter=True, no_reverse=True)
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
		_test_backend_factory=partial(SimpleGiBackend, no_filter=True)
	)
	benchmark(run_match, spec, cpython_file_match_end)


@pytest.mark.benchmark(group=GROUP)
def bench_sm_v1(
	benchmark: BenchmarkFixture,
	cpython_file_match_end: str,
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		cpython_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, cpython_file_match_end)


def run_match(spec: GitIgnoreSpec, file: str):
	_match = spec.match_file(file)
