# encoding: utf-8
"""
This script tests ``PathSpec``.
"""

import unittest

import pathspec

class PathSpecTest(unittest.TestCase):
	"""
	The ``PathSpecTest`` class tests the ``PathSpec`` class.
	"""

	def test_01_windows_paths(self):
		"""
		Tests that Windows paths will be properly normalized and matched.
		"""
		spec = pathspec.PathSpec.from_lines('gitignore', [
			'*.txt',
			'!test1/',
		])
		results = set(spec.match_files([
			'src\\test1\\a.txt',
			'src\\test1\\b.txt',
			'src\\test1\\c\\c.txt',
			'src\\test2\\a.txt',
			'src\\test2\\b.txt',
			'src\\test2\\c\\c.txt',
		], separators=('\\',)))
		self.assertEquals(results, {
			'src\\test2\\a.txt',
			'src\\test2\\b.txt',
			'src\\test2\\c\\c.txt',
		})
