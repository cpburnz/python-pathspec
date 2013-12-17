# coding: utf-8
"""
This script tests ``GitIgnorePattern``.
"""

import unittest

from pathspec import GitIgnorePattern

class GitIgnoreTest(unittest.TestCase):
	"""
	The ``GitIgnoreTest`` class tests the ``GitIgnorePattern``
	implementation.
	"""

	def test_00_empty(self):
		"""
		Tests an empty pattern.
		"""
		spec = GitIgnorePattern('')
		self.assertIsNone(spec.include)
		self.assertIsNone(spec.regex)

	def test_01_absolute(self):
		"""
		Tests an absolute path pattern.
		"""
		spec = GitIgnorePattern('/an/absolute/file/path')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^an/absolute/file/path$')

	def test_01_relative(self):
		"""
		Tests a relative path pattern.
		"""
		spec = GitIgnorePattern('spam')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?spam$')

	def test_02_comment(self):
		"""
		Tests a comment pattern.
		"""
		spec = GitIgnorePattern('# Cork soakers.')
		self.assertIsNone(spec.include)
		self.assertIsNone(spec.regex)

	def test_02_ignore(self):
		"""
		Tests an exclude pattern.
		"""
		spec = GitIgnorePattern('!temp')
		self.assertIsNotNone(spec.include)
		self.assertFalse(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?temp$')

	def test_03_child_double_asterisk(self):
		"""
		Tests a directory name with a double-asterisk child
		directory.
		"""
		spec = GitIgnorePattern('spam/**')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?spam/.+$')

	def test_03_inner_double_asterisk(self):
		"""
		Tests a path with an inner double-asterisk directory.
		"""
		spec = GitIgnorePattern('left/**/right')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?left(?:/.+)?/right$')

	def test_03_only_double_asterisk(self):
		"""
		Tests a double-asterisk pattern which matches everything.
		"""
		spec = GitIgnorePattern('**')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^.+$')

	def test_03_parent_double_asterisk(self):
		"""
		Tests a file name with a double-asterisk parent directory.
		"""
		spec = GitIgnorePattern('**/spam')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?spam$')

	def test_04_infix_wildcard(self):
		"""
		Tests a pattern with an infix wildcard.
		"""
		spec = GitIgnorePattern('foo-*-bar')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?foo\\-[^/]*\\-bar$')

	def test_04_postfix_wildcard(self):
		"""
		Tests a pattern with a postfix wildcard.
		"""
		spec = GitIgnorePattern('~temp-*')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?\\~temp\\-[^/]*$')

	def test_04_prefix_wildcard(self):
		"""
		Tests a pattern with a prefix wildcard.
		"""
		spec = GitIgnorePattern('*.py')
		self.assertTrue(spec.include)
		self.assertEquals(spec.regex.pattern, '^(?:.+/)?[^/]*\\.py$')

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(GitIgnoreTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
