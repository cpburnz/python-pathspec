"""
This script tests the trailing space trimming behavior for gitignore
patterns which end with a backslash followed by a space.

Git's *trim_trailing_spaces()* function (dir.c) only keeps a trailing
space when it is escaped by a backslash, and a space is only escaped when
it is preceded by an odd number of consecutive backslashes. When the run
of backslashes preceding the trailing space is even, the backslashes
escape each other and the trailing space is unescaped — Git strips it.

E.g., with an escaped backslash ('foo\\\\') followed by a space, Git
treats the space as unescaped trailing whitespace and matches the file
'foo\\' rather than 'foo\\ '.
"""

import unittest

from pathspec import (
	PathSpec)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)

BS = '\\'
"""
Backslash.
"""


class TrailingSpaceAfterEscapedBackslashTest(unittest.TestCase):
	"""
	The :class:`TrailingSpaceAfterEscapedBackslashTest` class tests that a
	trailing space preceded by an escaped backslash is stripped, matching
	Git's behavior.
	"""

	def _assert_matches(self, pattern_class, raw_pattern: str, file: str, expected: bool) -> None:
		pattern = pattern_class(raw_pattern)
		actual = pattern.match_file(file)
		self.assertIs(
			actual is not None,
			expected,
			f"Pattern {raw_pattern!r} matching file {file!r}: expected {expected}, got {actual is not None} (regex: {pattern.regex.pattern if pattern.regex is not None else None})",
		)

	def test_00_even_backslash_run_trailing_space_stripped(self):
		"""
		Tests that a trailing space preceded by an even number of
		backslashes is unescaped and stripped.
		"""
		# 'foo\\ ' (escaped backslash followed by space): Git strips the
		# unescaped trailing space and matches the file 'foo\'.
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			with self.subTest(pattern_class=pattern_class.__name__):
				self._assert_matches(pattern_class, f'foo{BS * 2} ', f'foo{BS}', True)
				self._assert_matches(pattern_class, f'foo{BS * 2} ', f'foo{BS} ', False)

	def test_01_four_backslashes_trailing_space_stripped(self):
		"""
		Tests that a trailing space preceded by four backslashes (two
		escaped backslashes) is unescaped and stripped.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			with self.subTest(pattern_class=pattern_class.__name__):
				self._assert_matches(pattern_class, f'foo{BS * 4} ', f'foo{BS * 2}', True)
				self._assert_matches(pattern_class, f'foo{BS * 4} ', f'foo{BS * 2} ', False)

	def test_02_odd_backslash_run_trailing_space_kept(self):
		"""
		Tests that a trailing space preceded by an odd number of
		backslashes is escaped and kept.
		"""
		# 'foo\ ' has an escaped space and matches the file 'foo '.
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			with self.subTest(pattern_class=pattern_class.__name__):
				self._assert_matches(pattern_class, f'foo{BS} ', f'foo ', True)
				self._assert_matches(pattern_class, f'foo{BS} ', f'foo', False)

	def test_03_three_backslashes_trailing_space_kept(self):
		"""
		Tests that a trailing space preceded by three backslashes (an
		escaped backslash followed by an escaped space) is kept.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			with self.subTest(pattern_class=pattern_class.__name__):
				self._assert_matches(pattern_class, f'foo{BS * 3} ', f'foo{BS} ', True)
				self._assert_matches(pattern_class, f'foo{BS * 3} ', f'foo{BS}', False)

	def test_04_regex_normalization(self):
		"""
		Tests the compiled regular expressions directly.
		"""
		# With an even run, the trailing space must be stripped before
		# compiling: 'foo\\ ' compiles like 'foo\\'.
		pattern = GitIgnoreBasicPattern(f'foo{BS * 2} ')
		self.assertEqual(pattern.regex.pattern, GitIgnoreBasicPattern(f'foo{BS * 2}').regex.pattern)

	def test_05_pathspec_end_to_end(self):
		"""
		Tests the behavior through the PathSpec interface.
		"""
		spec = PathSpec.from_lines('gitignore', [f'foo{BS * 2} '])
		# These POSIX-style paths contain literal backslashes. Keep Windows
		# from normalizing those characters into directory separators.
		self.assertIs(spec.match_file(f'foo{BS}', separators=('/',)), True)
		self.assertIs(spec.match_file(f'foo{BS} ', separators=('/',)), False)

		spec = PathSpec.from_lines('gitignore', [f'foo{BS} '])
		self.assertIs(spec.match_file('foo '), True)
		self.assertIs(spec.match_file('foo'), False)
