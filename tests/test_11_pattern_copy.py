"""Test shallow copying of regular expression patterns and their subclasses."""

import re
from copy import copy
from unittest import TestCase

from pathspec import RegexPattern
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern


class SingleArgumentPattern(RegexPattern):
	def __init__(self, pattern):
		super().__init__(pattern)


class StatefulPattern(RegexPattern):
	def __init__(self, pattern, include=None):
		super().__init__(pattern, include)
		self.metadata = []


class SlottedPattern(RegexPattern):
	__slots__ = ('metadata', '__private', 'unset')

	def __init__(self, pattern, include=None):
		super().__init__(pattern, include)
		self.metadata = []
		self.__private = []


class PatternCopyTest(TestCase):

	def assert_pattern_copy(self, pattern):
		other = copy(pattern)
		self.assertIsNot(other, pattern)
		self.assertIs(type(other), type(pattern))
		self.assertIs(other.pattern, pattern.pattern)
		self.assertIs(other.regex, pattern.regex)
		self.assertIs(other.include, pattern.include)
		self.assertEqual(
			bool(other.match_file('abc.txt')), bool(pattern.match_file('abc.txt')),
		)
		return other

	def test_builtin_patterns(self):
		for factory in (RegexPattern, GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for text in ('abc.txt', None):
				with self.subTest(factory=factory, text=text):
					self.assert_pattern_copy(factory(text))

	def test_compiled_pattern_and_include(self):
		for include in (True, False, None):
			with self.subTest(include=include):
				pattern = RegexPattern(re.compile('abc.txt', re.IGNORECASE), include)
				other = self.assert_pattern_copy(pattern)
				self.assertIsNotNone(other.match_file('ABC.TXT'))

	def test_subclass_without_include_parameter(self):
		self.assert_pattern_copy(SingleArgumentPattern('abc.txt'))

	def test_subclass_dictionary_state(self):
		pattern = StatefulPattern('abc.txt')
		pattern.metadata.append('retained')
		other = self.assert_pattern_copy(pattern)
		self.assertIs(other.metadata, pattern.metadata)
		self.assertIsNot(other.__dict__, pattern.__dict__)

	def test_subclass_slot_state(self):
		pattern = SlottedPattern('abc.txt')
		pattern.metadata.append('retained')
		other = self.assert_pattern_copy(pattern)
		self.assertIs(other.metadata, pattern.metadata)
		self.assertIs(
			getattr(other, '_SlottedPattern__private'),
			getattr(pattern, '_SlottedPattern__private'),
		)
		self.assertFalse(hasattr(other, 'unset'))
