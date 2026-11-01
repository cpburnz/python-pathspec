"""Test slashes inside gitignore bracket expressions against Git's semantics."""

from unittest import TestCase

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend


CASES = [
	('[a/b].txt', ['a.txt', 'b.txt'], ['c.txt', 'dir/a.txt', 'a/b.txt']),
	('[a/b].txt/', ['a.txt/', 'a.txt/file'], ['a.txt', 'dir/a.txt/file']),
	('dir/[a/b].txt', ['dir/a.txt', 'dir/b.txt'], ['a.txt', 'deep/dir/a.txt']),
	('/[a/b].txt', ['a.txt', 'b.txt'], ['dir/a.txt', 'a/b.txt']),
	('x[/0]y', ['x0y'], ['x/y', 'dir/x0y']),
	('x[.-/]y', ['x.y'], ['x/y', 'x0y']),
	('x[/-0]y', ['x0y'], ['x/y', 'x.y']),
	('x[!/]y', ['xay', 'x0y'], ['x/y', 'dir/xay']),
	('x[^/]y', ['xay', 'x0y'], ['x/y', 'dir/xay']),
	('x[/]y', [], ['x/y', 'xay']),
	('x[/^a]y', ['x^y', 'xay'], ['xby', 'x/y', 'dir/xay']),
	(r'\[a/b].txt', ['[a/b].txt'], ['a.txt', 'b.txt']),
	(r'\\[a/b].txt', [r'\a.txt', r'\b.txt'], ['a.txt', r'dir/\a.txt']),
	(r'[a\/].txt', ['a.txt'], ['dir/a.txt', 'a/.txt']),
	('[[:alpha:]/].txt', ['a.txt', 'b.txt'], ['0.txt', 'dir/a.txt']),
	('[]a/].txt', ['].txt', 'a.txt'], ['b.txt', 'dir/a.txt']),
]


class BracketSeparatorTest(TestCase):

	def test_patterns(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, included, excluded in CASES:
				for as_bytes in (False, True):
					with self.subTest(factory=factory, line=line, as_bytes=as_bytes):
						pattern = factory(line.encode() if as_bytes else line)
						for path in included + excluded:
							self.assertEqual(
								bool(pattern.match_file(path.encode() if as_bytes else path)),
								path in included,
								path,
							)

	def test_backends(self):
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
				spec = GitIgnoreSpec.from_lines(['*.txt', '![a/b].txt'], backend=backend)
				self.assertFalse(spec.match_file('a.txt'))
				self.assertFalse(spec.match_file('b.txt'))
				self.assertTrue(spec.match_file('c.txt'))
				self.assertTrue(spec.match_file('dir/a.txt'))

	def test_noop_all_error_modes(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line in ('[/]', 'x[/-/]y', '![/]', 'dir[/]/'):
				for errors in ('literal', 'null', 'raise'):
					for text in (line, line.encode()):
						with self.subTest(factory=factory, line=text, errors=errors):
							pattern = factory(text, errors=errors)
							self.assertIsNone(pattern.include)
							self.assertIsNone(pattern.regex)
