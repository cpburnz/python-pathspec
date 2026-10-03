"""Test that a terminal newline remains part of a filename."""

import unittest

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend


class EndAnchorTest(unittest.TestCase):

	def test_pattern_filename_end(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for source, filename in (
				('foo', 'foo'),
				('foo', 'x/foo'),
				('foo', 'x\ny/foo'),
				('/foo', 'foo'),
				('**/foo', 'x/foo'),
				('foo?', 'foo1'),
				('foo[0-9]', 'foo1'),
				(r'foo\\Z', r'foo\Z'),
			):
				for as_bytes in (False, True):
					with self.subTest(factory=factory, source=source, as_bytes=as_bytes):
						pattern = factory(source.encode() if as_bytes else source)
						path = filename.encode() if as_bytes else filename
						newline = b'\n' if as_bytes else '\n'
						self.assertIsNotNone(pattern.match_file(path))
						self.assertIsNone(pattern.match_file(path + newline))

	def test_backend_filename_end(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
					for as_bytes in (False, True):
						if as_bytes and backend == 'simple':
							continue  # The simple backend requires string patterns for string paths.
						with self.subTest(factory=factory, as_bytes=as_bytes):
							line = b'foo' if as_bytes else 'foo'
							spec = PathSpec.from_lines(factory, [line], backend=backend)
							self.assertTrue(spec.match_file('foo'))
							self.assertFalse(spec.match_file('foo\n'))
							spec = GitIgnoreSpec.from_lines([line], backend=backend)
							self.assertTrue(spec.match_file('foo'))
							self.assertFalse(spec.match_file('foo\n'))

	def test_negation_keeps_newline_filename(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				spec = GitIgnoreSpec.from_lines(['*', '!foo'], backend=backend)
				self.assertFalse(spec.match_file('foo'))
				self.assertTrue(spec.match_file('foo\n'))

	def test_backend_literal_backslash(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
					with self.subTest(factory=factory):
						spec = PathSpec.from_lines(factory, [r'foo\\Z'], backend=backend)
						self.assertTrue(spec.match_file(r'foo\Z', separators=('/',)))
						self.assertFalse(spec.match_file(r'foo\z', separators=('/',)))
