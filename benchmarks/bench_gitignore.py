"""
This module defines benchmarks for :class:`.GitIgnoreSpec`.
"""

# TODO: Hatchling uses GitIgnoreSpec.match_file(). Benchmark individual files.

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec)
from pathspec.gitignore import (
	_GiDefaultMatcher)
from benchmarks.match_gitignore import (
	GiHyperscanR1BlockClosureMatcher,
	GiHyperscanR1BlockStateMatcher,
	GiHyperscanR1StreamClosureMatcher,
	GiHyperscanR1StreamStateMatcher,
	GiHyperscanR2BlockClosureMatcher,
	GiHyperscanR2BlockStateMatcher,
	GiHyperscanR2StreamClosureMatcher)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_filtered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_filt)
	spec._matcher = _GiDefaultMatcher(spec.patterns, no_reverse=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_filtered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_filt)
	spec._matcher = _GiDefaultMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_unfiltered(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all)
	spec._matcher = _GiDefaultMatcher(spec.patterns, no_filter=True, no_reverse=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_unfiltered_reversed(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all)
	spec._matcher = _GiDefaultMatcher(spec.patterns, no_filter=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_def_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR1BlockClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR1BlockStateMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r1_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR1StreamClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


# WARNING: This segfaults.
# @pytest.mark.benchmark(group="GitIgnore.match_files")
# def bench_hs_r1_stream_state(
# 	benchmark: BenchmarkFixture,
# 	cpython_files: set[str],
# 	cpython_gi_lines_all: list[str],
# ):
# 	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
# 	spec._matcher = GiHyperscanStreamStateMatcher(spec.patterns)
# 	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR2BlockClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR2BlockStateMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_r2_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	spec._matcher = GiHyperscanR2StreamClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_hs_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize='hyperscan')
	benchmark(run_match, spec, cpython_files)


def run_match(spec: GitIgnoreSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
