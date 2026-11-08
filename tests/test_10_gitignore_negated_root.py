"""A root-only pattern remains a no-op after its negation prefix is removed."""

from unittest import TestCase

from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .test_06_gitignore import GitIgnoreSpecMixin


class NegatedRootTest(GitIgnoreSpecMixin, TestCase):

	def test_root_pattern_is_noop(self):
		for pattern in ('/', '!/', '!/ ', '!/\r\n'):
			for value in (pattern, pattern.encode('ascii')):
				for errors in (None, 'null', 'literal', 'raise'):
					with self.subTest(pattern=value, errors=errors):
						self.assertEqual(
							GitIgnoreSpecPattern.pattern_to_regex(value, errors=errors),
							(None, None),
						)

	def test_negated_root_does_not_reinclude_ancestor(self):
		# Git check-ignore and git add --dry-run both keep the child ignored:
		# '!/' does not reopen 'a/', so the final negation cannot reach it.
		for root_pattern in ('!/', '!/ ', '!/\r\n', '/', '!//', '', '# comment'):
			lines = ['*', root_pattern, '!a/keep.txt']
			for sub_test in self.parameterize_from_lines(lines):
				with sub_test() as spec:
					for path in ('a/', 'a/keep.txt', 'a/b/keep.txt'):
						result = spec.check_file(path)
						self.assertEqual((result.include, result.index), (True, 0))

	def test_actual_directory_negation_still_reincludes(self):
		for sub_test in self.parameterize_from_lines(['*', '!a/', '!a/keep.txt']):
			with sub_test() as spec:
				self.assertFalse(spec.match_file('a/keep.txt'))

	def test_escaped_exclamation_is_literal(self):
		for sub_test in self.parameterize_from_lines([r'\!/']):
			with sub_test() as spec:
				self.assertTrue(spec.match_file('!/keep.txt'))
				self.assertFalse(spec.match_file('a/keep.txt'))
