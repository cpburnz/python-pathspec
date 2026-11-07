"""Test carriage returns retained after Git removes a line ending and spaces."""

from unittest import TestCase

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore.base import _strip_trailing_ws
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend


# Expected filenames verified with git check-ignore --no-index.
CASES = [
	('probe\r \n', 'probe\r'),
	('probe\r\r\n', 'probe\r'),
	('probe\r \r\n', 'probe\r'),
	('probe \r \n', 'probe \r'),
	('probe\r\r \n', 'probe\r\r'),
]


class CarriageReturnTest(TestCase):

	def test_line_ending_before_spaces(self):
		for line, expected in CASES + [
			('probe\n', 'probe'),
			('probe\r\n', 'probe'),
			('probe\r', 'probe'),
			('probe \r\n', 'probe'),
			('probe\\\r\n', 'probe\\'),
			('probe\\\n', 'probe\\'),
			('probe\\ \r\n', 'probe\\ '),
		]:
			with self.subTest(line=line):
				self.assertEqual(_strip_trailing_ws(line), expected)

	def test_pattern_matching(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, filename in CASES:
				for as_bytes in (False, True):
					for errors in (None, 'literal', 'null', 'raise'):
						with self.subTest(factory=factory, line=line, as_bytes=as_bytes, errors=errors):
							if as_bytes:
								pattern = factory(line.encode(), errors=errors)
								self.assertIsNotNone(pattern.match_file(filename.encode()))
								self.assertIsNone(pattern.match_file(b'probe'))
							else:
								pattern = factory(line, errors=errors)
								self.assertIsNotNone(pattern.match_file(filename))
								self.assertIsNone(pattern.match_file('probe'))

	def test_spec_matching(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line, filename in CASES:
					for spec in (
						GitIgnoreSpec.from_lines([line], backend=backend),
						PathSpec.from_lines('gitignore', [line], backend=backend),
					):
						with self.subTest(line=line, spec=type(spec)):
							self.assertEqual(list(spec.match_files(['probe', filename])), [filename])

	def test_negation(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				spec = GitIgnoreSpec.from_lines(['*', '!probe\r \n'], backend=backend)
				self.assertTrue(spec.match_file('probe'))
				result = spec.check_file('probe\r')
				self.assertIs(result.include, False)
				self.assertEqual(result.index, 1)
