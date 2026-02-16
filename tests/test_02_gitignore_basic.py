"""
This script tests :class:`.GitIgnoreBasicPattern`.
"""

import re
import unittest

from pathspec.patterns.gitignore.base import (
	GitIgnorePatternError,
	_BYTES_ENCODING)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.util import (
	lookup_pattern)

_DIR_OPT = '(?:/|$)'
"""
Optional directory ending.
"""


class GitIgnoreBasicPatternTest(unittest.TestCase):
	"""
	The :class:`GitIgnoreBasicPatternTest` class tests the :class:`GitIgnoreBasicPattern`
	implementation.
	"""

	def _check_invalid_pattern(self, git_ignore_pattern: str) -> None:
		expected_message_pattern = re.escape(git_ignore_pattern)
		with self.assertRaisesRegex(GitIgnorePatternError, expected_message_pattern):
			GitIgnoreBasicPattern(git_ignore_pattern)

	def test_00_empty(self):
		"""
		Tests an empty pattern.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('')
		self.assertIsNone(include)
		self.assertIsNone(regex)

	def test_01_absolute(self):
		"""
		Tests an absolute path pattern.

		This should match:

			an/absolute/file/path
			an/absolute/file/path/foo

		This should NOT match:

			foo/an/absolute/file/path
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('/an/absolute/file/path')
		self.assertTrue(include)
		self.assertEqual(regex, f'^an/absolute/file/path{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'an/absolute/file/path',
			'an/absolute/file/path/foo',
			'foo/an/absolute/file/path',
		]))
		self.assertEqual(results, {
			'an/absolute/file/path',
			'an/absolute/file/path/foo',
		})

	def test_01_absolute_ignore(self):
		"""
		Tests an ignore absolute path pattern.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('!/foo/build')
		self.assertIs(include, False)
		self.assertEqual(regex, f'^foo/build{_DIR_OPT}')

		# NOTE: The pattern match is backwards because the pattern itself
		# does not consider the include attribute.
		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'build/file.py',
			'foo/build/file.py',
		]))
		self.assertEqual(results, {
			'foo/build/file.py',
		})

	def test_01_absolute_root_1(self):
		"""
		Tests a single root absolute path pattern.

		This should match any file, unlike git check-ignore.
		"""
		# NOTICE: The results from GitIgnoreBasicPattern will differ from
		# GitIgnoreSpecPattern.
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('/')
		self.assertTrue(include)
		self.assertEqual(regex, '.')

	def test_01_absolute_root_2_double_asterisk(self):
		"""
		Tests the root path patterns:

			/**
			/**/**
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('/**')
		self.assertTrue(include)
		self.assertIsNotNone(regex)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('/**/**')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('/')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

	def test_01_relative(self):
		"""
		Tests a relative path pattern.

		This should match:

			spam
			spam/
			foo/spam
			spam/foo
			foo/spam/bar
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('spam')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?spam{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'spam',
			'spam/',
			'foo/spam',
			'spam/foo',
			'foo/spam/bar',
		]))
		self.assertEqual(results, {
			'spam',
			'spam/',
			'foo/spam',
			'spam/foo',
			'foo/spam/bar',
		})

	def test_01_relative_nested(self):
		"""
		Tests a relative nested path pattern.

		This should match:

			foo/spam
			foo/spam/bar

		This should **not** match (according to git check-ignore (v2.4.1)):

			bar/foo/spam
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('foo/spam')
		self.assertTrue(include)
		self.assertEqual(regex, f'^foo/spam{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'foo/spam',
			'foo/spam/bar',
			'bar/foo/spam',
		]))
		self.assertEqual(results, {
			'foo/spam',
			'foo/spam/bar',
		})

	def test_02_comment(self):
		"""
		Tests a comment pattern.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('# Cork soakers.')
		self.assertIsNone(include)
		self.assertIsNone(regex)

	def test_02_ignore(self):
		"""
		Tests an exclude pattern.

		This should NOT match (according to git check-ignore (v2.4.1)):

			temp/foo
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('!temp')
		self.assertIs(include, False)
		self.assertEqual(regex, f'^(?:.+/)?temp{_DIR_OPT}')

		# NOTE: The pattern match is backwards because the pattern itself
		# does not consider the include attribute.
		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'temp/foo',
		]))
		self.assertEqual(results, {
			'temp/foo',
		})

	def test_03_child_double_asterisk(self):
		"""
		Tests a directory name with a double-asterisk child
		directory.

		This should match:

			spam/bar

		This should **not** match (according to git check-ignore (v2.4.1)):

			foo/spam/bar
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('spam/**')
		self.assertTrue(include)
		self.assertEqual(regex, '^spam/')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'spam/bar',
			'foo/spam/bar',
		]))
		self.assertEqual(results, {'spam/bar'})

	def test_03_inner_double_asterisk(self):
		"""
		Tests a path with an inner double-asterisk directory.

		This should match:

			left/right
			left/bar/right
			left/foo/bar/right
			left/bar/right/foo

		This should **not** match (according to git check-ignore (v2.4.1)):

			foo/left/bar/right
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('left/**/right')
		self.assertTrue(include)
		self.assertEqual(regex, f'^left(?:/.+)?/right{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'left/right',
			'left/bar/right',
			'left/foo/bar/right',
			'left/bar/right/foo',
			'foo/left/bar/right',
		]))
		self.assertEqual(results, {
			'left/right',
			'left/bar/right',
			'left/foo/bar/right',
			'left/bar/right/foo',
		})

	def test_03_only_double_asterisk(self):
		"""
		Tests a double-asterisk pattern which matches everything.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**')
		self.assertTrue(include)
		self.assertEqual(regex, '.')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'x',
			'y.py',
			'A/x',
			'A/y.py',
			'A/B/x',
			'A/B/y.py',
			'A/B/C/x',
			'A/B/C/y.py',
		]))

		self.assertEqual(results, {
			'x',
			'y.py',
			'A/x',
			'A/y.py',
			'A/B/x',
			'A/B/y.py',
			'A/B/C/x',
			'A/B/C/y.py',
		})

	def test_03_parent_double_asterisk(self):
		"""
		Tests a file name with a double-asterisk parent directory.

		This should match:

			spam
			foo/spam
			foo/spam/bar
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/spam')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?spam{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'spam',
			'foo/spam',
			'foo/spam/bar',
		]))
		self.assertEqual(results, {
			'spam',
			'foo/spam',
			'foo/spam/bar',
		})

	def test_03_duplicate_leading_double_asterisk_edge_case(self):
		"""
		Regression test for duplicate leading **/ bug.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**')
		self.assertTrue(include)
		self.assertEqual(regex, '.')

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**/**')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/api')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?api{_DIR_OPT}')

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**/api')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/api/')
		self.assertTrue(include)
		self.assertEqual(regex, '^(?:.+/)?api/')

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**/api/')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/api/**')
		self.assertTrue(include)
		self.assertEqual(regex, '^(?:.+/)?api/')

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**/api/**/**')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

	def test_03_double_asterisk_trailing_slash_edge_case(self):
		"""
		Tests the edge-case **/ pattern.

		This should match everything except individual files in the root directory.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/')
		self.assertTrue(include)
		self.assertEqual(regex, '/')

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/**/')
		self.assertTrue(include)
		self.assertEqual(equiv_regex, regex)

	def test_04_infix_wildcard(self):
		"""
		Tests a pattern with an infix wildcard.

		This should match:

			foo--bar
			foo-hello-bar
			a/foo-hello-bar
			foo-hello-bar/b
			a/foo-hello-bar/b
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('foo-*-bar')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?foo\\-[^/]*\\-bar{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'foo--bar',
			'foo-hello-bar',
			'a/foo-hello-bar',
			'foo-hello-bar/b',
			'a/foo-hello-bar/b',
		]))
		self.assertEqual(results, {
			'foo--bar',
			'foo-hello-bar',
			'a/foo-hello-bar',
			'foo-hello-bar/b',
			'a/foo-hello-bar/b',
		})

	def test_04_postfix_wildcard(self):
		"""
		Tests a pattern with a postfix wildcard.

		This should match:

			~temp-
			~temp-foo
			~temp-foo/bar
			foo/~temp-bar
			foo/~temp-bar/baz
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('~temp-*')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?\\~temp\\-[^/]*{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'~temp-',
			'~temp-foo',
			'~temp-foo/bar',
			'foo/~temp-bar',
			'foo/~temp-bar/baz',
		]))
		self.assertEqual(results, {
			'~temp-',
			'~temp-foo',
			'~temp-foo/bar',
			'foo/~temp-bar',
			'foo/~temp-bar/baz',
		})

	def test_04_prefix_wildcard(self):
		"""
		Tests a pattern with a prefix wildcard.

		This should match:

			bar.py
			bar.py/
			foo/bar.py
			foo/bar.py/baz
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('*.py')
		self.assertTrue(include)
		self.assertEqual(regex, f'^(?:.+/)?[^/]*\\.py{_DIR_OPT}')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'bar.py',
			'bar.py/',
			'foo/bar.py',
			'foo/bar.py/baz',
		]))
		self.assertEqual(results, {
			'bar.py',
			'bar.py/',
			'foo/bar.py',
			'foo/bar.py/baz',
		})

	def test_05_directory(self):
		"""
		Tests a directory pattern.

		This should match:

			dir/
			foo/dir/
			foo/dir/bar

		This should **not** match:

			dir
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('dir/')
		self.assertTrue(include)
		self.assertEqual(regex, '^(?:.+/)?dir/')

		pattern = GitIgnoreBasicPattern(re.compile(regex), include)
		results = set(filter(pattern.match_file, [
			'dir/',
			'foo/dir/',
			'foo/dir/bar',
			'dir',
		]))
		self.assertEqual(results, {
			'dir/',
			'foo/dir/',
			'foo/dir/bar',
		})

	def test_06_registered(self):
		"""
		Tests that the pattern is registered.
		"""
		self.assertIs(lookup_pattern('gitignore'), GitIgnoreBasicPattern)

	def test_07_encode_bytes(self):
		"""
		Test encoding bytes.
		"""
		encoded = "".join(map(chr, range(0, 256))).encode(_BYTES_ENCODING)
		expected = (
			b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10'
			b'\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
			b' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\'
			b']^_`abcdefghijklmnopqrstuvwxyz{|}~'
			b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d'
			b'\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c'
			b'\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab'
			b'\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba'
			b'\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9'
			b'\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8'
			b'\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7'
			b'\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6'
			b'\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'
		)
		self.assertEqual(encoded, expected)

	def test_07_decode_bytes(self):
		"""
		Test decoding bytes.
		"""
		decoded = bytes(bytearray(range(0, 256))).decode(_BYTES_ENCODING)
		expected = (
			'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10'
			'\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
			' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\'
			']^_`abcdefghijklmnopqrstuvwxyz{|}~'
			'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d'
			'\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c'
			'\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab'
			'\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba'
			'\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9'
			'\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8'
			'\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7'
			'\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6'
			'\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'
		)
		self.assertEqual(decoded, expected)

	def test_07_match_bytes_and_bytes(self):
		"""
		Test byte string patterns matching byte string paths.
		"""
		pattern = GitIgnoreBasicPattern(b'*.py')
		results = set(filter(pattern.match_file, [b'a.py']))
		self.assertEqual(results, {b'a.py'})

	def test_07_match_bytes_and_bytes_complete(self):
		"""
		Test byte string patterns matching byte string paths.
		"""
		encoded = bytes(bytearray(range(0, 256)))

		# Forward slashes cannot be escaped with the current implementation.
		# Remove ASCII 47.
		fs_ord = ord('/')
		encoded = encoded[:fs_ord] + encoded[fs_ord+1:]

		escaped = b''.join(b'\\' + encoded[i:i+1] for i in range(len(encoded)))

		pattern = GitIgnoreBasicPattern(escaped)
		results = set(filter(pattern.match_file, [encoded]))
		self.assertEqual(results, {encoded})

	def test_07_match_bytes_and_unicode_fail(self):
		"""
		Test byte string patterns matching byte string paths.
		"""
		pattern = GitIgnoreBasicPattern(b'*.py')
		with self.assertRaises(TypeError):
			pattern.match_file('a.py')

	def test_07_match_unicode_and_bytes_fail(self):
		"""
		Test unicode patterns with byte paths.
		"""
		pattern = GitIgnoreBasicPattern('*.py')
		with self.assertRaises(TypeError):
			pattern.match_file(b'a.py')

	def test_07_match_unicode_and_unicode(self):
		"""
		Test unicode patterns with unicode paths.
		"""
		pattern = GitIgnoreBasicPattern('*.py')
		results = set(filter(pattern.match_file, ['a.py']))
		self.assertEqual(results, {'a.py'})

	def test_08_escape(self):
		"""
		Test escaping a string with meta-characters
		"""
		fname = 'file!with*weird#naming_[1].t?t'
		escaped = r'file\!with\*weird\#naming_\[1\].t\?t'
		result = GitIgnoreBasicPattern.escape(fname)
		self.assertEqual(result, escaped)

	def test_09_single_escape_fail(self):
		"""
		Test an escape on a line by itself.
		"""
		self._check_invalid_pattern('\\')

	def test_09_single_exclamation_mark_fail(self):
		"""
		Test an escape on a line by itself.
		"""
		self._check_invalid_pattern('!')

	def test_10_escape_asterisk_end(self):
		"""
		Test escaping an asterisk at the end of a line.
		"""
		pattern = GitIgnoreBasicPattern('asteris\\*')
		results = set(filter(pattern.match_file, [
			'asteris*',
			'asterisk',
		]))
		self.assertEqual(results, {'asteris*'})

	def test_10_escape_asterisk_mid(self):
		"""
		Test escaping an asterisk in the middle of a line.
		"""
		pattern = GitIgnoreBasicPattern('as\\*erisk')
		results = set(filter(pattern.match_file, [
			'as*erisk',
			'asterisk',
		]))
		self.assertEqual(results, {'as*erisk'})

	def test_10_escape_asterisk_start(self):
		"""
		Test escaping an asterisk at the start of a line.
		"""
		pattern = GitIgnoreBasicPattern('\\*sterisk')
		results = set(filter(pattern.match_file, [
			'*sterisk',
			'asterisk',
		]))
		self.assertEqual(results, {'*sterisk'})

	def test_10_escape_exclamation_mark_start(self):
		"""
		Test escaping an exclamation mark at the start of a line.
		"""
		pattern = GitIgnoreBasicPattern('\\!mark')
		results = set(filter(pattern.match_file, [
			'!mark',
		]))
		self.assertEqual(results, {'!mark'})

	def test_10_escape_pound_start(self):
		"""
		Test escaping a pound sign at the start of a line.
		"""
		pattern = GitIgnoreBasicPattern('\\#sign')
		results = set(filter(pattern.match_file, [
			'#sign',
		]))
		self.assertEqual(results, {'#sign'})

	def test_11_issue_19_directory_a(self):
		"""
		Test a directory discrepancy, scenario A.
		"""
		# NOTICE: The results from GitIgnoreBasicPattern will differ from
		# GitIgnoreSpecPattern.
		pattern = GitIgnoreBasicPattern('dirG/')
		results = set(filter(pattern.match_file, [
			'fileA',
			'fileB',
			'dirD/fileE',
			'dirD/fileF',
			'dirG/dirH/fileI',
			'dirG/dirH/fileJ',
			'dirG/fileO',
		]))
		self.assertEqual(results, {
			'dirG/dirH/fileI',
			'dirG/dirH/fileJ',
			'dirG/fileO',
		})

	def test_11_issue_19_directory_b(self):
		"""
		Test a directory discrepancy, scenario B.
		"""
		# NOTICE: The results from GitIgnoreBasicPattern will differ from
		# GitIgnoreSpecPattern.
		pattern = GitIgnoreBasicPattern('dirG/*')
		results = set(filter(pattern.match_file, [
			'fileA',
			'fileB',
			'dirD/fileE',
			'dirD/fileF',
			'dirG/dirH/fileI',
			'dirG/dirH/fileJ',
			'dirG/fileO',
		]))
		self.assertEqual(results, {
			'dirG/fileO',
		})

	def test_11_issue_19_directory_c(self):
		"""
		Test a directory discrepancy, scenario C.
		"""
		# NOTICE: The results from GitIgnoreBasicPattern will differ from
		# GitIgnoreSpecPattern.
		pattern = GitIgnoreBasicPattern('dirG/**')
		results = set(filter(pattern.match_file, [
			'fileA',
			'fileB',
			'dirD/fileE',
			'dirD/fileF',
			'dirG/dirH/fileI',
			'dirG/dirH/fileJ',
			'dirG/fileO',
		]))
		self.assertEqual(results, {
			'dirG/dirH/fileI',
			'dirG/dirH/fileJ',
			'dirG/fileO',
		})

	def test_12_asterisk_1_regex(self):
		"""
		Test a relative asterisk path pattern's regular expression.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('*')
		self.assertTrue(include)
		self.assertEqual(regex, '.')

	def test_12_asterisk_2_regex_equivalent(self):
		"""
		Test a path pattern equivalent to the relative asterisk using double
		asterisk.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('*')
		self.assertTrue(include)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('**/*')
		self.assertTrue(include)

		self.assertEqual(regex, equiv_regex)

	def test_12_asterisk_3_child(self):
		"""
		Test a relative asterisk path pattern matching a direct child path.
		"""
		pattern = GitIgnoreBasicPattern('*')
		self.assertTrue(pattern.match_file('file.txt'))

	def test_12_asterisk_4_descendant(self):
		"""
		Test a relative asterisk path pattern matching a descendant path.
		"""
		pattern = GitIgnoreBasicPattern('*')
		self.assertTrue(pattern.match_file('anydir/file.txt'))

	def test_12_issue_62(self):
		"""
		Test including all files, scenario A.
		"""
		pattern = GitIgnoreBasicPattern('*')
		results = set(filter(pattern.match_file, [
			'file.txt',
			'anydir/file.txt',
		]))
		self.assertEqual(results, {
			'file.txt',
			'anydir/file.txt',
		})

	def test_13_issue_77_1_negate_with_caret(self):
		"""
		Test negation using the caret symbol ("^").
		"""
		pattern = GitIgnoreBasicPattern('a[^gy]c')
		results = set(filter(pattern.match_file, [
			'agc',
			'ayc',
			'abc',
			'adc',
		]))
		self.assertEqual(results, {
			'abc',
			'adc',
		})

	def test_13_issue_77_1_negate_with_exclamation_mark(self):
		"""
		Test negation using the exclamation mark ("!").
		"""
		pattern = GitIgnoreBasicPattern('a[!gy]c')
		results = set(filter(pattern.match_file, [
			'agc',
			'ayc',
			'abc',
			'adc',
		]))
		self.assertEqual(results, {
			'abc',
			'adc',
		})

	def test_13_issue_77_2_regex(self):
		"""
		Test the resulting regex for regex bracket expression negation.
		"""
		regex, include = GitIgnoreBasicPattern.pattern_to_regex('a[^b]c')
		self.assertTrue(include)

		equiv_regex, include = GitIgnoreBasicPattern.pattern_to_regex('a[!b]c')
		self.assertTrue(include)

		self.assertEqual(regex, equiv_regex)

	def test_14_issue_81_a(self):
		"""
		Test ignoring files in a directory, scenario A.
		"""
		pattern = GitIgnoreBasicPattern('!libfoo/**')

		self.assertEqual(pattern.regex.pattern, '^libfoo/')
		self.assertIs(pattern.include, False)
		self.assertTrue(pattern.match_file('libfoo/__init__.py'))

	def test_14_issue_81_b(self):
		"""
		Test ignoring files in a directory, scenario B.
		"""
		pattern = GitIgnoreBasicPattern('!libfoo/*')

		self.assertEqual(pattern.regex.pattern, f'^libfoo/[^/]+/?$')
		self.assertIs(pattern.include, False)
		self.assertTrue(pattern.match_file('libfoo/__init__.py'))

	def test_14_issue_81_c(self):
		"""
		Test ignoring files in a directory, scenario C.
		"""
		# NOTICE: GitIgnoreBasicPattern will match the file, but
		# GitIgnoreSpecPattern should not.
		pattern = GitIgnoreBasicPattern('!libfoo/')

		self.assertEqual(pattern.regex.pattern, '^(?:.+/)?libfoo/')
		self.assertIs(pattern.include, False)
		self.assertTrue(pattern.match_file('libfoo/__init__.py'))

	def test_15_issue_93_a_1(self):
		"""
		Test patterns with trailing double asterisks in a segment.
		"""
		pattern = GitIgnoreBasicPattern('foo**')
		self.assertIs(pattern.include, True)
		self.assertEqual(pattern.regex.pattern, f'^(?:.+/)?foo[^/]*[^/]*{_DIR_OPT}')
		self.assertTrue(pattern.match_file('foosrodah'))

	def test_15_issue_93_a_2(self):
		"""
		Test patterns with trailing double asterisks in a segment.
		"""
		pattern = GitIgnoreBasicPattern('foo**/bar')
		self.assertIs(pattern.include, True)
		self.assertEqual(pattern.regex.pattern, f'^foo[^/]*[^/]*/bar{_DIR_OPT}')
		self.assertFalse(pattern.match_file('foobar'))
		self.assertTrue(pattern.match_file('foosrodah/bar'))

	def test_15_issue_93_b_1_single(self):
		"""
		Test patterns with leading spaces.
		"""
		pattern = GitIgnoreBasicPattern(' foo')
		self.assertIs(pattern.include, True)
		self.assertEqual(pattern.regex.pattern, f'^(?:.+/)?\\ foo{_DIR_OPT}')
		self.assertFalse(pattern.match_file('foo'))
		self.assertTrue(pattern.match_file(' foo'))

	def test_15_issue_93_b_2_double(self):
		"""
		Test patterns with leading spaces.
		"""
		pattern = GitIgnoreBasicPattern('  foo')
		self.assertIs(pattern.include, True)
		self.assertEqual(pattern.regex.pattern, f'^(?:.+/)?\\ \\ foo{_DIR_OPT}')
		self.assertFalse(pattern.match_file('foo'))
		self.assertFalse(pattern.match_file(' foo'))
		self.assertTrue(pattern.match_file('  foo'))

	def test_15_issue_93_c_1(self):
		"""
		Test patterns with invalid range notation.
		"""
		pattern = GitIgnoreBasicPattern('[')
		self.assertIsNone(pattern.include)
		self.assertIsNone(pattern.regex)
		self.assertFalse(pattern.match_file('['))

	def test_15_issue_93_c_2(self):
		"""
		Test patterns with invalid range notation.
		"""
		pattern = GitIgnoreBasicPattern('[!]')
		self.assertIsNone(pattern.include)
		self.assertIsNone(pattern.regex)
		self.assertFalse(pattern.match_file('[!]'))
