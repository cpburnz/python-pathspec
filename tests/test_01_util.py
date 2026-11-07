"""
This script tests utility functions.
"""

import errno
import os
import os.path
import shutil
import tempfile
import unittest
import warnings
from collections.abc import (
	Iterable)
from functools import (
	partial)
from pathlib import (
	Path,
	PurePath)
from typing import (
	ClassVar,
	Optional)  # Replaced by `X | None` in 3.10.
from unittest import (
	TestCase)
from unittest.mock import (
	MagicMock,
	patch)

import pathspec
import pathspec.util
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.util import (
	RecursivePathError,
	check_match_file,
	detailed_match_files,
	iter_tree_entries,
	iter_tree_files,
	match_file,
	normalize_file)
from tests.util import (
	get_paths_from_entries,
	make_dirs,
	make_files,
	make_links,
	mkfile,
	ospath)


class CheckMatchFileTest(TestCase):
	"""
	The :class:`CheckMatchFileTest` class tests the :meth:`.check_match_file`
	function.
	"""

	def test_01_single_1_include(self):
		"""
		Test checking a single file that is included.
		"""
		patterns = list(enumerate(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "include.txt")

		self.assertEqual(include_index, (True, 0))

	def test_01_single_2_exclude(self):
		"""
		Test checking a single file that is excluded.
		"""
		patterns = list(enumerate(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "test/exclude.txt")

		self.assertEqual(include_index, (False, 1))

	def test_01_single_3_unmatch(self):
		"""
		Test checking a single file that is ignored.
		"""
		patterns = list(enumerate(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "unmatch.bin")

		self.assertEqual(include_index, (None, None))

	def test_02_many(self):
		"""
		Test matching files individually.
		"""
		patterns = list(enumerate(map(GitIgnoreBasicPattern, [
			'*.txt',
			'!b.txt',
		])))
		files = {
			'X/a.txt',
			'X/b.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/b.txt',
			'Y/Z/c.txt',
		}

		includes = {
			__file
			for __file in files
			if check_match_file(patterns, __file)[0]
		}

		self.assertEqual(includes, {
			'X/a.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/Z/c.txt',
		})


class DetailedMatchFilesTest(TestCase):
	"""
	Test inclusion and exclusion bookkeeping for detailed matches.
	"""

	def setUp(self):
		# Suppress deprecation warnings from usage of deprecated functions in
		# `detailed_match_files()`.
		catcher = warnings.catch_warnings()
		catcher.__enter__()
		self.addCleanup(catcher.__exit__, None, None, None)
		warnings.simplefilter('ignore', DeprecationWarning)

	def test_negation_without_previous_match(self):
		patterns = list(map(GitIgnoreBasicPattern, ['*.txt', '!*.log']))
		for all_matches in (False, True):
			with self.subTest(all_matches=all_matches):
				results = detailed_match_files(patterns, ['notes.txt', 'debug.log'], all_matches)
				self.assertEqual(set(results), {'notes.txt'})
				self.assertEqual(results['notes.txt'].patterns, [patterns[0]])

	def test_repeated_negation_and_reinclusion(self):
		patterns = list(map(GitIgnoreBasicPattern, ['*.txt', '!notes.txt', '!notes.txt', 'notes.txt']))
		for all_matches in (False, True):
			with self.subTest(all_matches=all_matches):
				results = detailed_match_files(iter(patterns), iter(['notes.txt']), all_matches)
				self.assertEqual(set(results), {'notes.txt'})
				self.assertEqual(results['notes.txt'].patterns, [patterns[-1]])

	def test_negation_removes_previous_match(self):
		patterns = list(map(GitIgnoreBasicPattern, ['*.txt', '!notes.txt']))
		self.assertEqual(detailed_match_files(patterns, ['notes.txt']), {})


class IterTreeTest(TestCase):
	"""
	The :class:`IterTreeTest` class tests :meth:`.iter_tree_entries` and
	:meth:`.iter_tree_files` functions.
	"""

	no_symlink: ClassVar[bool]
	"""
	*no_symlink* (:class:`bool`) is whether symlinks are not supported.
	"""

	def make_dirs(self, dirs: Iterable[str]) -> None:
		"""
		Create the specified directories.
		"""
		make_dirs(self.temp_dir, dirs)

	def make_files(self, files: Iterable[str]) -> None:
		"""
		Create the specified files.
		"""
		make_files(self.temp_dir, files)

	def make_links(self, links: Iterable[tuple[str, str]]) -> None:
		"""
		Create the specified links.
		"""
		make_links(self.temp_dir, links)

	def require_symlink(self) -> None:
		"""
		Skips the test if `os.symlink` is not supported.
		"""
		if self.no_symlink:
			raise unittest.SkipTest("`os.symlink` is not supported.")

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

	def test_01_files_1_entries(self):
		"""
		Tests to make sure all files are found.
		"""
		self.make_dirs([
			'Empty',
			'Dir',
			'Dir/Inner',
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
			'Dir/Inner/e',
			'Dir/Inner/f',
		])
		results = get_paths_from_entries(iter_tree_entries(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'a',
			'b',
			'Dir',
			'Dir/Inner',
			'Dir/Inner/e',
			'Dir/Inner/f',
			'Dir/c',
			'Dir/d',
			'Empty',
		])))

	def test_01_files_2_files(self):
		"""
		Tests to make sure all files are found.
		"""
		self.make_dirs([
			'Empty',
			'Dir',
			'Dir/Inner',
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
			'Dir/Inner/e',
			'Dir/Inner/f',
		])
		results = set(iter_tree_files(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'a',
			'b',
			'Dir/c',
			'Dir/d',
			'Dir/Inner/e',
			'Dir/Inner/f',
		])))

	def test_02_link_1_check_symlink(self):
		"""
		Tests whether links can be created.
		"""
		# NOTE: Windows Vista and greater supports `os.symlink` for Python 3.2+.
		no_symlink: Optional[bool] = None
		try:
			file = self.temp_dir / 'file'
			link = self.temp_dir / 'link'
			mkfile(file)

			try:
				os.symlink(file, link)
			except (AttributeError, NotImplementedError, OSError):
				no_symlink = True
			else:
				no_symlink = False

		finally:
			self.__class__.no_symlink = no_symlink

	def test_02_link_2_links_1_entries(self):
		"""
		Tests to make sure links to directories and files work.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
		])
		self.make_links([
			('ax', 'a'),
			('bx', 'b'),
			('Dir/cx', 'Dir/c'),
			('Dir/dx', 'Dir/d'),
			('DirX', 'Dir'),
		])
		results = get_paths_from_entries(iter_tree_entries(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'a',
			'ax',
			'b',
			'bx',
			'Dir',
			'Dir/c',
			'Dir/cx',
			'Dir/d',
			'Dir/dx',
			'DirX',
			'DirX/c',
			'DirX/cx',
			'DirX/d',
			'DirX/dx',
		])))

	def test_02_link_2_links_2_files(self):
		"""
		Tests to make sure links to directories and files work.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
		])
		self.make_links([
			('ax', 'a'),
			('bx', 'b'),
			('Dir/cx', 'Dir/c'),
			('Dir/dx', 'Dir/d'),
			('DirX', 'Dir'),
		])
		results = set(iter_tree_files(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'a',
			'ax',
			'b',
			'bx',
			'Dir/c',
			'Dir/cx',
			'Dir/d',
			'Dir/dx',
			'DirX/c',
			'DirX/cx',
			'DirX/d',
			'DirX/dx',
		])))

	def test_02_link_3_sideways_links_1_entries(self):
		"""
		Tests to make sure the same directory can be encountered multiple
		times via links.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
			'Dir/Target',
		])
		self.make_files([
			'Dir/Target/file',
		])
		self.make_links([
			('Ax', 'Dir'),
			('Bx', 'Dir'),
			('Cx', 'Dir/Target'),
			('Dx', 'Dir/Target'),
			('Dir/Ex', 'Dir/Target'),
			('Dir/Fx', 'Dir/Target'),
		])
		results = get_paths_from_entries(iter_tree_entries(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'Ax',
			'Ax/Ex',
			'Ax/Ex/file',
			'Ax/Fx',
			'Ax/Fx/file',
			'Ax/Target',
			'Ax/Target/file',
			'Bx',
			'Bx/Ex',
			'Bx/Ex/file',
			'Bx/Fx',
			'Bx/Fx/file',
			'Bx/Target',
			'Bx/Target/file',
			'Cx',
			'Cx/file',
			'Dx',
			'Dx/file',
			'Dir',
			'Dir/Ex',
			'Dir/Ex/file',
			'Dir/Fx',
			'Dir/Fx/file',
			'Dir/Target',
			'Dir/Target/file',
		])))

	def test_02_link_3_sideways_links_2_files(self):
		"""
		Tests to make sure the same directory can be encountered multiple
		times via links.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
			'Dir/Target',
		])
		self.make_files([
			'Dir/Target/file',
		])
		self.make_links([
			('Ax', 'Dir'),
			('Bx', 'Dir'),
			('Cx', 'Dir/Target'),
			('Dx', 'Dir/Target'),
			('Dir/Ex', 'Dir/Target'),
			('Dir/Fx', 'Dir/Target'),
		])
		results = set(iter_tree_files(self.temp_dir))
		self.assertEqual(results, set(map(ospath, [
			'Ax/Ex/file',
			'Ax/Fx/file',
			'Ax/Target/file',
			'Bx/Ex/file',
			'Bx/Fx/file',
			'Bx/Target/file',
			'Cx/file',
			'Dx/file',
			'Dir/Ex/file',
			'Dir/Fx/file',
			'Dir/Target/file',
		])))

	def test_02_link_4_recursive_links_1_entries(self):
		"""
		Tests detection of recursive links.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'Dir/file',
		])
		self.make_links([
			('Dir/Self', 'Dir'),
		])
		with self.assertRaises(RecursivePathError) as context:
			set(iter_tree_entries(self.temp_dir))

		self.assertEqual(context.exception.first_path, 'Dir')
		self.assertEqual(context.exception.second_path, ospath('Dir/Self'))

	def test_02_link_4_recursive_links_2_files(self):
		"""
		Tests detection of recursive links.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'Dir/file',
		])
		self.make_links([
			('Dir/Self', 'Dir'),
		])
		with self.assertRaises(RecursivePathError) as context:
			set(iter_tree_files(self.temp_dir))

		self.assertEqual(context.exception.first_path, 'Dir')
		self.assertEqual(context.exception.second_path, ospath('Dir/Self'))

	def test_02_link_5_recursive_circular_links_1_entries(self):
		"""
		Tests detection of recursion through circular links.
		"""
		self.require_symlink()
		self.make_dirs([
			'A',
			'B',
			'C',
		])
		self.make_files([
			'A/d',
			'B/e',
			'C/f',
		])
		self.make_links([
			('A/Bx', 'B'),
			('B/Cx', 'C'),
			('C/Ax', 'A'),
		])
		with self.assertRaises(RecursivePathError) as context:
			set(iter_tree_entries(self.temp_dir))

		self.assertIn(context.exception.first_path, ('A', 'B', 'C'))
		self.assertEqual(context.exception.second_path, {
			'A': ospath('A/Bx/Cx/Ax'),
			'B': ospath('B/Cx/Ax/Bx'),
			'C': ospath('C/Ax/Bx/Cx'),
		}[context.exception.first_path])

	def test_02_link_5_recursive_circular_links_2_files(self):
		"""
		Tests detection of recursion through circular links.
		"""
		self.require_symlink()
		self.make_dirs([
			'A',
			'B',
			'C',
		])
		self.make_files([
			'A/d',
			'B/e',
			'C/f',
		])
		self.make_links([
			('A/Bx', 'B'),
			('B/Cx', 'C'),
			('C/Ax', 'A'),
		])
		with self.assertRaises(RecursivePathError) as context:
			set(iter_tree_files(self.temp_dir))

		self.assertIn(context.exception.first_path, ('A', 'B', 'C'))
		self.assertEqual(context.exception.second_path, {
			'A': ospath('A/Bx/Cx/Ax'),
			'B': ospath('B/Cx/Ax/Bx'),
			'C': ospath('C/Ax/Bx/Cx'),
		}[context.exception.first_path])

	def test_02_link_6_detect_broken_links_1_entries(self):
		"""
		Tests that broken links are detected.
		"""
		def reraise(e):
			raise e

		self.require_symlink()
		self.make_links([
			('A', 'DOES_NOT_EXIST'),
		])
		with self.assertRaises(OSError) as context:
			set(iter_tree_entries(self.temp_dir, on_error=reraise))

		self.assertEqual(context.exception.errno, errno.ENOENT)

	def test_02_link_6_detect_broken_links_2_files(self):
		"""
		Tests that broken links are detected.
		"""
		def reraise(e):
			raise e

		self.require_symlink()
		self.make_links([
			('A', 'DOES_NOT_EXIST'),
		])
		# `iter_tree_files` does not stat the link.
		set(iter_tree_files(self.temp_dir, on_error=reraise))

	def test_02_link_7_ignore_broken_links_1_entries(self):
		"""
		Tests that broken links are ignored.
		"""
		self.require_symlink()
		self.make_links([
			('A', 'DOES_NOT_EXIST'),
		])
		results = get_paths_from_entries(iter_tree_entries(self.temp_dir))
		self.assertEqual(results, set())

	def test_02_link_7_ignore_broken_links_2_files(self):
		"""
		Tests that broken links are ignored.
		"""
		self.require_symlink()
		self.make_links([
			('A', 'DOES_NOT_EXIST'),
		])
		results = set(iter_tree_files(self.temp_dir))
		self.assertEqual(results, set())

	def test_02_link_8_no_follow_links_1_entries(self):
		"""
		Tests to make sure directory links can be ignored.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'A',
			'B',
			'Dir/C',
			'Dir/D',
		])
		self.make_links([
			('Ax', 'A'),
			('Bx', 'B'),
			('Dir/Cx', 'Dir/C'),
			('Dir/Dx', 'Dir/D'),
			('DirX', 'Dir'),
		])
		results = get_paths_from_entries(iter_tree_entries(self.temp_dir, follow_links=False))
		self.assertEqual(results, set(map(ospath, [
			'A',
			'Ax',
			'B',
			'Bx',
			'Dir',
			'Dir/C',
			'Dir/Cx',
			'Dir/D',
			'Dir/Dx',
			'DirX',
		])))

	def test_02_link_8_no_follow_links_2_files(self):
		"""
		Tests to make sure directory links can be ignored.
		"""
		self.require_symlink()
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'A',
			'B',
			'Dir/C',
			'Dir/D',
		])
		self.make_links([
			('Ax', 'A'),
			('Bx', 'B'),
			('Dir/Cx', 'Dir/C'),
			('Dir/Dx', 'Dir/D'),
			('DirX', 'Dir'),
		])
		results = set(iter_tree_files(self.temp_dir, follow_links=False))
		self.assertEqual(results, set(map(ospath, [
			'A',
			'Ax',
			'B',
			'Bx',
			'Dir/C',
			'Dir/Cx',
			'Dir/D',
			'Dir/Dx',
			'DirX',
		])))

	def test_02_link_9_no_follow_loop_links_1_files(self):
		"""
		Unfollowed links with cyclic targets are yielded without inspecting targets.
		"""
		self.require_symlink()
		for case, links in [
			('Self', [('Loop', 'Loop')]),
			('Pair', [('First', 'Second'), ('Second', 'First')]),
		]:
			with self.subTest(case=case):
				self.make_dirs([
					case,
					f'{case}/Dir',
				])
				self.make_files([
					f'{case}/kept.txt',
					f'{case}/Dir/child.txt',
				])
				self.make_links([
					(f'{case}/{link}', f'{case}/{target}')
					for link, target in links
				])
				errors = []
				results = set(iter_tree_files(
					self.temp_dir / case, follow_links=False, on_error=errors.append,
				))
				self.assertEqual(errors, [])
				self.assertEqual(results, {
					'kept.txt',
					ospath('Dir/child.txt'),
					*[link for link, _ in links],
				})

	def test_02_link_9_no_follow_loop_links_2_entries(self):
		"""
		Unfollowed links with cyclic targets are yielded without inspecting targets.
		"""
		self.require_symlink()
		for case, links in [
			('Self', [('Loop', 'Loop')]),
			('Pair', [('First', 'Second'), ('Second', 'First')]),
		]:
			with self.subTest(case=case):
				self.make_dirs([
					case,
					f'{case}/Dir',
				])
				self.make_files([
					f'{case}/kept.txt',
					f'{case}/Dir/child.txt',
				])
				self.make_links([
					(f'{case}/{link}', f'{case}/{target}')
					for link, target in links
				])
				errors = []
				results = get_paths_from_entries(iter_tree_entries(
					self.temp_dir / case, follow_links=False, on_error=errors.append,
				))
				self.assertEqual(errors, [])
				self.assertEqual(results, {
					'Dir',
					'kept.txt',
					ospath('Dir/child.txt'),
					*[link for link, _ in links],
				})

	def test_03_subdir_1_from_filesystem_root(self):
		"""
		raverse only the requested subtree when the root ends in a separator.
		"""
		self.make_files(['a.txt'])
		root = Path(self.temp_dir).anchor
		expected = {os.path.relpath(os.path.join(self.temp_dir, 'a.txt'), root)}
		for subdir in (self.temp_dir, os.path.relpath(self.temp_dir, root)):
			with self.subTest(subdir=subdir):
				self.assertEqual(set(iter_tree_files(root, subdir=subdir)), expected)
				self.assertEqual(
					get_paths_from_entries(iter_tree_entries(root, subdir=subdir)), expected)

	def test_03_subdir_2_same_root(self):
		"""
		Both an absolute root and a dot select the root itself.
		"""
		self.make_files(['a.txt'])
		for subdir in ('.', self.temp_dir):
			with self.subTest(subdir=subdir):
				self.assertEqual(set(iter_tree_files(self.temp_dir, subdir=subdir)), {'a.txt'})

	def test_03_subdir_3_rejects_outside_root(self):
		"""
		Reject parents and sibling paths sharing the root's string prefix.
		"""
		for subdir in ('..', os.path.join('..', 'other'), str(self.temp_dir) + '-other'):
			for traverse in (iter_tree_files, iter_tree_entries):
				with self.subTest(subdir=subdir, traverse=traverse):
					with self.assertRaises(ValueError):
						list(traverse(self.temp_dir, subdir=subdir))

	@unittest.skipUnless(os.path.normcase('A') == os.path.normcase('a'), 'Case-sensitive paths')
	def test_03_subdir_4_case_insensitive_root(self):
		"""
		Accept equivalent root paths with different casing on Windows.
		"""
		self.make_files(['a.txt'])
		root = str(self.temp_dir).swapcase()
		self.assertEqual(set(iter_tree_files(root, subdir=self.temp_dir)), {'a.txt'})

	def test_04_scan_missing_directory(self):
		"""
		Directory scan failures honor the error handler.
		"""
		missing = os.path.join(self.temp_dir, 'missing')
		for walk in (iter_tree_entries, iter_tree_files):
			for mode in ('ignore', 'record', 'raise'):
				with self.subTest(walk=walk.__name__, mode=mode):
					errors = []

					def on_error(error):
						errors.append(error)
						if mode == 'raise':
							raise RuntimeError('stop walking') from error

					handler = None if mode == 'ignore' else on_error
					if mode == 'raise':
						with self.assertRaisesRegex(RuntimeError, 'stop walking'):
							list(walk(missing, on_error=handler))
					else:
						self.assertEqual(list(walk(missing, on_error=handler)), [])
					if mode != 'ignore':
						self.assertEqual(len(errors), 1)
						self.assertEqual(errors[0].errno, errno.ENOENT)

	def test_04_scan_inaccessible_child(self):
		"""
		An inaccessible child does not prevent walking readable siblings.
		"""
		self.make_dirs(['blocked'])
		self.make_files(['kept.txt'])
		scandir = os.scandir
		error = PermissionError(errno.EACCES, 'permission denied', 'blocked')

		def scan(path):
			if os.path.basename(path) == 'blocked':
				raise error
			return scandir(path)

		for walk in (iter_tree_entries, iter_tree_files):
			for record in (False, True):
				with self.subTest(walk=walk.__name__, record=record):
					errors = []
					with patch('pathspec.util.os.scandir', side_effect=scan):
						results = list(walk(self.temp_dir, on_error=errors.append if record else None))
					paths = get_paths_from_entries(results) if walk is iter_tree_entries else set(results)
					self.assertIn('kept.txt', paths)
					self.assertEqual(errors, [error] if record else [])

	def test_04_scan_iteration_error(self):
		"""
		Errors advancing a directory scan honor the handler and close the scan.
		"""
		self.make_files(['readable.txt'])
		with os.scandir(self.temp_dir) as scan:
			entry = next(scan)

		for walk in (iter_tree_entries, iter_tree_files):
			for mode in ('ignore', 'record', 'raise'):
				with self.subTest(walk=walk.__name__, mode=mode):
					error = OSError(errno.EIO, 'directory read failed', str(self.temp_dir))
					errors = []

					def read_entries():
						yield entry
						raise error

					def on_error(exc):
						errors.append(exc)
						if mode == 'raise':
							raise exc

					scan = MagicMock()
					scan.__iter__.return_value = read_entries()
					with patch('pathspec.util.os.scandir', return_value=scan):
						results = walk(self.temp_dir, on_error=None if mode == 'ignore' else on_error)
						first = next(results)
						self.assertEqual(first.path if walk is iter_tree_entries else first, 'readable.txt')
						if mode == 'raise':
							with self.assertRaises(OSError) as caught:
								list(results)
							self.assertIs(caught.exception, error)
						else:
							self.assertEqual(list(results), [])
					self.assertEqual(errors, [] if mode == 'ignore' else [error])
					scan.__exit__.assert_called_once()

	def test_04_scan_iteration_error_keeps_siblings(self):
		"""
		A read failure in a child scan leaves healthy sibling directories walkable.
		"""
		self.make_dirs(['blocked', 'healthy'])
		self.make_files(['healthy/kept.txt'])
		scandir = os.scandir
		error = OSError(errno.EIO, 'directory read failed', 'blocked')

		def read_entries():
			raise error
			yield  # Make this a generator that raises when advanced.

		for walk in (iter_tree_entries, iter_tree_files):
			with self.subTest(walk=walk.__name__):
				blocked = MagicMock()
				blocked.__iter__.return_value = read_entries()

				def scan(path):
					return blocked if os.path.basename(path) == 'blocked' else scandir(path)

				errors = []
				with patch('pathspec.util.os.scandir', side_effect=scan):
					results = list(walk(self.temp_dir, on_error=errors.append))
				paths = get_paths_from_entries(results) if walk is iter_tree_entries else set(results)
				self.assertIn(ospath('healthy/kept.txt'), paths)
				self.assertEqual(errors, [error])
				blocked.__exit__.assert_called_once()

	def test_05_entry_inspection_error(self):
		"""
		Route errors inspecting an entry through the configured error handler.
		"""
		for operation in ('is_dir', 'is_file', 'is_symlink'):
			for handling in ('ignore', 'collect', 'raise'):
				with self.subTest(operation=operation, handling=handling):
					error = PermissionError(errno.EACCES, 'Permission denied', 'blocked')
					blocked = MagicMock(name='blocked entry')
					blocked.name = 'blocked'
					blocked.is_dir.return_value = False
					blocked.is_file.return_value = False
					getattr(blocked, operation).side_effect = error
					file = MagicMock(name='readable entry')
					file.name = 'readable.txt'
					file.is_dir.return_value = False
					file.is_file.return_value = True
					scan = MagicMock()
					scan.__iter__.return_value = iter([blocked, file])
					errors = []

					def on_error(exc):
						if handling == 'raise':
							raise exc
						errors.append(exc)

					with patch('pathspec.util.os.scandir', return_value=scan):
						entries = iter_tree_entries(
							root=self.temp_dir,
							follow_links=False,
							on_error=None if handling == 'ignore' else on_error,
						)

						if handling == 'raise':
							with self.assertRaises(PermissionError) as caught:
								list(get_paths_from_entries(entries))
							self.assertIs(caught.exception, error)
						else:
							self.assertEqual(list(get_paths_from_entries(entries)), [
								'readable.txt',
							])
							self.assertEqual(errors, [error] if handling == 'collect' else [])

	def test_05_file_inspection_error(self):
		"""
		Route errors inspecting an entry through the configured error handler.
		"""
		for operation in ('is_dir', 'is_file', 'is_symlink'):
			for handling in ('ignore', 'collect', 'raise'):
				with self.subTest(operation=operation, handling=handling):
					error = PermissionError(errno.EACCES, 'Permission denied', 'blocked')
					blocked = MagicMock(name='blocked entry')
					blocked.name = 'blocked'
					blocked.is_dir.return_value = False
					blocked.is_file.return_value = False
					getattr(blocked, operation).side_effect = error
					file = MagicMock(name='readable entry')
					file.name = 'readable.txt'
					file.is_dir.return_value = False
					file.is_file.return_value = True
					scan = MagicMock()
					scan.__iter__.return_value = iter([blocked, file])
					errors = []

					def on_error(exc):
						if handling == 'raise':
							raise exc
						errors.append(exc)

					with patch('pathspec.util.os.scandir', return_value=scan):
						files = iter_tree_files(
							root=self.temp_dir,
							follow_links=False,
							on_error=None if handling == 'ignore' else on_error,
						)

						if handling == 'raise':
							with self.assertRaises(PermissionError) as caught:
								list(files)
							self.assertIs(caught.exception, error)
						else:
							self.assertEqual(list(files), ['readable.txt'])
							self.assertEqual(errors, [error] if handling == 'collect' else [])


class MatchFileTest(TestCase):
	"""
	The :class:`MatchFileTest` class tests the :meth:`.match_file`
	function.
	"""

	def test_01_single_1_include(self):
		"""
		Test checking a single file that is included.
		"""
		patterns = list(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "include.txt")

		self.assertIs(include, True)

	def test_01_single_2_exclude(self):
		"""
		Test checking a single file that is excluded.
		"""
		patterns = list(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "test/exclude.txt")

		self.assertIs(include, False)

	def test_01_single_3_unmatch(self):
		"""
		Test checking a single file that is ignored.
		"""
		patterns = list(map(GitIgnoreBasicPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "unmatch.bin")

		self.assertIs(include, False)

	def test_02_many(self):
		"""
		Test matching files individually.
		"""
		patterns = list(map(GitIgnoreBasicPattern, [
			'*.txt',
			'!b.txt',
		]))
		files = {
			'X/a.txt',
			'X/b.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/b.txt',
			'Y/Z/c.txt',
		}

		includes = set(filter(partial(match_file, patterns), files))

		self.assertEqual(includes, {
			'X/a.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/Z/c.txt',
		})


class ModuleAttrDeprecationTest(TestCase):
	"""
	Test that module-level deprecated attributes do not have a broken
	implementation.
	"""

	def test_01_unknown_attribute(self):
		"""
		Test unknown attributes still raise :exc:`AttributeError`.
		"""
		with self.assertRaises(AttributeError):
			pathspec.util.NoSuchThing

		with self.assertRaises(AttributeError):
			pathspec.NoSuchThing


class NormalizeFileTest(TestCase):
	"""
	The :class:`NormalizeFileTest` class tests the :meth:`.normalize_file`
	function.
	"""

	def test_01_purepath(self):
		"""
		Tests normalizing a :class:`PurePath` as argument.
		"""
		first_spec = normalize_file(PurePath('a.txt'))
		second_spec = normalize_file('a.txt')
		self.assertEqual(first_spec, second_spec)


class RecursionErrorDeprecationTest(TestCase):
	"""
	Test the :class:`pathspec.util.RecursionError` deprecations.
	"""

	def test_01_package_attribute(self):
		"""
		Test accessing `pathspec.RecursionError` warns and returns the new class.
		"""
		with self.assertWarns(DeprecationWarning) as context:
			cls = pathspec.RecursionError

		self.assertIs(cls, RecursivePathError)
		self.assertEqual(context.filename, __file__)

	def test_02_util_attribute(self):
		"""
		Test accessing `pathspec.util.RecursionError` warns and returns the new
		class.
		"""
		with self.assertWarns(DeprecationWarning) as context:
			cls = pathspec.util.RecursionError

		self.assertIs(cls, RecursivePathError)
		self.assertEqual(context.filename, __file__)

	def test_03_from_import(self):
		"""
		Test `from pathspec import RecursionError` warns and returns the new class.
		"""
		with self.assertWarns(DeprecationWarning):
			from pathspec import RecursionError as cls

		self.assertIs(cls, RecursivePathError)

	def test_04_star_import(self):
		"""
		Test `from pathspec import *` does not warn, and does not shadow the
		built-in :exc:`RecursionError`.
		"""
		namespace = {}
		exec("from pathspec import *", namespace)

		self.assertNotIn('RecursionError', namespace)
		self.assertNotIn('RecursionError', pathspec.__all__)
