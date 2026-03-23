"""
This script tests :class:`._GitIgnoreBasePattern`.
"""

import unittest

from pathspec.patterns.gitignore.base import (
	_BYTES_ENCODING,
	_GitIgnoreBasePattern)


class GitIgnoreBasePatternTest(unittest.TestCase):
	"""
	The :class:`GitIgnoreBasePatternTest` class tests the :class:`_GitIgnoreBasePattern`
	implementation.
	"""

	def test_01_escape_bytes(self):
		"""
		Test escaping binary strings.
		"""
		byte_to_escaped = {__b: b'\\' + __b for __b in (
			__c.encode(_BYTES_ENCODING) for __c in '\\[]!*#?'
		)}
		for char_ord in range(256):
			char_byte = chr(char_ord).encode(_BYTES_ENCODING)
			escape_val = _GitIgnoreBasePattern.escape(char_byte)
			expect_val = byte_to_escaped.get(char_byte, char_byte)
			self.assertEqual(escape_val, expect_val)

	def test_01_escape_str(self):
		"""
		Test escaping unicode strings.
		"""
		char_to_escaped = {__c: f"\\{__c}" for __c in '\\[]!*#?'}
		for char_ord in range(128):
			char = chr(char_ord)
			escape_val = _GitIgnoreBasePattern.escape(char)
			expect_val = char_to_escaped.get(char, char)
			self.assertEqual(escape_val, expect_val)
