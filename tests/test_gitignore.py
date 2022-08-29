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

	def test_01_issue_41(self) -> None:
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
