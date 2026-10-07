"""
Tests trailing recursive wildcards restricted to descendant directories.
"""

import re
from itertools import product
from unittest import TestCase

from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .test_06_gitignore import GitIgnoreSpecMixin


class GlobstarDirectoryPatternTest(TestCase):
	"""
	Tests literal, anchored and wildcard prefixes in both pattern implementations.
	"""

	def test_descendant_directories(self):
		"""
		A trailing **/ requires a descendant directory, not the parent or a direct file.
		"""
		cases = [
			('folder/**/', ['folder/sub/', 'folder/sub/file', 'folder/sub/deep/file'],
			 ['folder/', 'folder/file', 'other/folder/sub/file']),
			('/folder/**/**/', ['folder/sub/', 'folder/sub/file'],
			 ['folder/', 'folder/file', 'other/folder/sub/file']),
			('**/folder/**/', ['folder/sub/file', 'other/folder/sub/file'],
			 ['folder/', 'folder/file', 'other/folder/', 'other/folder/file']),
			('*/**/', ['folder/sub/', 'folder/sub/file', 'other/sub/deep/file'],
			 ['folder/', 'folder/file', 'other/', 'other/file']),
			('**/*/**/', ['folder/sub/', 'folder/sub/file', 'other/sub/deep/file'],
			 ['folder/', 'folder/file', 'other/', 'other/file']),
			('folder/*/**/', ['folder/sub/deep/', 'folder/sub/deep/file'],
			 ['folder/', 'folder/file', 'folder/sub/', 'folder/sub/file']),
		]
		for pattern_class, (text, matches, misses), binary in product(
			(GitIgnoreBasicPattern, GitIgnoreSpecPattern), cases, (False, True),
		):
			with self.subTest(pattern_class=pattern_class, text=text, binary=binary):
				pattern_text = text.encode() if binary else text
				regex, include = pattern_class.pattern_to_regex(pattern_text)
				self.assertIs(include, True)
				compiled = re.compile(regex)
				for file in matches:
					self.assertIsNotNone(compiled.search(file.encode() if binary else file), file)
				for file in misses:
					self.assertIsNone(compiled.search(file.encode() if binary else file), file)

	def test_explicit_globstar_contents_shortcut(self):
		"""
		The explicit **/*/** pattern is not the automatic directory-only */ shortcut.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			pattern = pattern_class('**/*/**')
			self.assertIsNone(pattern.match_file('folder/'))
			self.assertIsNone(pattern.match_file('file'))
			self.assertIsNotNone(pattern.match_file('folder/file'))
			self.assertIsNotNone(pattern.match_file('folder/sub/file'))

	def test_regular_directory_and_recursive_shortcuts(self):
		"""
		Ordinary directory patterns and root-wide recursive shortcuts keep their meaning.
		"""
		for pattern_class, text in product(
			(GitIgnoreBasicPattern, GitIgnoreSpecPattern), ('folder/', '**/', '**/**/'),
		):
			with self.subTest(pattern_class=pattern_class, text=text):
				pattern = pattern_class(text)
				for file in ('folder/', 'folder/file', 'folder/sub/file'):
					self.assertIsNotNone(pattern.match_file(file), file)

	def test_newline_directory_names(self):
		"""
		Recursive directory matching includes newline characters within names.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			pattern = pattern_class('folder/**/')
			for file in ('folder/line\nbreak/', 'folder/line\nbreak/file'):
				self.assertIsNotNone(pattern.match_file(file), file)
			self.assertIsNone(pattern.match_file('folder/line\nbreak'))


class GlobstarDirectorySpecTest(GitIgnoreSpecMixin, TestCase):
	"""
	Tests all matching backend and expression-order configurations.
	"""

	def test_literal_prefix(self):
		"""
		A parent and its immediate files remain available for traversal.
		"""
		for begin in self.parameterize_from_lines(['folder/**/']):
			with begin() as spec:
				for file in ('folder/', 'folder/file'):
					self.assertFalse(spec.match_file(file), file)
				for file in ('folder/sub/', 'folder/sub/file', 'folder/sub/deep/file'):
					self.assertTrue(spec.match_file(file), file)

	def test_wildcard_prefix(self):
		"""
		Wildcard prefixes still require at least one additional directory.
		"""
		for begin in self.parameterize_from_lines(['*/**/']):
			with begin() as spec:
				for file in ('folder/', 'folder/file', 'other/file'):
					self.assertFalse(spec.match_file(file), file)
				for file in ('folder/sub/file', 'other/sub/deep/file'):
					self.assertTrue(spec.match_file(file), file)
