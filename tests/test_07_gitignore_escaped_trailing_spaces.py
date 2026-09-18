"""Regression: gitignore trailing-space trimming must match Git dir.c."""

import unittest

from pathspec import PathSpec
from pathspec.patterns.gitignore.base import trim_trailing_spaces
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern


class TrimTrailingSpacesTest(unittest.TestCase):
	def test_extra_spaces_after_escaped_space(self):
		# Git: 'bar\\  ' (backslash, space, space) → keep escaped space only.
		self.assertEqual(trim_trailing_spaces('bar\\  '), 'bar\\ ')
		self.assertEqual(trim_trailing_spaces('bar\\   '), 'bar\\ ')

	def test_even_backslash_run_strips_space(self):
		# Even backslashes: space is unescaped and must be stripped.
		self.assertEqual(trim_trailing_spaces('foo\\\\ '), 'foo\\\\')
		self.assertEqual(trim_trailing_spaces('foo\\\\\\\\ '), 'foo\\\\\\\\')

	def test_odd_backslash_run_keeps_space(self):
		self.assertEqual(trim_trailing_spaces('foo\\ '), 'foo\\ ')
		self.assertEqual(trim_trailing_spaces('foo\\\\\\ '), 'foo\\\\\\ ')

	def test_plain_trailing_spaces(self):
		self.assertEqual(trim_trailing_spaces('foo  '), 'foo')
		self.assertEqual(trim_trailing_spaces('foo'), 'foo')


class PathSpecEscapedTrailingSpaceTest(unittest.TestCase):
	def test_pathspec_matches_file_with_trailing_space(self):
		# Previously raised GitIgnorePatternError (dangling backslash).
		spec = PathSpec.from_lines('gitwildmatch', ['bar\\  '])
		self.assertFalse(spec.match_file('bar'))
		self.assertTrue(spec.match_file('bar '))
		self.assertFalse(spec.match_file('bar  '))

	def test_basic_and_spec_pattern_classes(self):
		for cls in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			pattern = cls('bar\\  ')
			self.assertTrue(pattern.include)
			self.assertIsNotNone(pattern.regex)


if __name__ == '__main__':
	unittest.main()
