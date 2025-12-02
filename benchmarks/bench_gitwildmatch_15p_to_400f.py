"""
This module benchmarks :class:`.GitWildMatchPattern` using ~15 patterns against
~400 files.
"""

import pytest
from pytest_benchmark.fixture import (
	BenchmarkFixture)

from pathspec import (
	GitIgnoreSpec,
	PathSpec)

from benchmarks.gitwildmatch_v1 import (
	GitWildMatchV1Pattern)


GROUP_GITIGNORE = "GitWildMatchPattern: GitIgnore.match_files(): 15 lines, 400 files"

GROUP_PATHSPEC = "GitWildMatchPattern: PathSpec.match_files(): 15 lines, 400 files"


# Hyperscan backend.

@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_hs_gitignore_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_hs_gitignore_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_hs_pathspec_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_hs_pathspec_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory='gitwildmatch',
		backend='hyperscan',
	)
	benchmark(run_match, spec, flit_files)


# Re2 backend.

@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_re2_gitignore_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='re2',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_re2_gitignore_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		backend='re2',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_re2_pathspec_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='re2',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_re2_pathspec_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory='gitwildmatch',
		backend='re2',
	)
	benchmark(run_match, spec, flit_files)


# Simple backend.

@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_sm_gitignore_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='simple',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_GITIGNORE)
def bench_sm_gitignore_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = GitIgnoreSpec.from_lines(
		lines=flit_gi_lines_all,
		backend='simple',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_sm_pathspec_v1(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory=GitWildMatchV1Pattern,
		backend='simple',
	)
	benchmark(run_match, spec, flit_files)


@pytest.mark.benchmark(group=GROUP_PATHSPEC)
def bench_sm_pathspec_v2(
	benchmark: BenchmarkFixture,
	flit_files: set[str],
	flit_gi_lines_all: list[str],
):
	spec = PathSpec.from_lines(
		lines=flit_gi_lines_all,
		pattern_factory='gitwildmatch',
		backend='simple',
	)
	benchmark(run_match, spec, flit_files)


def run_match(spec: GitIgnoreSpec, files: set[str]):
	for _ in spec.match_files(files):
		pass
