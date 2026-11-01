"""Regression coverage for redundant interior components in matching paths."""

from unittest import TestCase

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.util import normalize_file

from .util import require_backend


class InteriorPathNormalizationTest(TestCase):

	def test_normalize_components(self):
		cases = {
			'data//private.txt': 'data/private.txt',
			'data/./private.txt': 'data/private.txt',
			'data///././/private.txt': 'data/private.txt',
			'data//child/./private.txt': 'data/child/private.txt',
			'data//./': 'data/',
			'data/././': 'data/',
			'data/private.txt': 'data/private.txt',
			'data/.hidden': 'data/.hidden',
			'data/..hidden/file': 'data/..hidden/file',
			'data/../private.txt': 'data/../private.txt',
			'data/.': 'data/.',
			'data/': 'data/',
			'': '',
		}
		for path, expected in cases.items():
			with self.subTest(path=path):
				self.assertEqual(normalize_file(path, separators=()), expected)

	def test_public_matching_apis_preserve_input_spelling(self):
		paths = [
			'data/private.txt',
			'data//private.txt',
			'data/./private.txt',
			'data///././private.txt',
			'data/keep.txt',
			'data//./keep.txt',
			'data/public.txt',
			'data/./public.txt',
		]
		expected = [(True, 0)] * 4 + [(False, 2)] * 2 + [(None, None)] * 2
		lines = ['/data/private.txt', '/data/keep.txt', '!/data/keep.txt']
		for cls in (PathSpec, GitIgnoreSpec):
			for backend in ('simple', 're2', 'hyperscan'):
				with self.subTest(cls=cls.__name__, backend=backend):
					require_backend(backend)
					if cls is PathSpec:
						spec = cls.from_lines('gitignore', lines, backend=backend)
					else:
						spec = cls.from_lines(lines, backend=backend)
					self.assertEqual(list(spec.match_files(paths)), paths[:4])
					self.assertEqual(list(spec.match_files(paths, negate=True)), paths[4:])
					results = list(spec.check_files(paths))
					self.assertEqual([result.file for result in results], paths)
					self.assertEqual(
						[(result.include, result.index) for result in results], expected)
					for path, (include, index) in zip(paths, expected):
						self.assertEqual(spec.match_file(path), bool(include))
						result = spec.check_file(path)
						self.assertEqual((result.file, result.include, result.index), (path, include, index))

	def test_custom_separator_and_literal_backslash(self):
		path = r'data\\.\private.txt'
		self.assertEqual(normalize_file(path, separators=('\\',)), 'data/private.txt')
		self.assertEqual(normalize_file(path, separators=()), path)
		for cls in (PathSpec, GitIgnoreSpec):
			with self.subTest(cls=cls.__name__):
				if cls is PathSpec:
					spec = cls.from_lines('gitignore', ['/data/private.txt'], backend='simple')
				else:
					spec = cls.from_lines(['/data/private.txt'], backend='simple')
				self.assertTrue(spec.match_file(path, separators=('\\',)))
				self.assertFalse(spec.match_file(path, separators=()))

	def test_directory_markers_and_parent_components(self):
		for cls in (PathSpec, GitIgnoreSpec):
			with self.subTest(cls=cls.__name__):
				if cls is PathSpec:
					spec = cls.from_lines('gitignore', ['/data/'], backend='simple')
				else:
					spec = cls.from_lines(['/data/'], backend='simple')
				self.assertTrue(spec.match_file('data//./'))
				self.assertFalse(spec.match_file('data'))
				self.assertEqual(normalize_file('data//../file.txt'), 'data/../file.txt')
