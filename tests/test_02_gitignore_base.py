"""
This script tests :class:`._GitIgnoreBasePattern`, and well as shared behavior
of :class:`.GitIgnoreBasicPattern` and :class:`.GitIgnoreSpecPattern`.
"""

import re
from itertools import (
	product)
from unittest import (
	TestCase)

from pathspec import (
	GitIgnoreSpec,
	PathSpec)
from pathspec.patterns.gitignore.base import (
	_BYTES_ENCODING,
	_GitIgnoreBasePattern,
	_strip_trailing_ws)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)

from .util import (
	require_backend)

BRACKET_LITERAL_CASES: list[tuple[str, list[str], list[str]]] = [
	('[[]draft].md', ['[draft].md'], ['draft.md', 'adraft].md']),
	('[a&&b].pdf', ['a.pdf', '&.pdf', 'b.pdf'], ['c.pdf', 'ab.pdf']),
	('[a||b].pdf', ['a.pdf', '|.pdf', 'b.pdf'], ['c.pdf', 'ab.pdf']),
	('[a~~b].pdf', ['a.pdf', '~.pdf', 'b.pdf'], ['c.pdf', 'ab.pdf']),
	('[![]draft].md', ['adraft].md'], ['[draft].md', 'draft.md']),
	('[!a&&b].pdf', ['c.pdf'], ['a.pdf', '&.pdf', 'b.pdf']),
	('[^a||b].pdf', ['c.pdf'], ['a.pdf', '|.pdf', 'b.pdf']),
	('[!a~~b].pdf', ['c.pdf'], ['a.pdf', '~.pdf', 'b.pdf']),
	('[[:digit:]&&a-c].pdf', ['0.pdf', '&.pdf', 'b.pdf'], ['d.pdf', 'x.pdf']),
	(r'[\[\&\|\~].pdf', ['[.pdf', '&.pdf', '|.pdf', '~.pdf'], ['a.pdf']),
	('[--0].pdf', ['-.pdf', '..pdf', '0.pdf'], ['1.pdf', '/.pdf']),
	('[a-c--].pdf', ['a.pdf', 'c.pdf', '-.pdf'], ['d.pdf', '+.pdf']),
	('[!a-c--].pdf', ['d.pdf', '+.pdf'], ['a.pdf', 'c.pdf', '-.pdf']),
	('[[:digit:]--].pdf', ['0.pdf', '-.pdf'], ['a.pdf', '+.pdf']),
	('[a-c--e].pdf', ['a.pdf', '-.pdf', '..pdf', 'e.pdf'], ['f.pdf', '+.pdf']),
]
"""
Bracket literal test cases.
"""

BS = '\\'
"""
Backslash character.
"""

STAR_RUN_CASES: list[tuple[str, list[str], list[str]]] = [
	('***/x', ['x', 'a/x', 'a/b/x'], ['xx', 'a/xx']),
	('****/x', ['x', 'a/x', 'a/b/x'], ['xx',]),
	('a/***', ['a/b', 'a/b/c'], ['a', 'b/a', 'b/a/c']),
	('a/***/b', ['a/b', 'a/x/b', 'a/x/y/b'], ['a/x', 'b/x/b']),
	('***', ['a', 'a/b', 'a/b/c'], []),
	# A run of asterisks inside a segment is a single asterisk, which does not
	# match a slash.
	('a**b', ['ab', 'axb', 'axxb'], ['a/b', 'a/x/b']),
	('a***b', ['ab', 'axb', 'axxb'], ['a/b', 'a/x/b']),
	('a***', ['a', 'ab', 'abc', 'q/a'], ['b', 'ba', 'xab']),
	('***b', ['b', 'ab', 'x/xb'], ['a', 'ba', 'abc']),
	('a***b***c', ['abc', 'abxc', 'axbxc'], ['ab', 'axc', 'a/b/c']),
	('***a***', ['a', 'ab', 'ba', 'xab'], ['b', 'x', 'b/x/b']),
	('x/***b', ['x/b', 'x/ab', 'x/xb'], ['b', 'q/x/b', 'x/y']),
	('***b/c', ['ab/c', 'xb/c'], ['q/xb/c', 'b/a/c']),
	# An escaped asterisk is literal and is not part of a run.
	(r'a\***b', ['a*b', 'a*xb'], ['ab', 'axb']),
	(r'a***\*b', ['a*b'], ['ab', 'axb']),
	(r'\***', ['*', '*x'], ['x', 'x*']),
	# A question mark between asterisks still requires one character.
	('a*?*b', ['axb', 'axxb', 'abb'], ['ab', 'a/b']),
]
"""
Each case is (pattern, paths that Git matches, paths that Git does not match).
Git's wildmatch treats a run of asterisks that spans a whole path segment as a
single globstar (``**``).
"""


class GitIgnoreBasePatternTest(TestCase):
	"""
	Tests the :class:`_GitIgnoreBasePattern` implementation.
	"""

	def test_01_escape_bytes(self):
		"""
		Test escaping binary strings.
		"""
		byte_to_escaped = {__b: b'\\' + __b for __b in (
			__c.encode(_BYTES_ENCODING) for __c in '\\[]!*#? '
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
		char_to_escaped = {__c: f"\\{__c}" for __c in '\\[]!*#? '}
		for char_ord in range(128):
			char = chr(char_ord)
			escape_val = _GitIgnoreBasePattern.escape(char)
			expect_val = char_to_escaped.get(char, char)
			self.assertEqual(escape_val, expect_val)

	def test_02_strip_trailing_ws_1_even_bs(self):
		"""
		Tests that trailing whitespace preceded by an even number of backslashes is
		unescaped and stripped.
		"""
		for n, wc in product(
			[0, 2, 4],
			[' ', '\n', '\r'],
		):
			with self.subTest(n=n, wc=wc):
				bs = BS*n
				ws = wc*n
				val = _strip_trailing_ws(f' foo{bs}{ws}')
				self.assertEqual(val, f' foo{bs}')

	def test_02_strip_trailing_ws_2_odd_bs(self):
		"""
		Tests that trailing whitespace preceded by an odd number of backslashes is
		escaped and stripped.
		"""
		for n, wc in product(
			[0, 1, 3],
			[' ', '\n', '\r'],
		):
			with self.subTest(n=n, wc=wc):
				bs = BS*n
				ws = wc*n
				val = _strip_trailing_ws(f' foo{bs}{ws}')
				self.assertEqual(val, f' foo{bs}{ws[:1]}')

	def test_02_strip_trailing_ws_3_literal_whitespace(self):
		"""
		Only spaces and line endings are stripped, not filename characters.
		"""
		for wc, ending in product(
			['\t', '\v', '\f', '\x85', '\xa0', '\u2003'],
			['', ' ', '\n', '\r\n'],
		):
			with self.subTest(wc=wc, ending=ending):
				self.assertEqual(_strip_trailing_ws(f'foo{wc}{ending}'), f'foo{wc}')


class BracketLiteralTest(TestCase):
	"""
	Test literal regex set operators in gitignore bracket expressions.
	"""

	def test_pattern_literals(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, matches, misses in BRACKET_LITERAL_CASES:
				for as_bytes in (False, True):
					for errors in (None, 'literal', 'null', 'raise'):
						with self.subTest(factory=factory, line=line, as_bytes=as_bytes, errors=errors):
							re.purge()
							pattern = factory(line.encode() if as_bytes else line, errors=errors)

							for paths, expected in ((matches, True), (misses, False)):
								for path in paths:
									self.assertEqual(
										bool(pattern.match_file(path.encode() if as_bytes else path)),
										expected, path,
									)

	def test_spec_literals(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line, matches, misses in BRACKET_LITERAL_CASES:
					for style in ('gitignore', None):
						with self.subTest(line=line, style=style):
							re.purge()
							if style is None:
								spec = GitIgnoreSpec.from_lines([line], backend=backend)
							else:
								spec = PathSpec.from_lines(style, [line], backend=backend)

							for prefix in ('', 'docs/'):
								for paths, expected in ((matches, True), (misses, False)):
									for path in paths:
										self.assertEqual(spec.match_file(prefix + path), expected, path)


class StarRunTest(TestCase):
	"""
	Tests asterisk runs against Git's behavior.
	"""

	def test_pattern_classes(self):
		"""
		Tests that both gitignore pattern classes treat a segment of asterisks
		like a double-asterisk.
		"""
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, matches, misses in STAR_RUN_CASES:
				with self.subTest(factory=factory.__name__, line=line):
					pattern = factory(line)
					for path in matches:
						self.assertTrue(pattern.match_file(path), path)
					for path in misses:
						self.assertFalse(pattern.match_file(path), path)

	def test_gitignore_spec(self):
		"""
		Tests that :class:`.GitIgnoreSpec` matches the same paths as Git.
		"""
		for line, matches, misses in STAR_RUN_CASES:
			with self.subTest(line=line):
				spec = GitIgnoreSpec.from_lines([line])
				for path in matches:
					self.assertTrue(spec.match_file(path), path)
				for path in misses:
					self.assertFalse(spec.match_file(path), path)
