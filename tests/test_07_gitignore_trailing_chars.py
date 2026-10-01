"""
Test that trailing filename characters are not treated as trailing spaces.
"""

import io
import unittest

from pathspec import (
	GitIgnoreSpec,
	PathSpec)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)


class GitIgnoreTrailingCharsTest(unittest.TestCase):
	"""
	Test literal trailing whitespace in patterns and filename escaping.
	"""

	def test_01_literal_whitespace(self):
		for cls in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for suffix in ('\t', '\v', '\f', '\x85', '\xa0', '\u2003'):
				name = 'foo' + suffix
				for ending in ('', ' ', '\n', '\r\n'):
					with self.subTest(cls=cls, suffix=suffix, ending=ending):
						pattern = cls(name + ending)
						self.assertTrue(pattern.match_file(name))
						self.assertIsNone(pattern.match_file('foo'))
						escaped = cls(cls.escape(name))
						self.assertTrue(escaped.match_file(name))

	def test_02_bytes(self):
		for cls in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for suffix in (b'\t', b'\v', b'\f', b'\x85', b'\xa0', b'\xc2\xa0', b'\xe2\x80\x83'):
				name = b'foo' + suffix
				for ending in (b'', b' ', b'\n', b'\r\n'):
					with self.subTest(cls=cls, suffix=suffix, ending=ending):
						pattern = cls(name + ending)
						self.assertTrue(pattern.match_file(name))
						self.assertIsNone(pattern.match_file(b'foo'))
						escaped = cls(cls.escape(name))
						self.assertTrue(escaped.match_file(name))

	def test_03_stream_lines(self):
		for suffix in ('\t', '\xa0', '\u2003'):
			name = 'foo' + suffix
			for ending in ('\n', '\r\n'):
				for make_spec in (
					lambda lines: PathSpec.from_lines('gitignore', lines, backend='simple'),
					lambda lines: GitIgnoreSpec.from_lines(lines, backend='simple'),
				):
					with self.subTest(suffix=suffix, ending=ending, make_spec=make_spec):
						spec = make_spec(io.StringIO(name + ending))
						self.assertTrue(spec.match_file(name))
						self.assertFalse(spec.match_file('foo'))

	def test_04_spaces_and_backslashes(self):
		for cls in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for raw, name in (
				('foo  ', 'foo'),
				('foo\\  ', 'foo '),
				('foo\\\\ ', 'foo\\'),
				('foo\\\\\\ ', 'foo\\ '),
				('foo\\\t ', 'foo\t'),
			):
				for ending in ('', '\n', '\r\n'):
					with self.subTest(cls=cls, raw=raw, ending=ending):
						self.assertTrue(cls(raw + ending).match_file(name))

	def test_05_negation_and_directories(self):
		for suffix in ('\t', '\xa0', '\u2003'):
			name = 'foo' + suffix
			with self.subTest(suffix=suffix):
				spec = GitIgnoreSpec.from_lines(['*', '!' + name], backend='simple')
				self.assertFalse(spec.match_file(name))
				self.assertTrue(spec.match_file('foo'))
				spec = GitIgnoreSpec.from_lines([name + '/'], backend='simple')
				self.assertTrue(spec.match_file(name + '/'))
				self.assertTrue(spec.match_file(name + '/child'))
				self.assertFalse(spec.match_file(name))
				self.assertFalse(spec.match_file('foo/child'))

	def test_06_character_after_slash(self):
		for suffix in ('\t', '\xa0', '\u2003'):
			name = 'foo/' + suffix
			for make_spec in (
				lambda lines: PathSpec.from_lines('gitignore', lines, backend='simple'),
				lambda lines: GitIgnoreSpec.from_lines(lines, backend='simple'),
			):
				with self.subTest(suffix=suffix, make_spec=make_spec):
					spec = make_spec([name])
					self.assertTrue(spec.match_file(name))
					self.assertFalse(spec.match_file('foo/'))
					self.assertFalse(spec.match_file('foo/other'))
