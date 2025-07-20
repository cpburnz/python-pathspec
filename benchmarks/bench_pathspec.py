"""
This module defines benchmarks for :class:`.PathSpec`.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	PathSpec)
from pathspec.match import (
	DefaultMatcher)
from benchmarks.match import (
	HyperscanBlockClosureMatcher,
	HyperscanBlockStateMatcher,
	HyperscanStreamClosureMatcher,
	HyperscanStreamStateMatcher)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_all_v0(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all)
	spec._matcher = DefaultMatcher(spec.patterns, no_filter=True, no_reverse=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_all_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all)
	spec._matcher = DefaultMatcher(spec.patterns, no_filter=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_filt_v0(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_filt)
	spec._matcher = DefaultMatcher(spec.patterns, no_reverse=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_filt_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_filt)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_opt_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all, optimize=True)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_opt_block_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all, optimize=True)
	spec._matcher = HyperscanBlockClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_opt_block_state(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all, optimize=True)
	spec._matcher = HyperscanBlockStateMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="PathSpec.match_files")
def bench_opt_stream_closure(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all, optimize=True)
	spec._matcher = HyperscanStreamClosureMatcher(spec.patterns)
	benchmark(run_match, spec, cpython_files)


# WARNING: This segfaults.
# @pytest.mark.benchmark(group="PathSpec.match_files")
# def bench_opt_stream_state(
# 	benchmark: BenchmarkFixture,
# 	cpython_files: set[str],
# 	cpython_gi_lines_all: list[str],
# ):
# 	spec = PathSpec.from_lines('gitwildmatch', cpython_gi_lines_all, optimize=True)
# 	spec._matcher = HyperscanStreamStateMatcher(spec.patterns)
# 	benchmark(run_match, spec, cpython_files)


def run_match(spec: PathSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
