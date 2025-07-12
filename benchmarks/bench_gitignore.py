
import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec)
from benchmarks.patches import (
	match_files_v0)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_all_v0(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all)
	spec.match_files = match_files_v0.__get__(spec)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_all_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_filt_v0(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_filt)
	spec.match_files = match_files_v0.__get__(spec)
	benchmark(run_match, spec, cpython_files)


@pytest.mark.benchmark(group="GitIgnore.match_files")
def bench_filt_v1(
	benchmark: BenchmarkFixture,
	cpython_files: set[str],
	cpython_gi_lines_filt: list[str],
):
	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_filt)
	benchmark(run_match, spec, cpython_files)


# TODO
# def bench_opt_v0(
# 	benchmark: BenchmarkFixture,
# 	cpython_files: set[str],
# 	cpython_gi_lines_all: list[str],
# ):
# 	spec = GitIgnoreSpec.from_lines(cpython_gi_lines_all, optimize=True)
# 	benchmark(run_match, spec, cpython_files)


def run_match(spec: GitIgnoreSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
