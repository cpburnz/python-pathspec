"""
Tests application-defined auditing of normalized gitignore patterns.
"""

import re
from itertools import product
from unittest import TestCase
from unittest.mock import patch

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend


class PatternAuditTest(TestCase):
	"""
	Tests that pattern factories can enforce application-specific limits.
	"""

	def test_normalized_segments(self):
		"""
		Audit decoded segments after anchoring, directory and wildcard normalization.
		"""
		cases = [
			('file', ('**', 'file')),
			('/file', ('file',)),
			('!foo/**/**/bar/', ('foo', '**', 'bar', '**')),
			('foo/\u00e9.txt', ('foo', '\u00e9.txt')),
			('**/**', ('**',)),
			('**/', ('**',)),
			('*', ('**', '*')),
			('*/', ('**', '*', '**')),
			('foo/bar  \n', ('foo', 'bar')),
		]
		for pattern_class, (pattern, expected), binary in product(
			(GitIgnoreBasicPattern, GitIgnoreSpecPattern), cases, (False, True),
		):
			with self.subTest(pattern_class=pattern_class, pattern=pattern, binary=binary):
				seen = []

				class AuditedPattern(pattern_class):
					@classmethod
					def _audit_segments(cls, segments):
						seen.append(segments)

				text = pattern.encode('latin1') if binary else pattern
				actual = AuditedPattern(text)
				original = pattern_class(text)
				self.assertEqual(seen, [expected])
				self.assertIsInstance(seen[0], tuple)
				self.assertEqual(actual.include, original.include)
				self.assertEqual(actual.regex, original.regex)

	def test_null_and_precompiled_patterns(self):
		"""
		Comments, empty patterns and precompiled expressions have no segments to audit.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			seen = []

			class AuditedPattern(pattern_class):
				@classmethod
				def _audit_segments(cls, segments):
					seen.append(segments)

			for text in ('', '!', '# comment', b'', b'!', b'# comment', None):
				with self.subTest(pattern_class=pattern_class, pattern=text):
					self.assertIsNone(AuditedPattern(text).include)
					self.assertEqual(seen, [])

			compiled = re.compile('foo')
			self.assertIs(AuditedPattern(compiled, True).regex, compiled)
			self.assertEqual(seen, [])

	def test_audit_exception_propagates(self):
		"""
		Audit rejection is not swallowed or replaced by notation error handling.
		"""
		for pattern_class, errors in product(
			(GitIgnoreBasicPattern, GitIgnoreSpecPattern),
			(None, 'literal', 'null', 'raise'),
		):
			with self.subTest(pattern_class=pattern_class, errors=errors):
				rejection = ValueError('Application pattern limit exceeded.')

				class AuditedPattern(pattern_class):
					@classmethod
					def _audit_segments(cls, segments):
						raise rejection

				with patch('pathspec.pattern.re.compile') as compile_regex:
					with self.assertRaises(ValueError) as caught:
						AuditedPattern('a/**/b/**/c', errors=errors)
					self.assertIs(caught.exception, rejection)
					compile_regex.assert_not_called()

	def test_factories_and_backends(self):
		"""
		Both spec types honor an audited factory before selecting a matching backend.
		"""
		for spec_class, pattern_class in (
			(PathSpec, GitIgnoreBasicPattern),
			(GitIgnoreSpec, GitIgnoreSpecPattern),
		):
			class AuditedPattern(pattern_class):
				@classmethod
				def _audit_segments(cls, segments):
					if segments.count('**') > 1:
						raise ValueError('Too many recursive wildcards.')

			for backend in ('simple', 're2', 'hyperscan', 'best'):
				with self.subTest(spec_class=spec_class, backend=backend):
					require_backend(backend)
					with self.assertRaisesRegex(ValueError, 'Too many recursive wildcards'):
						spec_class.from_lines(
							AuditedPattern, ['a/**/b/**/c'], backend=backend,
						)
					spec = spec_class.from_lines(
						AuditedPattern, ['foo/**/**/bar', '!foo/private/bar'], backend=backend,
					)
					self.assertTrue(spec.match_file('foo/other/bar'))
					self.assertFalse(spec.match_file('foo/private/bar'))

	def test_independent_policies(self):
		"""
		A subclass policy does not change standard patterns or another subclass.
		"""
		class RejectingPattern(GitIgnoreSpecPattern):
			@classmethod
			def _audit_segments(cls, segments):
				raise ValueError('Rejected by this application.')

		class PermissivePattern(GitIgnoreSpecPattern):
			@classmethod
			def _audit_segments(cls, segments):
				pass

		with self.assertRaises(ValueError):
			RejectingPattern('foo/**/bar')
		self.assertIsNotNone(PermissivePattern('foo/**/bar').match_file('foo/bar'))
		self.assertIsNotNone(GitIgnoreSpecPattern('foo/**/bar').match_file('foo/bar'))

	def test_default_has_no_limits(self):
		"""
		Applications opt in; the standard factories impose no arbitrary limits.
		"""
		for pattern_class in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			pattern = pattern_class('a/' + '**/b/' * 10 + 'c')
			self.assertIsNotNone(pattern.regex)
