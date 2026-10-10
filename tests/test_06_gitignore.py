"""
This script tests :class:`.GitIgnoreSpec`.
"""

import itertools
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
	Any,
	Callable,  # Replaced by `collections.abc.Callable` in 3.9.2.
	Optional,  # Replaced by `X | None` in 3.10.
	Protocol)
from unittest import (
	SkipTest,
	TestCase)

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


class SubTestContext(Protocol):
	def __call__(self) -> AbstractContextManager[GitIgnoreSpec]:
		...


class GitIgnoreSpecMixin(object):
	"""
	The :class:`GitIgnoreSpecMixin` class provides utility methods used by the
	tests.
	"""

	def parameterize_from_lines(
		self,
		lines: Iterable[AnyStr],
		sub_params: Optional[dict[str, Any]] = None,
	) -> Iterator[SubTestContext]:
		"""
		Parameterize `GitIgnoreSpec.from_lines()` for each backend and configuration
		to begin a subtest.

		*lines* (:class:`Iterable` of :class:`str`) yields the lines.

		*sub_params* (:class:`dict`) contains additional parameters for the
		subtest.

		Yields each subtest context (:class:`SubTestContext`) for the
		:class:`GitIgnoreSpec`.
		"""
		lines = list(lines)

		if sub_params is None:
			sub_params = {}

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
				with self.subTest(label, **sub_params):
					raise
				continue

			@contextmanager
			def _sub_test(
				_backend=backend,
				_backend_factory=backend_factory,
				_label=label,
			):
				has_error = False
				with self.subTest(_label, **sub_params):
					try:
						spec = GitIgnoreSpec.from_lines(
							lines,
							backend=_backend,
							_test_backend_factory=_backend_factory,
						)
					except Exception:
						has_error = True
						raise

					yield spec

				if has_error:
					raise Exception("Subtest failed.")

			yield _sub_test


class GitIgnoreSpecTest(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecTest` class tests the :class:`.GitIgnoreSpec` class.
	"""

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

	def test_02_dir_reinclusion_whitelist(self):
		"""
		Test that a directory re-included by a directory-only pattern is not
		reported as ignored.

		The whitelist idiom ("*" ignores everything, "!*/" keeps descending into
		directories, "!*.py" keeps the files of interest) only works if asking
		about the directory answers what Git answers. A consumer asks about the
		directory precisely to decide whether to descend, so reporting "sub/" as
		ignored silently drops every file below it.
		"""
		for sub_test in self.parameterize_from_lines([
			'*',
			'!*/',
			'!*.py',
		]):
			with sub_test() as spec:
				# Confirmed results with git check-ignore (v2.55.0).
				dirs = {
					'sub/',    # 2:!*/
					'sub/d/',  # 2:!*/
				}
				self.assertEqual({_dir for _dir in dirs if spec.match_file(_dir)}, set())

				# Confirmed results with git check-ignore (v2.55.0).
				files = {
					'a.py',        # 3:!*.py
					'a.txt',       # 1:*
					'sub/b.py',    # 3:!*.py
					'sub/b.txt',   # 1:*
					'sub/d/c.py',  # 3:!*.py
				}

				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)

				self.assertEqual(ignores, {
					'a.txt',
					'sub/b.txt',
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


class GitIgnoreSpecIssue19Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue19Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #19.
	"""

	def test_a(self):
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

	def test_b(self):
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

	def test_c(self):
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


class GitIgnoreSpecIssue39Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue39Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #39.
	"""

	def test_1(self):
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


class GitIgnoreSpecIssue41Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue41Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #41.
	"""

	def test_a(self):
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

	def test_b(self):
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

	def test_c(self):
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


class GitIgnoreSpecIssue62Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue62Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #62.
	"""

	def test_1(self):
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


class GitIgnoreSpecIssue64Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue64Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #64.
	"""

	def test_1(self):
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


class GitIgnoreSpecIssue74Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue74Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #74.
	"""

	def test_1(self):
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


class GitIgnoreSpecIssue81Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue81Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #81.
	"""

	def test_a(self):
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

	def test_b(self):
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

	def test_c(self):
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


class GitIgnoreSpecIssue100Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue100Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #100.
	"""

	def test_1(self):
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


class GitIgnoreSpecIssue129Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue129Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #129.
	"""

	def test_a1(self):
		"""
		Test issue 129, a file negation under an excluded directory.
		"""
		for sub_test in self.parameterize_from_lines([
			"build",
			"!keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"build/keep.log",  # 1:build
					"keep.log",        # 2:!keep.log
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"build/keep.log",
				}, debug)
				self.assertEqual(files - ignores, {
					"keep.log",
				}, debug)

	def test_a2(self):
		"""
		Test issue 129, a file negation under an excluded directory.
		"""
		for sub_test in self.parameterize_from_lines([
			"build/*",
			"!keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"build/keep.log",  # 2:!keep.log
					"keep.log",        # 2:!keep.log
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, set(), debug)
				self.assertEqual(files - ignores, {
					"build/keep.log",
					"keep.log",
				}, debug)

	def test_a3(self):
		"""
		Test issue 129, a file negation under an excluded directory.
		"""
		for sub_test in self.parameterize_from_lines([
			"build/**",
			"!keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"build/keep.log",  # 2:!keep.log
					"keep.log",        # 2:!keep.log
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, set(), debug)
				self.assertEqual(files - ignores, {
					"build/keep.log",
					"keep.log",
				}, debug)

	def test_b(self):
		"""
		Test issue 129, a file negation naming the excluded directory, and a
		grandparent.
		"""
		for sub_test in self.parameterize_from_lines([
			"build",
			"!build/keep.log",
			"a",
			"!a/b/keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.54.0).
				files = {
					"build/keep.log",  # 1:build
					"a/b/keep.log",    # 3:a
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, files, debug)

	def test_c1(self):
		"""
		Test issue 129, re-inclusion that must keep working: the directory itself is
		not excluded, or its exclusion is undone before the file negation.
		"""
		for sub_test in self.parameterize_from_lines([
			"build/*",
			"!build/keep.log",
			"log",
			"!log/",
			"!log/keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"build/keep.log",  # 2:!build/keep.log
					"build/drop.log",  # 1:build/*
					"log/keep.log",    # 5:!log/keep.log
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"build/drop.log",
				}, debug)
				self.assertEqual(files - ignores, {
					"build/keep.log",
					"log/keep.log",
				}, debug)

	def test_c2(self):
		"""
		Test issue 129, re-inclusion that must keep working: the directory itself is
		not excluded, or its exclusion is undone before the file negation.
		"""
		for sub_test in self.parameterize_from_lines([
			"build/**",
			"!build/keep.log",
			"log",
			"!log/",
			"!log/keep.log",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"build/keep.log",  # 2:!build/keep.log
					"build/drop.log",  # 1:build/**
					"log/keep.log",    # 5:!log/keep.log
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"build/drop.log",
				}, debug)
				self.assertEqual(files - ignores, {
					"build/keep.log",
					"log/keep.log",
				}, debug)


class GitIgnoreSpecIssue134Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue134Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #134.
	"""

	def test_1(self):
		"""
		Test a forward and reverse evaluation discrepancy.
		"""
		for sub_test in self.parameterize_from_lines([
			"!**/node_modules/**",
			"/node_modules",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					"node_modules",           # 2:/node_modules
					"node_modules/",          # 2:/node_modules
					"node_modules/leaf.txt",  # 2:/node_modules
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"node_modules",
					"node_modules/",
					"node_modules/leaf.txt",
				}, debug)


class GitIgnoreSpecIssue137Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue137Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #137.
	"""

	def test_a(self):
		"""
		Test that trailing glob-stars do not ignore parent.
		"""
		for sub_test in self.parameterize_from_lines([
			"d/**",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				# - NOTICE: Technically, there is a discrepancy on matching "d/" but git
				#   does not actually match on directories, only files.
				files = {
					"d",         # -
					"d/",        # 1:d/** - Discrepancy
					"d/file",    # 1:d/**
					"d/child/",  # 1:d/**
					"d/\nfile",  # 1:d/**
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					"d/file",
					"d/child/",
					"d/\nfile",
				}, debug)
				self.assertEqual(files - ignores, {
					"d",
					"d/",
				})

	def test_b(self):
		"""
		Test that the excluded ancestor rule does not fire on an ancestor which the
		spec itself re-includes.
		"""
		for sub_test in self.parameterize_from_lines([
			".*",
			"!**/node_modules/**",
		]):
			with sub_test() as spec:
				# Confirmed results with git (v2.55.0).
				files = {
					".hidden",                                      # 1:.*
					"vendor/keep.txt",                              # -
					"vendor/.cache/y.txt",                          # 1:.*
					"vendor/deps/npm/node_modules/keep.txt",        # 2:!**/node_modules/**
					"vendor/deps/npm/node_modules/.bin/x.txt",      # 2:!**/node_modules/**
					"vendor/deps/npm/node_modules/.bin/.hide.txt",  # 2:!**/node_modules/**
					"node_modules/.bin/z.txt",                      # 2:!**/node_modules/**
				}
				results = list(spec.check_files(files))
				ignores = get_includes(results)
				debug = debug_results(spec, results)
				self.assertEqual(ignores, {
					".hidden",
					"vendor/.cache/y.txt",
				}, debug)


class GitIgnoreSpecIssue139Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue139Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #139.
	"""

	def test_1(self):
		"""
		Test that glob-stars match newlines in names.
		"""
		for pattern, path in [
			("target", "line\nbreak/target"),
			("*/target", "line\nbreak/target"),
			("**/target", "line\nbreak/target"),
			("root/*/target", "root/line\nbreak/target"),
			("root/**/target", "root/line\nbreak/target"),
			("*/target", "\n/target"),
			("**/target", "\n/target"),
		]:
			for sub_test in self.parameterize_from_lines([pattern]):
				with sub_test() as spec:
					self.assertTrue(spec.match_file(path))


class GitIgnoreSpecIssue150Test(GitIgnoreSpecMixin, TestCase):
	"""
	The :class:`GitIgnoreSpecIssue150Test` class tests the :class:`.GitIgnoreSpec`
	implementation for issue #150.
	"""

	def test_1_stream_lines(self):
		"""
		Test handling of trailing tabs, non-breaking spaces, and em-spaces.
		"""
		for suffix, ending in itertools.product(
			('\t', '\xa0', '\u2003'),
			('\n', '\r\n'),
		):
			name = f"foo{suffix}"
			for sub_test in self.parameterize_from_lines(
				[name + ending],
				sub_params=dict(suffix=suffix, ending=ending),
			):
				with sub_test() as spec:
					self.assertTrue(spec.match_file(name))
					self.assertFalse(spec.match_file('foo'))

	def test_2_negation_and_directories_1(self):
		"""
		Test handling of negation and directories.
		"""
		for suffix in ('\t', '\xa0', '\u2003'):
			name = f"foo{suffix}"
			for sub_test in self.parameterize_from_lines(
				["*", f"!{name}"],
				sub_params=dict(suffix=suffix),
			):
				with sub_test() as spec:
					self.assertFalse(spec.match_file(name))
					self.assertTrue(spec.match_file('foo'))

	def test_2_negation_and_directories_2(self):
		"""
		Test handling of negation and directories.
		"""
		for suffix in ('\t', '\xa0', '\u2003'):
			name = f"foo{suffix}"
			for sub_test in self.parameterize_from_lines(
				[f"{name}/"],
				sub_params=dict(suffix=suffix),
			):
				with sub_test() as spec:
					self.assertTrue(spec.match_file(f"{name}/"))
					self.assertTrue(spec.match_file(f"{name}/child"))
					self.assertFalse(spec.match_file(name))
					self.assertFalse(spec.match_file("foo/child"))

	def test_3_character_after_slash(self):
		"""
		Test handling of characters after a slash.
		"""
		for suffix in ('\t', '\xa0', '\u2003'):
			name = f"foo/{suffix}"
			for sub_test in self.parameterize_from_lines(
				[name],
				sub_params=dict(suffix=suffix),
			):
				with sub_test() as spec:
					self.assertTrue(spec.match_file(name))
					self.assertFalse(spec.match_file('foo/'))
					self.assertFalse(spec.match_file('foo/other'))
