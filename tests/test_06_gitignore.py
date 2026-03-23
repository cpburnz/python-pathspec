"""
This script tests :class:`.GitIgnoreSpec`.
"""

import unittest
from collections.abc import (
	Iterable,
	Iterator,
	Sequence)
from contextlib import (
	AbstractContextManager,
	contextmanager)
from functools import (
	partial)
from typing import (
	Callable,  # Replaced by `collections.abc.Callable` in 3.9.2.
	Optional)  # Replaced by `X | None` in 3.10.
from unittest import (
	SkipTest)

from pathspec.backend import (
	BackendNamesHint,
	_Backend)
from pathspec._backends.hyperscan.gitignore import (
	HyperscanGiBackend)
from pathspec._backends.re2.gitignore import (
	Re2GiBackend)
from pathspec._backends.simple.gitignore import (
	SimpleGiBackend)
from pathspec.gitignore import (
	GitIgnoreSpec)
from pathspec.pattern import (
	Pattern)
from pathspec._typing import (
	AnyStr)  # Removed in 3.18.

from .util import (
	debug_results,
	get_includes,
	require_backend,
	reverse_inplace,
	shuffle_inplace)

BACKENDS: list[BackendNamesHint] = [
	'hyperscan',
	're2',
]
"""
The backend parameters.
"""


class GitIgnoreSpecTest(unittest.TestCase):
	"""
	The :class:`GitIgnoreSpecTest` class tests the :class:`.GitIgnoreSpec` class.
	"""

	def parameterize_from_lines(
		self,
		lines: Iterable[AnyStr],
	) -> Iterator[Callable[[], AbstractContextManager[GitIgnoreSpec]]]:
		"""
		Parameterize `GitIgnoreSpec.from_lines()` for each backend and configuration
		to begin a subtest.

		*pattern_factory* (:class:`str`) is the pattern factory.

		*lines* (:class:`Iterable` of :class:`str`) yields the lines.

		Returns an :class:`Iterator` yielding each context for the
		:class:`GitIgnoreSpec`.
		"""
		lines = list(lines)

		configs: list[tuple[
			str, BackendNamesHint, Optional[Callable[[Sequence[Pattern]], _Backend]]
		]] = []

		# Simple backend, no optimizations.
		configs.append((
			"simple (unopt)",
			'simple',
			partial(SimpleGiBackend, no_filter=True, no_reverse=True),
		))

		# Simple backend, minimal optimizations.
		configs.append((
			"simple (minopt)",
			'simple',
			None,
		))

		# Add additional backends.
		for backend in BACKENDS:
			if backend == 'hyperscan':
				configs.append((
					f"hyperscan (forward)",
					backend,
					partial(HyperscanGiBackend, _debug_exprs=True),
				))
				configs.append((
					f"hyperscan (reverse)",
					backend,
					partial(HyperscanGiBackend, _debug_exprs=True, _test_sort=reverse_inplace)
				))
				configs.append((
					f"hyperscan (shuffle)",
					backend,
					partial(HyperscanGiBackend, _debug_exprs=True, _test_sort=shuffle_inplace)
				))
			elif backend == 're2':
				configs.append((
					f"re2 (forward)",
					backend,
					partial(Re2GiBackend, _debug_regex=True),
				))
				configs.append((
					f"re2 (reverse)",
					backend,
					partial(Re2GiBackend, _debug_regex=True, _test_sort=reverse_inplace)
				))
				configs.append((
					f"re2 (shuffle)",
					backend,
					partial(Re2GiBackend, _debug_regex=True, _test_sort=shuffle_inplace)
				))
			else:
				configs.append((
					backend,
					backend,
					None,
				))

		for label, backend, backend_factory in configs:
			try:
				require_backend(backend)
			except SkipTest:
				with self.subTest(label):
					raise
				continue

			@contextmanager
			def _sub_test(
				backend=backend,
				backend_factory=backend_factory,
				label=label,
			):
				with self.subTest(label):
					yield GitIgnoreSpec.from_lines(
						lines,
						backend=backend,
						_test_backend_factory=backend_factory,
					)

			yield _sub_test

	def test_01_reversed_args(self):
		"""
		Test reversed args for `.from_lines()`.
		"""
		spec = GitIgnoreSpec.from_lines('gitignore', ['*.txt'])
		files = {
			'a.txt',
			'b.bin',
		}

		results = list(spec.check_files(files))
		ignores = get_includes(results)
		debug = debug_results(spec, results)

		self.assertEqual(ignores, {
			'a.txt',
		}, debug)

	def test_02_dir_exclusions(self):
		"""
		Test directory exclusions.
		"""
		for sub_test in self.parameterize_from_lines([
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'test1/a.txt',
					'test1/b.bin',
					'test1/c/c.txt',
					'test2/a.txt',
					'test2/b.bin',
					'test2/c/c.txt',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'test1/a.txt',
					'test1/c/c.txt',
					'test2/a.txt',
					'test2/c/c.txt',
				}, debug)
				self.assertEqual(files - ignores, {
					'test1/b.bin',
					'test2/b.bin',
				}, debug)

	def test_02_file_exclusions(self):
		"""
		Test file exclusions.
		"""
		for sub_test in self.parameterize_from_lines([
			'*.txt',
			'!b.txt',
		]):
			with sub_test() as spec:
				files = {
					'X/a.txt',
					'X/b.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/b.txt',
					'Y/Z/c.txt',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				}, debug)
				self.assertEqual(files - ignores, {
					'X/b.txt',
					'Y/b.txt',
				}, debug)

	def test_02_issue_41_a(self):
		"""
		Test including a file and excluding a directory with the same name pattern,
		scenario A.
		"""
		for sub_test in self.parameterize_from_lines([
			'*.yaml',
			'!*.yaml/',
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.42.0).
				files = {
					'dir.yaml/file.sql',   # -
					'dir.yaml/file.yaml',  # 1:*.yaml
					'dir.yaml/index.txt',  # -
					'dir/file.sql',        # -
					'dir/file.yaml',       # 1:*.yaml
					'dir/index.txt',       # -
					'file.yaml',           # 1:*.yaml
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dir.yaml/file.yaml',
					'dir/file.yaml',
					'file.yaml',
				}, debug)
				self.assertEqual(files - ignores, {
					'dir.yaml/file.sql',
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/index.txt',
				}, debug)

	def test_02_issue_41_b(self):
		"""
		Test including a file and excluding a directory with the same name pattern,
		scenario B.
		"""
		for sub_test in self.parameterize_from_lines([
			'!*.yaml/',
			'*.yaml',
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.42.0).
				files = {
					'dir.yaml/file.sql',   # 2:*.yaml
					'dir.yaml/file.yaml',  # 2:*.yaml
					'dir.yaml/index.txt',  # 2:*.yaml
					'dir/file.sql',        # -
					'dir/file.yaml',       # 2:*.yaml
					'dir/index.txt',       # -
					'file.yaml',           # 2:*.yaml
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',
					'dir.yaml/index.txt',
					'dir/file.yaml',
					'file.yaml',
				}, debug)
				self.assertEqual(files - ignores, {
					'dir/file.sql',
					'dir/index.txt',
				}, debug)

	def test_02_issue_41_c(self):
		"""
		Test including a file and excluding a directory with the same name pattern,
		scenario C.
		"""
		for sub_test in self.parameterize_from_lines([
			'*.yaml',
			'!dir.yaml',
		]):
			with sub_test() as spec:
				# Confirmed results with git check-ignore (v2.42.0).
				files = {
					'dir.yaml/file.sql',   # -
					'dir.yaml/file.yaml',  # 1:*.yaml
					'dir.yaml/index.txt',  # -
					'dir/file.sql',        # -
					'dir/file.yaml',       # 1:*.yaml
					'dir/index.txt',       # -
					'file.yaml',           # 1:*.yaml
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dir.yaml/file.yaml',
					'dir/file.yaml',
					'file.yaml',
				}, debug)
				self.assertEqual(files - ignores, {
					'dir.yaml/file.sql',
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/index.txt',
				}, debug)

	def test_03_subdir(self):
		"""
		Test matching files in a subdirectory of an included directory.
		"""
		for sub_test in self.parameterize_from_lines([
			"dirG/",
		]):
			with sub_test() as spec:
				files = {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}, debug)
				self.assertEqual(files - ignores, {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
				}, debug)

	def test_03_issue_19_a(self):
		"""
		Test matching files in a subdirectory of an included directory, scenario A.
		"""
		for sub_test in self.parameterize_from_lines([
			"dirG/",
		]):
			with sub_test() as spec:
				files = {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}, debug)
				self.assertEqual(files - ignores, {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
				}, debug)

	def test_03_issue_19_b(self):
		"""
		Test matching files in a subdirectory of an included directory, scenario B.
		"""
		for sub_test in self.parameterize_from_lines([
			"dirG/*",
		]):
			with sub_test() as spec:
				files = {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}, debug)
				self.assertEqual(files - ignores, {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
				}, debug)

	def test_03_issue_19_c(self):
		"""
		Test matching files in a subdirectory of an included directory, scenario C.
		"""
		for sub_test in self.parameterize_from_lines([
			"dirG/**",
		]):
			with sub_test() as spec:
				files = {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'dirG/dirH/fileI',
					'dirG/dirH/fileJ',
					'dirG/fileO',
				}, debug)
				self.assertEqual(files - ignores, {
					'fileA',
					'fileB',
					'dirD/fileE',
					'dirD/fileF',
				}, debug)

	def test_04_issue_62(self):
		"""
		Test including all files and excluding a directory.
		"""
		for sub_test in self.parameterize_from_lines([
			'*',
			'!product_dir/',
		]):
			with sub_test() as spec:
				files = {
					'anydir/file.txt',
					'product_dir/file.txt',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'anydir/file.txt',
					'product_dir/file.txt',
				}, debug)

	def test_05_issue_39(self):
		"""
		Test excluding files in a directory.
		"""
		for sub_test in self.parameterize_from_lines([
			'*.log',
			'!important/*.log',
			'trace.*',
		]):
			with sub_test() as spec:
				files = {
					'a.log',
					'b.txt',
					'important/d.log',
					'important/e.txt',
					'trace.c',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'a.log',
					'trace.c',
				}, debug)
				self.assertEqual(files - ignores, {
					'b.txt',
					'important/d.log',
					'important/e.txt',
				}, debug)

	def test_06_issue_64(self):
		"""
		Test using a double asterisk pattern.
		"""
		for sub_test in self.parameterize_from_lines([
			"**",
		]):
			with sub_test() as spec:
				files = {
					'x',
					'y.py',
					'A/x',
					'A/y.py',
					'A/B/x',
					'A/B/y.py',
					'A/B/C/x',
					'A/B/C/y.py',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, files, debug)

	def test_07_issue_74(self):
		"""
		Test include directory should override exclude file.
		"""
		for sub_test in self.parameterize_from_lines([
			'*',  # Ignore all files by default
			'!*/',  # but scan all directories
			'!*.txt',  # Text files
			'/test1/**',  # ignore all in the directory
		]):
			with sub_test() as spec:
				files = {
					'test1/a.txt',    # 4:/test1/**
					'test1/b.bin',    # 4:/test1/**
					'test1/c/c.txt',  # 4:/test1/**
					'test2/a.txt',    # -
					'test2/b.bin',    # 1:*
					'test2/c/c.txt',  # -
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'test1/a.txt',
					'test1/b.bin',
					'test1/c/c.txt',
					'test2/b.bin',
				}, debug)
				self.assertEqual(files - ignores, {
					'test2/a.txt',
					'test2/c/c.txt',
				}, debug)

	def test_08_issue_81_a(self):
		"""
		Test issue 81 whitelist, scenario A.
		"""
		for sub_test in self.parameterize_from_lines([
			"*",
			"!libfoo",
			"!libfoo/**",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.42.0).
				files = {
					"ignore.txt",          # 1:*
					"libfoo/__init__.py",  # 3:!libfoo/**
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					"ignore.txt",
				}, debug)
				self.assertEqual(files - ignores, {
					"libfoo/__init__.py",
				}, debug)

	def test_08_issue_81_b(self):
		"""
		Test issue 81 whitelist, scenario B.
		"""
		for sub_test in self.parameterize_from_lines([
			"*",
			"!libfoo",
			"!libfoo/*",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.42.0).
				files = {
					"ignore.txt",          # 1:*
					"libfoo/__init__.py",  # 3:!libfoo/*
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					"ignore.txt",
				}, debug)
				self.assertEqual(files - ignores, {
					"libfoo/__init__.py",
				}, debug)

	def test_08_issue_81_c(self):
		"""
		Test issue 81 whitelist, scenario C.
		"""
		for sub_test in self.parameterize_from_lines([
			"*",
			"!libfoo",
			"!libfoo/",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.42.0).
				files = {
					"ignore.txt",          # 1:*
					"libfoo/__init__.py",  # 1:*
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"ignore.txt",
					"libfoo/__init__.py",
				}, debug)
				self.assertEqual(files - ignores, set())

	def test_09_issue_100(self):
		"""
		Test an empty list of patterns.
		"""
		for sub_test in self.parameterize_from_lines([]):
			with sub_test() as spec:
				files = {'foo'}
				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(includes, set(), debug)
