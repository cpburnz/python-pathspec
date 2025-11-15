"""
This script tests utility functions.
"""

import errno
import os
import os.path
import shutil
import tempfile
import unittest
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

from pathspec.patterns.gitwildmatch import (
	GitWildMatchPattern)
from pathspec.util import (
	RecursionError,
	check_match_file,
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


class CheckMatchFileTest(unittest.TestCase):
	"""
	The :class:`CheckMatchFileTest` class tests the :meth:`.check_match_file`
	function.
	"""

	def test_01_single_1_include(self):
		"""
		Test checking a single file that is included.
		"""
		patterns = list(enumerate(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "include.txt")

		self.assertEqual(include_index, (True, 0))

	def test_01_single_2_exclude(self):
		"""
		Test checking a single file that is excluded.
		"""
		patterns = list(enumerate(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "test/exclude.txt")

		self.assertEqual(include_index, (False, 1))

	def test_01_single_3_unmatch(self):
		"""
		Test checking a single file that is ignored.
		"""
		patterns = list(enumerate(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		])))

		include_index = check_match_file(patterns, "unmatch.bin")

		self.assertEqual(include_index, (None, None))

	def test_02_many(self):
		"""
		Test matching files individually.
		"""
		patterns = list(enumerate(map(GitWildMatchPattern, [
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


class IterTreeTest(unittest.TestCase):
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
		with self.assertRaises(RecursionError) as context:
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
		with self.assertRaises(RecursionError) as context:
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
		with self.assertRaises(RecursionError) as context:
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
		with self.assertRaises(RecursionError) as context:
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


class MatchFileTest(unittest.TestCase):
	"""
	The :class:`MatchFileTest` class tests the :meth:`.match_file`
	function.
	"""

	def test_01_single_1_include(self):
		"""
		Test checking a single file that is included.
		"""
		patterns = list(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "include.txt")

		self.assertIs(include, True)

	def test_01_single_2_exclude(self):
		"""
		Test checking a single file that is excluded.
		"""
		patterns = list(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "test/exclude.txt")

		self.assertIs(include, False)

	def test_01_single_3_unmatch(self):
		"""
		Test checking a single file that is ignored.
		"""
		patterns = list(map(GitWildMatchPattern, [
			"*.txt",
			"!test/",
		]))

		include = match_file(patterns, "unmatch.bin")

		self.assertIs(include, False)

	def test_02_many(self):
		"""
		Test matching files individually.
		"""
		patterns = list(map(GitWildMatchPattern, [
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


class NormalizeFileTest(unittest.TestCase):
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
