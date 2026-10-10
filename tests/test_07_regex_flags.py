"""
This script tests backend selection for compiled regular expression flags.
"""

import copy
import re
import unittest
import warnings

from pathspec import (
	GitIgnoreSpec,
	PathSpec,
	RegexPattern)
from pathspec._backends import agg
from pathspec._backends._utils import (
	has_regex_flags)
from pathspec._backends.hyperscan.gitignore import (
	HyperscanGiBackend)
from pathspec._backends.hyperscan.pathspec import (
	HyperscanPsBackend)
from pathspec._backends.re2.gitignore import (
	Re2GiBackend)
from pathspec._backends.re2.pathspec import (
	Re2PsBackend)
from pathspec._backends.simple.gitignore import (
	SimpleGiBackend)
from pathspec._backends.simple.pathspec import (
	SimplePsBackend)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)

from .util import (
	require_backend)


class RegexFlagsTest(unittest.TestCase):
	"""
	Compiled flags must not be silently discarded by native backends.
	"""

	def test_best_preserves_flags(self):
		"""
		Automatic selection preserves the original Python regex semantics.
		"""
		cases = [
			('secret', re.IGNORECASE, 'SECRET', 'public'),
			('^secret$', re.MULTILINE, 'x\nsecret\ny', 'xsecret'),
			('^a.b$', re.DOTALL, 'a\nb', 'ab'),
			('s e c r e t # note', re.VERBOSE, 'secret', 's e c r e t # note'),
			('secret # [', re.VERBOSE, 'secret', 'public'),
			('^[a-z]+$', re.IGNORECASE, '\u0130\u0131\u017f\u212a', '!'),
			('^\\w+$', re.ASCII, 'secret', '\u00e9'),
			('^[a-z]+$', re.ASCII | re.IGNORECASE, 'SECRET', '\u0130'),
			('^secret.*end$', re.IGNORECASE | re.MULTILINE | re.DOTALL,
			 'x\nSECRET\nEND\ny', 'SECRET'),
			('(?i)^secret$', re.MULTILINE, 'x\nSECRET\ny', 'xsecret'),
		]
		for spec_cls, simple_cls in (
			(PathSpec, SimplePsBackend), (GitIgnoreSpec, SimpleGiBackend),
		):
			for backend in (None, 'best', 'simple'):
				for expression, flags, match, no_match in cases:
					with self.subTest(spec=spec_cls, backend=backend, flags=flags, expression=expression):
						pattern = RegexPattern(re.compile(expression, flags), include=True)
						spec = spec_cls([pattern], backend=backend)
						self.assertTrue(spec.match_file(match))
						self.assertFalse(spec.match_file(no_match))
						self.assertIsInstance(spec._backend, simple_cls)

	def test_explicit_native_rejects_flags(self):
		"""
		Explicit native selection reports unsupported compiled flags.
		"""
		for backend, ps_backend, gi_backend in (
			('re2', Re2PsBackend, Re2GiBackend),
			('hyperscan', HyperscanPsBackend, HyperscanGiBackend),
		):
			with self.subTest(backend=backend):
				require_backend(backend)
				for flags in (re.I, re.M, re.S, re.X, re.A, re.I | re.M | re.S):
					for factory in (
						lambda patterns: PathSpec(patterns, backend=backend),
						lambda patterns: GitIgnoreSpec(patterns, backend=backend),
						ps_backend, gi_backend,
					):
						with self.subTest(flags=flags, factory=factory):
							patterns = [RegexPattern(re.compile('secret', flags), include=True)]
							with self.assertRaisesRegex(ValueError, "backend='simple'"):
								factory(patterns)

	def test_rejected_iadd_keeps_state(self):
		"""
		Rejecting flags during an in-place addition leaves the spec unchanged.
		"""
		for backend in ('re2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for spec_cls in (PathSpec, GitIgnoreSpec):
					with self.subTest(spec=spec_cls):
						spec = spec_cls([RegexPattern(re.compile('secret'), include=True)], backend=backend)
						patterns, matcher = spec.patterns, spec._backend
						other = spec_cls([RegexPattern(re.compile('secret', re.I), include=False)], backend='simple')
						with self.assertRaisesRegex(ValueError, "backend='simple'"):
							spec += other
						self.assertIs(spec.patterns, patterns)
						self.assertIs(spec._backend, matcher)
						self.assertEqual(len(spec), 1)
						self.assertTrue(spec.match_file('secret'))
						self.assertFalse(spec.match_file('SECRET'))

	def test_flag_detection(self):
		"""
		Detect external flags without translating bytes or unknown Python flags.
		"""
		for expression, flags, expected in (
			('secret', 0, False),
			('secret', re.UNICODE, False),
			('(?i)secret', re.I, False),
			('(?i)secret', re.M, True),
			('secret', 1 << 20, True),
			(b'secret', 0, False),
			(b'secret', re.I, True),
			(b'secret', re.LOCALE, True),
			(b'(?i)secret', re.I, False),
		):
			with self.subTest(expression=expression, flags=flags):
				pattern = RegexPattern(re.compile(expression, flags), include=True)
				self.assertEqual(has_regex_flags([pattern]), expected)
				pattern.include = None
				self.assertFalse(has_regex_flags([pattern]))
		self.assertFalse(has_regex_flags([]))
		self.assertFalse(has_regex_flags([RegexPattern(None)]))

	def test_probe_does_not_expose_warnings(self):
		"""
		Compiling a probe does not leak warnings or change the outer filters.
		"""
		for expression in ('secret # [a&&b]', 'secret # [[a]', 'secret # [a--b]'):
			pattern = RegexPattern(re.compile(expression, re.X), include=True)
			for backend in (None, 'best', 'simple', 're2', 'hyperscan'):
				with self.subTest(expression=expression, backend=backend):
					require_backend(backend)
					for action in ('always', 'error'):
						with self.subTest(action=action):
							with warnings.catch_warnings(record=True) as caught:
								warnings.simplefilter(action, FutureWarning)
								filters = warnings.filters[:]
								re.purge()
								self.assertTrue(has_regex_flags([pattern]))
								re.purge()
								if backend in ('re2', 'hyperscan'):
									with self.assertRaisesRegex(ValueError, "backend='simple'"):
										PathSpec([pattern], backend=backend)
								else:
									self.assertTrue(PathSpec([pattern], backend=backend).match_file('secret'))
								self.assertEqual(warnings.filters, filters)
								self.assertEqual(caught, [])

	def test_mixed_flags_and_rebuild(self):
		"""
		Fallback keeps pattern indices and precedence after copying or adding.
		"""
		for spec_cls in (PathSpec, GitIgnoreSpec):
			with self.subTest(spec=spec_cls):
				spec = spec_cls([
					RegexPattern(None),
					RegexPattern(re.compile('secret', re.I), include=True),
					RegexPattern(re.compile('secret'), include=False),
				])
				for current in (spec, copy.copy(spec), spec + spec_cls([])):
					upper = current.check_file('SECRET')
					lower = current.check_file('secret')
					self.assertEqual((upper.include, upper.index), (True, 1))
					self.assertEqual((lower.include, lower.index), (False, 2))
					self.assertEqual(list(current.match_files(['SECRET', 'secret', 'public'])), ['SECRET'])
				base = spec_cls([RegexPattern(re.compile('secret'), include=False)])
				base += spec_cls([RegexPattern(re.compile('secret', re.I), include=True)])
				result = base.check_file('SECRET')
				self.assertEqual((result.include, result.index), (True, 1))

	def test_gitignore_directory_priority(self):
		"""
		GitIgnoreSpec fallback retains its ancestor-directory exclusion rules.
		"""
		patterns = []
		for line in ('logs/', '!logs/KEEP'):
			pattern = GitIgnoreSpecPattern(line)
			assert pattern.regex is not None, pattern
			patterns.append(GitIgnoreSpecPattern(
				re.compile(pattern.regex.pattern, re.I), pattern.include,
			))
		for backend in (None, 'best', 'simple'):
			with self.subTest(backend=backend):
				spec = GitIgnoreSpec(patterns, backend=backend)
				self.assertIsInstance(spec._backend, SimpleGiBackend)
				result = spec.check_file('LOGS/KEEP')
				self.assertEqual((result.include, result.index), (True, 0))
				plain_result = PathSpec(patterns, backend=backend).check_file('LOGS/KEEP')
				self.assertEqual((plain_result.include, plain_result.index), (False, 1))

	def test_native_controls(self):
		"""
		Plain regexes, inline flags, and no-op patterns keep native selection.
		"""
		for backend in ('best', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for spec_cls in (PathSpec, GitIgnoreSpec):
					for expression, file in (
						('secret', 'secret'),
						('(?i)secret', 'SECRET'),
						('(?m)^secret$', 'x\nsecret\ny'),
						('(?s)^a.b$', 'a\nb'),
					):
						with self.subTest(spec=spec_cls, expression=expression):
							patterns = [
								RegexPattern(re.compile('ignored', re.I), include=None),
								RegexPattern(re.compile(expression), include=True),
							]
							spec = spec_cls(patterns, backend=backend)
							expected = agg._BEST_BACKEND if backend == 'best' else backend
							self.assertEqual(type(spec._backend).__name__, {
								('re2', PathSpec): 'Re2PsBackend',
								('re2', GitIgnoreSpec): 'Re2GiBackend',
								('hyperscan', PathSpec): 'HyperscanPsBackend',
								('hyperscan', GitIgnoreSpec): 'HyperscanGiBackend',
								('simple', PathSpec): 'SimplePsBackend',
								('simple', GitIgnoreSpec): 'SimpleGiBackend',
							}[expected, spec_cls])
							self.assertTrue(spec.match_file(file))
							self.assertFalse(spec.match_file('public'))


if __name__ == '__main__':
	unittest.main()
