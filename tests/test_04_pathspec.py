"""
This script tests :class:`.PathSpec`.
"""

import os
import shutil
import tempfile
import unittest
from collections.abc import (
	Callable,
	Iterable,
	Iterator,
	Sequence)
from contextlib import (
	AbstractContextManager,
	contextmanager)
from functools import (
	partial)
from pathlib import (
	Path)
from typing import (
	Optional)  # Replaced by `X | None` in 3.10.
from unittest import (
	SkipTest)

from pathspec import (
	PathSpec)
from pathspec.backend import (
	BackendNamesHint,
	_Backend)
from pathspec._backends.hyperscan.pathspec import (
	HyperscanPsBackend)
from pathspec._backends.re2.pathspec import (
	Re2PsBackend)
from pathspec._backends.simple.pathspec import (
	SimplePsBackend)
from pathspec.pattern import (
	Pattern)
from pathspec.patterns.gitignore.base import (
	GitIgnorePatternError)
from pathspec._typing import (
	AnyStr)  # Removed in 3.18.
from pathspec.util import (
	iter_tree_entries)

from .util import (
	CheckResult,
	debug_includes,
	debug_results,
	get_includes,
	get_paths_from_entries,
	make_dirs,
	make_files,
	ospath,
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


class PathSpecTest(unittest.TestCase):
	"""
	The :class:`PathSpecTest` class tests the :class:`.PathSpec` class.
	"""

	def clear_temp_dir(self) -> None:
		"""
		Clear the temp directory.
		"""
		for path in os.scandir(self.temp_dir):
			shutil.rmtree(path.path)

	def make_dirs(self, dirs: Iterable[str]) -> None:
		"""
		Create the specified directories.
		"""
		make_dirs(self.temp_dir, dirs)

	def make_files(self, files: Iterable[str]) -> None:
		"""
		Create the specified files.
		"""
		return make_files(self.temp_dir, files)

	def parameterize_from_lines(
		self,
		pattern_factory: str,
		lines: Iterable[AnyStr],
	) -> Iterator[Callable[[], AbstractContextManager[PathSpec]]]:
		"""
		Parameterize `PathSpec.from_lines()` for each backend and configuration to
		begin a subtest.

		*pattern_factory* (:class:`str`) is the pattern factory.

		*lines* (:class:`Iterable` of :class:`str`) yields the lines.

		Returns an :class:`Iterator` yielding each subtest context for the
		:class:`PathSpec`.
		"""
		lines = list(lines)

		configs: list[tuple[
			str, BackendNamesHint, Optional[Callable[[Sequence[Pattern]], _Backend]]
		]] = []

		# Simple backend, no optimizations.
		configs.append((
			"simple (unopt)",
			'simple',
			partial(SimplePsBackend, no_filter=True, no_reverse=True),
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
					partial(HyperscanPsBackend, _debug_exprs=True),
				))
				configs.append((
					f"hyperscan (reverse)",
					backend,
					partial(HyperscanPsBackend, _debug_exprs=True, _test_sort=reverse_inplace)
				))
				configs.append((
					f"hyperscan (shuffle)",
					backend,
					partial(HyperscanPsBackend, _debug_exprs=True, _test_sort=shuffle_inplace)
				))
			elif backend == 're2':
				configs.append((
					f"re2 (forward)",
					backend,
					partial(Re2PsBackend, _debug_regex=True),
				))
				configs.append((
					f"re2 (reverse)",
					backend,
					partial(Re2PsBackend, _debug_regex=True, _test_sort=reverse_inplace),
				))
				configs.append((
					f"re2 (shuffle)",
					backend,
					partial(Re2PsBackend, _debug_regex=True, _test_sort=shuffle_inplace),
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
				self.clear_temp_dir()
				with self.subTest(label):
					yield PathSpec.from_lines(
						pattern_factory,
						lines,
						backend=backend,
						_test_backend_factory=backend_factory,
					)

			yield _sub_test

	def setUp(self) -> None:
		"""
		Called before each test.
		"""
		self.temp_dir = Path(tempfile.mkdtemp())

	def tearDown(self) -> None:
		"""
		Called after each test.
		"""
		shutil.rmtree(self.temp_dir)

	def test_01_absolute_dir_paths_1(self):
		"""
		Tests that absolute paths will be properly normalized and matched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'foo',
		]):
			with sub_test() as spec:
				files = {
					'/a.py',
					'/foo/a.py',
					'/x/a.py',
					'/x/foo/a.py',
					'a.py',
					'foo/a.py',
					'x/a.py',
					'x/foo/a.py',
				}

				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'/foo/a.py',
					'/x/foo/a.py',
					'foo/a.py',
					'x/foo/a.py',
				}, debug)

	def test_01_absolute_dir_paths_2(self):
		"""
		Tests that absolute paths will be properly normalized and matched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'/foo',
		]):
			with sub_test() as spec:
				files = {
					'/a.py',
					'/foo/a.py',
					'/x/a.py',
					'/x/foo/a.py',
					'a.py',
					'foo/a.py',
					'x/a.py',
					'x/foo/a.py',
				}

				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'/foo/a.py',
					'foo/a.py',
				}, debug)

	def test_01_check_file_1_include(self):
		"""
		Test checking a single file that is included.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				result = spec.check_file("include.txt")
				debug = debug_results(spec, [result])

				self.assertEqual(result, CheckResult("include.txt", True, 0), debug)

	def test_01_check_file_2_exclude(self):
		"""
		Test checking a single file that is excluded.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				result = spec.check_file("test/exclude.txt")
				debug = debug_results(spec, [result])

				self.assertEqual(result, CheckResult("test/exclude.txt", False, 1), debug)

	def test_01_check_file_3_unmatch(self):
		"""
		Test checking a single file that is unmatched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				result = spec.check_file("unmatch.bin")
				debug = debug_results(spec, [result])

				self.assertEqual(result, CheckResult("unmatch.bin", None, None), debug)

	def test_01_check_file_4_many(self):
		"""
		Test that checking files one at a time yields the same results as checking
		multiples files at once.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'test1/a.txt',
					'test1/b.txt',
					'test1/c/c.txt',
					'test2/a.txt',
					'test2/b.txt',
					'test2/c/c.txt',
				}

				single_results = set(map(spec.check_file, files))
				multi_results = set(spec.check_files(files))
				debug = debug_results(spec, single_results)

				self.assertEqual(single_results, multi_results, debug)

	def test_01_check_match_files(self):
		"""
		Test that checking files and matching files yield the same results.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/**',
		]):
			with sub_test() as spec:
				files = {
					'src/test1/a.txt',
					'src/test1/b.txt',
					'src/test1/c/c.txt',
					'src/test2/a.txt',
					'src/test2/b.txt',
					'src/test2/c/c.txt',
				}

				check_results = set(spec.check_files(files))
				check_includes = get_includes(check_results)
				match_files = set(spec.match_files(files))
				debug = debug_results(spec, check_results)

				self.assertEqual(check_includes, match_files, debug)

	def test_01_current_dir_paths(self):
		"""
		Tests that paths referencing the current directory will be properly
		normalized and matched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'./src/test1/a.txt',
					'./src/test1/b.txt',
					'./src/test1/c/c.txt',
					'./src/test2/a.txt',
					'./src/test2/b.txt',
					'./src/test2/c/c.txt',
				}

				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'./src/test2/a.txt',
					'./src/test2/b.txt',
					'./src/test2/c/c.txt',
				}, debug)

	def test_01_empty_path_1(self):
		"""
		Tests that patterns that end with an escaped space will be treated properly.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'\\ ',
			'abc\\ ',
		]):
			with sub_test() as spec:
				files = {
					' ',
					'  ',
					'abc ',
					'somefile',
				}

				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					' ',
					'abc ',
				}, debug)

	def test_01_empty_path_2(self):
		"""
		Tests that patterns that end with an escaped space will be treated properly.
		"""
		with self.assertRaises(GitIgnorePatternError):
			# An escape with double spaces is invalid. Disallow it. Better to be
			# safe than sorry.
			PathSpec.from_lines('gitignore', [
				'\\  ',
			], backend='simple')

	def test_01_match_file_1_include(self):
		"""
		Test matching a single file that is included.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				include = spec.match_file("include.txt")

				self.assertIs(include, True)

	def test_01_match_file_2_exclude(self):
		"""
		Test matching a single file that is excluded.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				file = 'test/exclude.txt'

				include = spec.match_file(file)
				includes = {file} if include else {}
				debug = debug_includes(spec, {file}, includes)

				self.assertIs(include, False, debug)

	def test_01_match_file_3_unmatch(self):
		"""
		Test match a single file that is unmatched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			"*.txt",
			"!test/",
		]):
			with sub_test() as spec:
				file = 'unmatch.bin'

				include = spec.match_file(file)
				includes = {file} if include else {}
				debug = debug_includes(spec, {file}, includes)

				self.assertIs(include, False, debug)

	def test_01_match_files(self):
		"""
		Test that matching files one at a time yields the same results as matching
		multiples files at once.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'test1/a.txt',
					'test1/b.txt',
					'test1/c/c.txt',
					'test2/a.txt',
					'test2/b.txt',
					'test2/c/c.txt',
				}

				single_files = set(filter(spec.match_file, files))
				multi_files = set(spec.match_files(files))
				debug = debug_includes(spec, files, single_files)

				self.assertEqual(single_files, multi_files, debug)

	def test_01_windows_current_dir_paths(self):
		"""
		Tests that paths referencing the current directory will be properly
		normalized and matched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'.\\test1\\a.txt',
					'.\\test1\\b.txt',
					'.\\test1\\c\\c.txt',
					'.\\test2\\a.txt',
					'.\\test2\\b.txt',
					'.\\test2\\c\\c.txt',
				}

				results = list(spec.check_files(files, separators=['\\']))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'.\\test2\\a.txt',
					'.\\test2\\b.txt',
					'.\\test2\\c\\c.txt',
				}, debug)

	def test_01_windows_paths(self):
		"""
		Tests that Windows paths will be properly normalized and matched.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!test1/',
		]):
			with sub_test() as spec:
				files = {
					'test1\\a.txt',
					'test1\\b.txt',
					'test1\\c\\c.txt',
					'test2\\a.txt',
					'test2\\b.txt',
					'test2\\c\\c.txt',
				}

				results = list(spec.check_files(files, separators=['\\']))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'test2\\a.txt',
					'test2\\b.txt',
					'test2\\c\\c.txt',
				}, debug)

	def test_02_eq(self):
		"""
		Tests equality.
		"""
		first_spec = PathSpec.from_lines('gitignore', [
			'*.txt',
			'!test1/**',
		], backend='simple')
		second_spec = PathSpec.from_lines('gitignore', [
			'*.txt',
			'!test1/**',
		], backend='simple')
		self.assertEqual(first_spec, second_spec)

	def test_02_ne(self):
		"""
		Tests inequality.
		"""
		first_spec = PathSpec.from_lines('gitignore', [
			'*.txt',
		], backend='simple')
		second_spec = PathSpec.from_lines('gitignore', [
			'!*.txt',
		], backend='simple')
		self.assertNotEqual(first_spec, second_spec)

	def test_03_add(self):
		"""
		Test spec addition using :data:`+` operator.
		"""
		first_spec = PathSpec.from_lines('gitignore', [
			'test.png',
			'test.txt',
		], backend='simple')
		second_spec = PathSpec.from_lines('gitignore', [
			'test.html',
			'test.jpg',
		], backend='simple')
		combined_spec = first_spec + second_spec
		files = {
			'test.html',
			'test.jpg',
			'test.png',
			'test.txt',
		}

		results = list(combined_spec.check_files(files))
		includes = get_includes(results)
		debug = debug_results(combined_spec, results)

		self.assertEqual(includes, {
			'test.html',
			'test.jpg',
			'test.png',
			'test.txt',
		}, debug)

	def test_03_iadd(self):
		"""
		Test spec addition using :data:`+=` operator.
		"""
		spec = PathSpec.from_lines('gitignore', [
			'test.png',
			'test.txt',
		], backend='simple')
		spec += PathSpec.from_lines('gitignore', [
			'test.html',
			'test.jpg',
		], backend='simple')
		files = {
			'test.html',
			'test.jpg',
			'test.png',
			'test.txt',
		}

		results = list(spec.check_files(files))
		includes = get_includes(results)
		debug = debug_results(spec, results)

		self.assertEqual(includes, {
			'test.html',
			'test.jpg',
			'test.png',
			'test.txt',
		}, debug)

	def test_04_len(self):
		"""
		Test spec length.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'foo',
			'bar',
		]):
			with sub_test() as spec:
				self.assertEqual(len(spec), 2)

	def test_05_match_entries(self):
		"""
		Test matching files collectively.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!b.txt',
		]):
			with sub_test() as spec:
				self.make_dirs([
					'X',
					'X/Z',
					'Y',
					'Y/Z',
				])
				self.make_files([
					'X/a.txt',
					'X/b.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/b.txt',
					'Y/Z/c.txt',
				])

				entries = iter_tree_entries(self.temp_dir)
				includes = get_paths_from_entries(spec.match_entries(entries))

				self.assertEqual(includes, set(map(ospath, [
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				])))

	def test_05_match_file(self):
		"""
		Test matching files individually.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
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

				includes = set(filter(spec.match_file, files))
				debug = debug_includes(spec, files, includes)

				self.assertEqual(includes, {
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				}, debug)

	def test_05_match_files(self):
		"""
		Test matching files collectively.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
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

				includes = set(spec.match_files(files))
				debug = debug_includes(spec, files, includes)

				self.assertEqual(includes, {
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				}, debug)

	def test_05_match_tree_entries(self):
		"""
		Test matching a file tree.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!b.txt',
		]):
			with sub_test() as spec:
				files = set(map(ospath, [
					'X/a.txt',
					'X/b.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/b.txt',
					'Y/Z/c.txt',
				]))

				self.make_dirs([
					'X',
					'X/Z',
					'Y',
					'Y/Z',
				])
				self.make_files(files)

				entries = spec.match_tree_entries(self.temp_dir)
				includes = get_paths_from_entries(entries)
				debug = debug_includes(spec, files, includes)

				self.assertEqual(includes, set(map(ospath, [
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				])), debug)

	def test_05_match_tree_files(self):
		"""
		Test matching a file tree.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.txt',
			'!b.txt',
		]):
			with sub_test() as spec:
				files = set(map(ospath, [
					'X/a.txt',
					'X/b.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/b.txt',
					'Y/Z/c.txt',
				]))

				self.make_dirs([
					'X',
					'X/Z',
					'Y',
					'Y/Z',
				])
				self.make_files(files)

				includes = set(spec.match_tree_files(self.temp_dir))
				debug = debug_includes(spec, files, includes)

				self.assertEqual(includes, set(map(ospath, [
					'X/a.txt',
					'X/Z/c.txt',
					'Y/a.txt',
					'Y/Z/c.txt',
				])), debug)

	def test_06_issue_41_a(self):
		"""
		Test including a file and excluding a directory with the same name pattern,
		scenario A.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.yaml',
			'!*.yaml/',
		]):
			with sub_test() as spec:
				files = {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/file.yaml',
					'dir/index.txt',
					'file.yaml',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					#'dir.yaml/file.yaml',  # Discrepancy with Git.
					'dir/file.yaml',
					'file.yaml',
				}, debug)
				self.assertEqual(files - ignores, {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',  # Discrepancy with Git.
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/index.txt',
				}, debug)

	def test_06_issue_41_b(self):
		"""
		Test including a file and excluding a directory with the same name
		pattern, scenario B.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'!*.yaml/',
			'*.yaml',
		]):
			with sub_test() as spec:
				files = {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/file.yaml',
					'dir/index.txt',
					'file.yaml',
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

	def test_06_issue_41_c(self):
		"""
		Test including a file and excluding a directory with the same name
		pattern, scenario C.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*.yaml',
			'!dir.yaml',
		]):
			with sub_test() as spec:
				files = {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/file.yaml',
					'dir/index.txt',
					'file.yaml',
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					#'dir.yaml/file.yaml',  # Discrepancy with Git.
					'dir/file.yaml',
					'file.yaml',
				}, debug)
				self.assertEqual(files - ignores, {
					'dir.yaml/file.sql',
					'dir.yaml/file.yaml',  # Discrepancy with Git.
					'dir.yaml/index.txt',
					'dir/file.sql',
					'dir/index.txt',
				}, debug)

	def test_07_issue_62(self):
		"""
		Test including all files and excluding a directory.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'*',
			'!product_dir/',
		]):
			with sub_test() as spec:
				files = {
					'anydir/file.txt',
					'product_dir/file.txt',
				}

				results = list(spec.check_files(files))
				includes = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(includes, {
					'anydir/file.txt',
				}, debug)

	def test_08_issue_39(self):
		"""
		Test excluding files in a directory.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
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

	def test_09_issue_80_a(self):
		"""
		Test negating patterns.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'build',
			'*.log',
			'.*',
			'!.gitignore',
		]):
			with sub_test() as spec:
				files = {
					'.c-tmp',           # 3:.*
					'.gitignore',       # 4:!.gitignore
					'a.log',            # 2:*.log
					'b.txt',            # -
					'build/d.log',      # 1:build
					'build/trace.bin',  # 1:build
					'trace.c',          # -
				}

				keeps = set(spec.match_files(files, negate=True))
				includes = files - keeps
				debug = debug_includes(spec, files, includes)

				self.assertEqual(keeps, {
					'.gitignore',
					'b.txt',
					'trace.c',
				}, debug)

	def test_09_issue_80_b(self):
		"""
		Test negating patterns.
		"""
		for sub_test in self.parameterize_from_lines('gitignore', [
			'build',
			'*.log',
			'.*',
			'!.gitignore',
		]):
			with sub_test() as spec:
				files = {
					'.c-tmp',           # 3:.*
					'.gitignore',       # 4:!.gitignore
					'a.log',            # 2:*.log
					'b.txt',            # -
					'build/d.log',      # 1:build
					'build/trace.bin',  # 1:build
					'trace.c',          # -
				}

				keeps = set(spec.match_files(files, negate=True))
				ignores = set(spec.match_files(files))

				self.assertEqual(files - ignores, keeps)
				self.assertEqual(files - keeps, ignores)
