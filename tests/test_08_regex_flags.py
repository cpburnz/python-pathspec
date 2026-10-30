"""
This script tests that the native backends preserve the compile flags of an
externally compiled regular expression.
"""

import re
import unittest

from pathspec import (
	GitIgnoreSpec,
	PathSpec,
	RegexPattern)
from pathspec._backends import (
	agg)
from pathspec._backends._utils import (
	get_regex_flags,
	has_unsupported_flags,
	supports_regex_flags,
	translate_regex_flags)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)

from .util import (
	require_backend)

BACKENDS = ('simple', 're2', 'hyperscan')
"""
The backends that can be required individually.
"""

NATIVE_BACKEND_CLASSES = {
	('re2', PathSpec): 'Re2PsBackend',
	('re2', GitIgnoreSpec): 'Re2GiBackend',
	('hyperscan', PathSpec): 'HyperscanPsBackend',
	('hyperscan', GitIgnoreSpec): 'HyperscanGiBackend',
}
"""
The name of the backend class used by each native backend.
"""

# Translate: expression, flags, a path that matches with the flags, and a path
# that must not match.
TRANSLATABLE_CASES = [
	('secret', re.IGNORECASE, 'SECRET', 'public'),
	('secret', re.UNICODE, 'secret', 'SECRET'),
	('^secret$', re.MULTILINE, 'x\nsecret\ny', 'xsecret'),
	('^a.b$', re.DOTALL, 'a\nb', 'aXbY'),
	('^[a-z]+$', re.IGNORECASE, 'SECRET', '123'),
	('^secret.*end$', re.IGNORECASE | re.MULTILINE | re.DOTALL, 'x\nSECRET\nEND\ny', 'xsecret'),
	('^Secret$', re.IGNORECASE | re.MULTILINE | re.DOTALL, 'x\nSECRET\ny', 'xsecret'),
	('secret', 0, 'secret', 'SECRET'),
	('(?i)secret', 0, 'SECRET', 'public'),
	('(?m)^secret$', 0, 'x\nsecret\ny', 'xsecret'),
	('(?s)^a.b$', 0, 'a\nb', 'aXbY'),
]
"""
The cases for the flags that both native engines can express as global inline
flags (`(?ims)`), or that need no translation at all.
"""

UNTRANSLATABLE_CASES = [
	('s e c r e t', re.VERBOSE, 'secret', 's e c r e t'),
	('secret # note', re.VERBOSE, 'secret', 'public'),
	('secret # [', re.VERBOSE, 'secret', 'public'),
	('^[a-z]+$', re.ASCII | re.IGNORECASE, 'SECRET', '\u017f'),
]
"""
The cases for the flags that no native engine can express: RE2 has no `(?x)`,
and neither engine can express `(?a)` or `(?L)`.
"""


class RegexFlagsTest(unittest.TestCase):
	"""
	The compile flags of a pattern must not be silently discarded.
	"""

	def test_translatable_flags(self):
		"""
		A native backend matches like the simple backend.
		"""
		for expression, flags, path, no_path in TRANSLATABLE_CASES:
			for backend in BACKENDS:
				with self.subTest(expression=expression, flags=flags, path=path, backend=backend):
					require_backend(backend)
					for spec_class in (PathSpec, GitIgnoreSpec):
						with self.subTest(spec_class=spec_class):
							spec = spec_class(
								[RegexPattern(re.compile(expression, flags), include=True)],
								backend=backend,
							)
							self.assertTrue(spec.match_file(path))
							self.assertFalse(spec.match_file(no_path))

	def test_translatable_flags_backend_agreement(self):
		"""
		Every backend agrees with the simple backend.
		"""
		for expression, flags, path, no_path in TRANSLATABLE_CASES:
			for spec_class in (PathSpec, GitIgnoreSpec):
				with self.subTest(expression=expression, flags=flags, spec_class=spec_class):
					require_backend('simple')
					expected = []
					for backend in BACKENDS:
						require_backend(backend)
						spec = spec_class(
							[RegexPattern(re.compile(expression, flags), include=True)],
							backend=backend,
						)
						expected.append((spec.match_file(path), spec.match_file(no_path)))

					self.assertEqual(expected, [expected[0]] * len(expected))

	def test_default_backend(self):
		"""
		The default backend keeps the flags of a compiled pattern.
		"""
		for expression, flags, path, no_path in TRANSLATABLE_CASES + UNTRANSLATABLE_CASES:
			for spec_class in (PathSpec, GitIgnoreSpec):
				for backend in (None, 'best'):
					with self.subTest(expression=expression, flags=flags,
					                  spec_class=spec_class, backend=backend):
						spec = spec_class(
							[RegexPattern(re.compile(expression, flags), include=True)],
							backend=backend,
						)
						self.assertTrue(spec.match_file(path))
						self.assertFalse(spec.match_file(no_path))

	def test_untranslatable_flags_fall_back(self):
		"""
		Flags that no native engine can express select the simple backend.
		"""
		for expression, flags, path, no_path in UNTRANSLATABLE_CASES:
			for spec_class in (PathSpec, GitIgnoreSpec):
				for backend in (None, 'best'):
					with self.subTest(expression=expression, flags=flags,
					                  spec_class=spec_class, backend=backend):
						spec = spec_class(
							[RegexPattern(re.compile(expression, flags), include=True)],
							backend=backend,
						)
						self.assertTrue(
							type(spec._backend).__name__.startswith('Simple'),
							spec._backend,
						)
						self.assertTrue(spec.match_file(path))
						self.assertFalse(spec.match_file(no_path))

	def test_untranslatable_flags_explicit_backend(self):
		"""
		Explicitly selecting a native backend reports the unsupported flags.
		"""
		for backend in ('re2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for expression, flags, _, _ in UNTRANSLATABLE_CASES:
					for spec_class in (PathSpec, GitIgnoreSpec):
						with self.subTest(expression=expression, flags=flags,
						                  spec_class=spec_class):
							patterns = [RegexPattern(re.compile(expression, flags), include=True)]
							with self.assertRaisesRegex(ValueError, "backend='simple'"):
								spec_class(patterns, backend=backend)

	def test_ordinary_patterns_stay_native(self):
		"""
		Patterns without external flags are not demoted to the simple backend.
		"""
		lines = ['*.txt', '!keep.txt', 'logs/', '!logs/KEEP']
		for backend in BACKENDS + ('best', None):
			with self.subTest(backend=backend):
				require_backend(backend)
				specs = (
					PathSpec.from_lines(GitIgnoreBasicPattern, lines, backend=backend),
					GitIgnoreSpec.from_lines(lines, backend=backend),
				)
				for spec in specs:
					with self.subTest(spec=type(spec)):
						if backend == 'simple':
							continue
						elif backend is None or backend == 'best':
							if agg._BEST_BACKEND != 'simple':
								self.assertFalse(
									type(spec._backend).__name__.startswith('Simple'),
									spec._backend,
								)
						else:
							self.assertEqual(
								type(spec._backend).__name__,
								NATIVE_BACKEND_CLASSES[(backend, type(spec))],
								spec._backend,
							)

				# Matching is unaffected.
				self.assertTrue(specs[1].match_file('a.txt'))
				self.assertFalse(specs[1].match_file('keep.txt'))

	def test_pattern_indices(self):
		"""
		The preserved flags do not disturb the pattern indices.
		"""
		patterns = [
			RegexPattern(None),
			RegexPattern(re.compile('secret', re.IGNORECASE), include=True),
			RegexPattern(re.compile('secret'), include=False),
		]
		for backend in BACKENDS:
			with self.subTest(backend=backend):
				require_backend(backend)
				spec = PathSpec(patterns, backend=backend)
				upper = spec.check_file('SECRET')
				lower = spec.check_file('secret')
				self.assertEqual((upper.include, upper.index), (True, 1))
				self.assertEqual((lower.include, lower.index), (False, 2))

	def test_gitignore_directory_precedence(self):
		"""
		A case-insensitive spec still applies the excluded-directory rule.
		"""
		patterns = []
		for line in ('logs/', '!logs/KEEP'):
			pattern = GitIgnoreSpecPattern(line)
			assert pattern.regex is not None, pattern
			# Rebuild the pattern as if it had been compiled case-insensitively.
			patterns.append(GitIgnoreSpecPattern(
				re.compile(pattern.regex.pattern, re.IGNORECASE), pattern.include,
			))
		for backend in BACKENDS:
			with self.subTest(backend=backend):
				require_backend(backend)
				spec = GitIgnoreSpec(patterns, backend=backend)
				result = spec.check_file('LOGS/KEEP')
				self.assertEqual((result.include, result.index), (True, 0))
				plain_result = PathSpec(patterns, backend=backend).check_file('LOGS/KEEP')
				self.assertEqual((plain_result.include, plain_result.index), (False, 1))

	def test_foreign_regex_falls_back(self):
		"""
		Foreign compiled expressions keep the behavior of their original engine.
		"""
		class ForeignRegex:
			pattern = 'secret'

			def match(self, file):
				return re.match(self.pattern, file, re.IGNORECASE)

			def search(self, file):
				return re.search(self.pattern, file, re.IGNORECASE)

		for spec_class in (PathSpec, GitIgnoreSpec):
			for backend in (None, 'best', 'simple'):
				with self.subTest(spec_class=spec_class, backend=backend):
					patterns = [RegexPattern(ForeignRegex(), include=True)]
					spec = spec_class(patterns, backend=backend)
					self.assertTrue(spec.match_file('SECRET'))
					self.assertFalse(spec.match_file('public'))
					self.assertTrue(type(spec._backend).__name__.startswith('Simple'))

		for backend in ('re2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for spec_class in (PathSpec, GitIgnoreSpec):
					with self.subTest(spec_class=spec_class):
						with self.assertRaisesRegex(ValueError, "backend='simple'"):
							spec_class([RegexPattern(ForeignRegex(), include=True)], backend=backend)

	def test_foreign_re2_options(self):
		"""
		Even an RE2 expression cannot be rebuilt without preserving its options.
		"""
		require_backend('re2')
		import re2

		options = re2.Options()
		options.case_sensitive = False
		pattern = RegexPattern(re2.compile('secret', options=options), include=True)
		for spec_class in (PathSpec, GitIgnoreSpec):
			with self.subTest(spec_class=spec_class):
				self.assertTrue(spec_class([pattern]).match_file('SECRET'))

	def test_inactive_foreign_regex_stays_native(self):
		"""
		A no-op foreign expression must not demote other active patterns.
		"""
		class ForeignRegex:
			def match(self, file):
				raise AssertionError('inactive expression must not be used')

		patterns = [
			RegexPattern(ForeignRegex(), include=None),
			RegexPattern(re.compile('secret'), include=True),
		]
		self.assertFalse(has_unsupported_flags(patterns))
		for backend in ('re2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for spec_class in (PathSpec, GitIgnoreSpec):
					with self.subTest(spec_class=spec_class):
						spec = spec_class(patterns, backend=backend)
						result = spec.check_file('secret')
						self.assertEqual((result.include, result.index), (True, 1))

	def test_translate_regex_flags(self):
		"""
		Only the flags a native engine understands are prepended.
		"""
		cases = [
			('secret', 0, 'secret'),
			('secret', re.UNICODE, 'secret'),
			('secret', re.DEBUG, 'secret'),
			('secret', re.ASCII, 'secret'),
			('secret', re.IGNORECASE, '(?i)secret'),
			('secret', re.MULTILINE, '(?m)secret'),
			('secret', re.DOTALL, '(?s)secret'),
			('secret', re.IGNORECASE | re.DOTALL, '(?is)secret'),
			('secret', re.IGNORECASE | re.MULTILINE | re.DOTALL, '(?ims)secret'),
			(b'secret', 0, b'secret'),
			(b'secret', re.IGNORECASE, b'(?i)secret'),
			(b'secret', re.IGNORECASE | re.DOTALL, b'(?is)secret'),
		]
		for expression, flags, expected in cases:
			with self.subTest(expression=expression, flags=flags):
				self.assertEqual(translate_regex_flags(expression, flags), expected)

	def test_supports_regex_flags(self):
		"""
		The flags that the native engines cannot express are reported.
		"""
		cases = [
			(re.compile('secret').flags, True),
			(re.compile(b'secret').flags, True),
			(re.compile('secret', re.IGNORECASE).flags, True),
			(re.compile('secret', re.MULTILINE).flags, True),
			(re.compile('secret', re.DOTALL).flags, True),
			(re.compile('secret', re.ASCII).flags, True),
			(re.compile('secret', re.IGNORECASE | re.MULTILINE | re.DOTALL).flags, True),
			(re.compile('(?i)secret').flags, True),
			(re.compile('secret', re.VERBOSE).flags, False),
			(re.compile('secret', re.IGNORECASE | re.VERBOSE).flags, False),
			(re.compile('secret', re.ASCII | re.IGNORECASE).flags, False),
			(int(re.UNICODE | re.DEBUG), True),
			(int(re.UNICODE | (1 << 20)), False),
		]
		for flags, expected in cases:
			with self.subTest(flags=flags):
				self.assertEqual(supports_regex_flags(flags), expected)

	def test_get_regex_flags(self):
		"""
		A pattern that Python did not compile has no flags to translate.
		"""
		class ForeignPattern(object):
			"""
			A regular expression that was not compiled by the *re* module.
			"""
			pattern = '(?i)secret'

		compiled = re.compile('secret', re.IGNORECASE)
		cases = [
			(compiled, int(compiled.flags)),
			(re.compile('secret'), int(re.compile('secret').flags)),
			('secret', 0),
			(b'secret', 0),
			(None, 0),
			(ForeignPattern(), 0),
		]
		for regex, expected in cases:
			with self.subTest(regex=regex):
				self.assertEqual(get_regex_flags(regex), expected)

	def test_has_unsupported_flags(self):
		"""
		Null patterns do not require preserving compile flags.
		"""
		cases = [
			([], False),
			([RegexPattern(None)], False),
			([RegexPattern(re.compile('secret'), include=True)], False),
			([RegexPattern(re.compile('secret', re.IGNORECASE), include=True)], False),
			([RegexPattern(re.compile('secret', re.VERBOSE), include=True)], True),
			([
				RegexPattern(re.compile('secret', re.IGNORECASE), include=True),
				RegexPattern(re.compile('secret', re.VERBOSE), include=False),
			], True),
			([
				RegexPattern(re.compile('secret', re.IGNORECASE), include=None),
				RegexPattern(re.compile('secret', re.VERBOSE), include=None),
			], False),
		]
		for patterns, expected in cases:
			with self.subTest(patterns=patterns):
				self.assertEqual(has_unsupported_flags(patterns), expected)


if __name__ == '__main__':
	unittest.main()
