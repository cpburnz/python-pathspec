"""
This script tests :class:`.GitIgnoreSpec`.
"""

import unittest

from pathspec.gitignore import (
	GitIgnoreSpec)


class GitIgnoreSpecTest(unittest.TestCase):
	"""
	The :class:`GitIgnoreSpecTest` class tests the :class:`.GitIgnoreSpec`
	class.
	"""

	def test_01_dir_exclusions(self) -> None:
		"""
		Test directory exclusions.
		"""
		spec = GitIgnoreSpec.from_lines([
			'*.txt',
			'!test1/',
		])
		results = set(spec.match_files([
			'test1/a.txt',
			'test1/b.bin',
			'test1/c/c.txt',
			'test2/a.txt',
			'test2/b.bin',
			'test2/c/c.txt',
		]))
		self.assertEqual(results, {
			'test1/a.txt',
			'test1/c/c.txt',
			'test2/a.txt',
			'test2/c/c.txt',
		})

	def test_01_file_exclusions(self):
		"""
		Test file exclusions.
		"""
		spec = GitIgnoreSpec.from_lines([
			'*.txt',
			'!b.txt',
		])
		results = set(spec.match_files([
			'X/a.txt',
			'X/b.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/b.txt',
			'Y/Z/c.txt',
		]))
		self.assertEqual(results, {
			'X/a.txt',
			'X/Z/c.txt',
			'Y/a.txt',
			'Y/Z/c.txt',
		})

	def test_02_issue_41(self) -> None:
		"""
		Test including a file and excluding a directory with the same name
		pattern.
		"""
		spec = GitIgnoreSpec.from_lines([
			'*.yaml',
			'!*.yaml/',
		])
		files = {
			'dir.yaml/file.sql',
			'dir.yaml/file.yaml',
			'dir.yaml/index.txt',
			'dir/file.sql',
			'dir/file.yaml',
			'dir/index.txt',
			'file.yaml',
		}
		ignores = set(spec.match_files(files))
		self.assertEqual(ignores, {
			'dir.yaml/file.yaml',
			'dir/file.yaml',
			'file.yaml',
		})
		self.assertEqual(files - ignores, {
			'dir.yaml/file.sql',
			'dir.yaml/index.txt',
			'dir/file.sql',
			'dir/index.txt',
		})
