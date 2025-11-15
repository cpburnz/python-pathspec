"""
This script tests :class:`.GitIgnoreSpec`.
"""

import unittest
from collections.abc import (
	Callable,
	Iterable,
	Iterator)
from contextlib import (
	AbstractContextManager,
	contextmanager)
from functools import (
	partial)
from typing import (
	AnyStr)
from unittest import (
	SkipTest)

from pathspec._backends.simple.gitignore import (
	SimpleGiBackend)
from pathspec.gitignore import (
	GitIgnoreSpec)

from .util import (
	BACKEND_PARAMS,
	debug_results,
	get_includes,
	require_backend)


class GitIgnoreSpecTest(unittest.TestCase):
	"""
	The :class:`GitIgnoreSpecTest` class tests the :class:`.GitIgnoreSpec` class.
	"""

	def parameterize_from_lines(
		self,
		lines: Iterable[AnyStr],
	) -> Iterator[Callable[[], AbstractContextManager[GitIgnoreSpec]]]:
		"""
		Parameterize `PathSpec.from_lines()` for each optimization and begin a
		subtest.

		*pattern_factory* (:class:`str`) is the pattern factory.

		*lines* (:class:`Iterable` of :class:`str`) yields the lines.

		Returns an :class:`Iterator` yielding each context for the
		:class:`GitIgnoreSpec`.
		"""
		lines = list(lines)

		@contextmanager
		def _unopt_sub_test():
			with self.subTest("simple (unopt)"):
				spec = GitIgnoreSpec.from_lines(
					lines,
					backend='simple',
					_test_backend_factory=partial(SimpleGiBackend, no_filter=True, no_reverse=True),
				)
				yield spec

		yield _unopt_sub_test

		@contextmanager
		def _minopt_sub_test():
			with self.subTest("simple (minopt)"):
				yield GitIgnoreSpec.from_lines(lines, backend='simple')

		yield _minopt_sub_test

		for label, backend in BACKEND_PARAMS:
			try:
				require_backend(backend)
			except SkipTest:
				with self.subTest(label):
					raise
				continue

			@contextmanager
			def _optimize_sub_test(label=label, backend=backend):
				with self.subTest(label):
					yield GitIgnoreSpec.from_lines(lines, backend=backend)

			yield _optimize_sub_test

	def test_01_reversed_args(self):
		"""
		Test reversed args for `.from_lines()`.
		"""
		spec = GitIgnoreSpec.from_lines('gitwildmatch', ['*.txt'])
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
					'test1/b.bin',
					'test1/a.txt',
					'test1/c/c.txt',
					'test2/a.txt',
					'test2/b.bin',
					'test2/c/c.txt',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'test1/b.bin',
					'test1/a.txt',
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
