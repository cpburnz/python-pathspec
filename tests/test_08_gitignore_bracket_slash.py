"""Test that bracket expressions only match within a path segment."""

import unittest
import warnings

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore import GitIgnorePatternError
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from .util import require_backend


class BracketSlashTest(unittest.TestCase):

	def test_invalid_posix_after_range(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line in ('[z-[:bogus:]]', '[z-[:^alpha:]]', '[.-[:bogus:]]'):
				with self.subTest(factory=factory, line=line):
					pattern = factory(line, errors='literal')
					self.assertIsNotNone(pattern.match_file(line))
					self.assertIsNone(factory(line, errors='null').regex)
					with self.assertRaises(GitIgnorePatternError):
						factory(line, errors='raise')

	def test_pattern_separator(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern, GitWildMatchPattern):
			for bracket, matched in (
				('[!x]', '.0'),
				('[^x]', '.0'),
				('[!]-]', '.0'),
				('[!-x]', '.0'),
				('[.-0]', '.0'),
				(r'[\.-\0]', '.0'),
				('[!0-9]', '.x'),
				('[[:punct:]]', '.!'),
				('[[:graph:]]', '.0'),
				('[[:print:]]', '. '),
				('[[:digit:].]', '.0'),
			):
				for as_bytes in (False, True):
					with self.subTest(factory=factory, bracket=bracket, as_bytes=as_bytes):
						line = 'a' + bracket + 'b'
						with warnings.catch_warnings():
							warnings.simplefilter('ignore', DeprecationWarning)
							pattern = factory(line.encode() if as_bytes else line)
						for char in matched + '/':
							path = 'a' + char + 'b'
							self.assertEqual(
								bool(pattern.match_file(path.encode() if as_bytes else path)),
								char != '/',
								path,
							)

	def test_spec_separator(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line in ('a[!x]b', 'a[.-0]b', 'a[[:punct:]]b'):
					with warnings.catch_warnings():
						warnings.simplefilter('ignore', DeprecationWarning)
						specs = (
							GitIgnoreSpec.from_lines([line], backend=backend),
							PathSpec.from_lines('gitignore', [line], backend=backend),
							PathSpec.from_lines('gitwildmatch', [line], backend=backend),
						)
					for spec in specs:
						for prefix in ('', 'dir/'):
							with self.subTest(line=line, spec=spec, prefix=prefix):
								self.assertTrue(spec.match_file(prefix + 'a.b'))
								self.assertFalse(spec.match_file(prefix + 'a/b'))

	def test_negated_rule(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line in ('a[!x]b', 'a[.-0]b', 'a[[:punct:]]b'):
					with self.subTest(line=line):
						spec = GitIgnoreSpec.from_lines(['*', '!' + line], backend=backend)
						self.assertFalse(spec.match_file('a.b'))
						self.assertTrue(spec.match_file('a/b'))
