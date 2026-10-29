"""Test gitignore patterns containing escaped path separators."""

from unittest import TestCase

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore import GitIgnorePatternError
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend


CASES = [
	(r'a\/b', ['a/b', 'a/b/child'], ['a', 'ab', 'x/a/b']),
	(r'/a\/b', ['a/b', 'a/b/child'], ['ab', 'x/a/b']),
	(r'a\/b\/c', ['a/b/c', 'a/b/c/child'], ['a/b', 'x/a/b/c']),
	(r'a\/b/', ['a/b/', 'a/b/child'], ['a/b', 'x/a/b/child']),
	(r'a\/b*.py', ['a/b.py', 'a/beta.py'], ['a/b.txt', 'x/a/b.py']),
	(r'a\/[bc].py', ['a/b.py', 'a/c.py'], ['a/d.py', 'x/a/b.py']),
	(r'a\/*/b', ['a/x/b'], ['a/b', 'a/x/y/b']),
	(r'a\/**/b', ['a/b', 'a/x/b', 'a/x/y/b'], ['x/a/b', 'a/c']),
	# An escaped slash after a globstar is required, unlike the slash in "**/".
	(r'**\/b', ['a/b', 'a/x/b', 'a/b/child'], ['b', 'a/c']),
	(r'***\/b', ['a/b', 'a/x/b'], ['b', 'a/c']),
	(r'a/**\/b', ['a/x/b', 'a/x/y/b'], ['a/b', 'x/a/x/b']),
]
"""Patterns with matching and non-matching paths, verified against Git."""


class EscapedSlashTest(TestCase):

	def test_pattern_matching(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, included, excluded in CASES:
				for as_bytes in (False, True):
					with self.subTest(factory=factory, line=line, as_bytes=as_bytes):
						pattern = factory(line.encode() if as_bytes else line)
						for path in included + excluded:
							with self.subTest(path=path):
								self.assertEqual(
									bool(pattern.match_file(path.encode() if as_bytes else path)),
									path in included,
								)

	def test_spec_matching(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line, included, excluded in CASES:
					for spec in (
						GitIgnoreSpec.from_lines([line], backend=backend),
						PathSpec.from_lines('gitignore', [line], backend=backend),
					):
						with self.subTest(line=line, spec=type(spec)):
							self.assertEqual(set(spec.match_files(included + excluded)), set(included))

	def test_negated_rule(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for spec in (
					GitIgnoreSpec.from_lines(['a/*.txt', r'!a\/keep.txt'], backend=backend),
					PathSpec.from_lines('gitignore', ['a/*.txt', r'!a\/keep.txt'], backend=backend),
				):
					with self.subTest(spec=type(spec)):
						self.assertTrue(spec.match_file('a/drop.txt'))
						result = spec.check_file('a/keep.txt')
						self.assertIs(result.include, False)
						self.assertEqual(result.index, 1)

	def test_backslash_parity(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for count in (1, 2, 3, 4):
				for as_bytes in (False, True):
					line = 'a' + '\\' * count + '/b'
					path = 'a' + '\\' * (count // 2) + '/b'
					other = 'a' + '\\' * (count // 2 + 1) + '/b'
					with self.subTest(factory=factory, count=count, as_bytes=as_bytes):
						pattern = factory(line.encode() if as_bytes else line)
						self.assertIsNotNone(pattern.match_file(path.encode() if as_bytes else path))
						self.assertIsNone(pattern.match_file(other.encode() if as_bytes else other))

	def test_leading_and_terminal_slashes(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line in (r'a\/', r'a/**\/', r'a\/b\/'):
				with self.subTest(factory=factory, line=line):
					for errors in (None, 'literal', 'null'):
						self.assertIsNone(factory(line, errors=errors).regex)
					with self.assertRaises(GitIgnorePatternError):
						factory(line, errors='raise')
			# An escaped leading slash is literal, rather than a root anchor.
			pattern = factory(r'\/b')
			self.assertIsNone(pattern.match_file('b'))
			self.assertIsNone(pattern.match_file('a/b'))
