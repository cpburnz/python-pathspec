"""Custom regex matching must not change when a native backend is installed."""

import re
import unittest
from unittest.mock import patch

from pathspec import GitIgnoreSpec, PathSpec, RegexPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

from .util import require_backend

SPEC_CLASSES: tuple[type[PathSpec], ...] = (PathSpec, GitIgnoreSpec)


class PublicPythonPattern(RegexPattern):
	def match_file(self, file):
		if file.startswith('private/'):
			return None
		return super().match_file(file)


class InheritedPublicPythonPattern(PublicPythonPattern):
	pass


class OrdinaryRegexPattern(RegexPattern):
	pass


class CustomRegexMatchingTest(unittest.TestCase):
	def test_automatic_backend_preserves_override(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				for pattern_class in (PublicPythonPattern, InheritedPublicPythonPattern):
					for selection in (None, 'best'):
						with self.subTest(backend=backend, spec_class=spec_class,
						                  pattern_class=pattern_class, selection=selection):
							require_backend(backend)
							pattern = pattern_class(re.compile(r'.*\.py$'), include=True)
							with patch('pathspec._backends.agg._BEST_BACKEND', backend):
								spec = spec_class([pattern], backend=selection)
							self.assertEqual(
								list(spec.match_files(['public/tool.py', 'private/secret.py'])),
								['public/tool.py'],
							)
							self.assertEqual(spec.check_file('public/tool.py').index, 0)
							self.assertFalse(spec.match_file('private/secret.py'))

	def test_explicit_native_backend_rejects_override(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				with self.subTest(backend=backend, spec_class=spec_class):
					require_backend(backend)
					pattern = PublicPythonPattern(re.compile(r'.*\.py$'), include=True)
					with self.assertRaisesRegex(ValueError, 'Use the simple backend instead'):
						spec_class([pattern], backend=backend)

	def test_combination_preserves_custom_exclusion(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				with self.subTest(backend=backend, spec_class=spec_class):
					require_backend(backend)
					with patch('pathspec._backends.agg._BEST_BACKEND', backend):
						original = spec_class([RegexPattern(re.compile(r'.*\.py$'), True)])
						exclusion = spec_class([PublicPythonPattern(re.compile(r'.*\.py$'), False)])
						combined = original + exclusion
						original += exclusion
					for spec in (combined, original):
						self.assertFalse(spec.match_file('public/tool.py'))
						self.assertTrue(spec.match_file('private/secret.py'))
						self.assertEqual(spec.check_file('public/tool.py').index, 1)
						self.assertEqual(spec.check_file('private/secret.py').index, 0)

	def test_inactive_override_keeps_native_backend(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				with self.subTest(backend=backend, spec_class=spec_class):
					require_backend(backend)
					patterns = [PublicPythonPattern(None), RegexPattern(re.compile(r'.*\.py$'), True)]
					with patch('pathspec._backends.agg._BEST_BACKEND', backend):
						spec = spec_class(patterns)
					self.assertFalse(type(spec._backend).__name__.startswith('Simple'))
					self.assertTrue(spec.match_file('private/secret.py'))
					self.assertEqual(spec.check_file('private/secret.py').index, 1)

	def test_inherited_default_matching_keeps_native_backend(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				for pattern_class in (OrdinaryRegexPattern, GitIgnoreSpecPattern):
					with self.subTest(backend=backend, spec_class=spec_class, pattern_class=pattern_class):
						require_backend(backend)
						pattern = pattern_class(re.compile(r'.*\.py$'), include=True)
						with patch('pathspec._backends.agg._BEST_BACKEND', backend):
							spec = spec_class([pattern])
						self.assertFalse(type(spec._backend).__name__.startswith('Simple'))
						self.assertTrue(spec.match_file('public/tool.py'))

	def test_instance_override(self):
		for backend in ('re2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				pattern = OrdinaryRegexPattern(re.compile(r'.*\.py$'), include=True)
				pattern.match_file = lambda file: None
				with patch('pathspec._backends.agg._BEST_BACKEND', backend):
					spec = PathSpec([pattern])
				self.assertFalse(spec.match_file('public/tool.py'))

	def test_instance_delegating_to_another_pattern(self):
		for backend in ('re2', 'hyperscan'):
			for spec_class in SPEC_CLASSES:
				with self.subTest(backend=backend, spec_class=spec_class):
					require_backend(backend)
					pattern = OrdinaryRegexPattern(re.compile(r'.*\.py$'), include=True)
					other = RegexPattern(re.compile(r'.*\.txt$'), include=True)
					pattern.match_file = other.match_file
					with patch('pathspec._backends.agg._BEST_BACKEND', backend):
						spec = spec_class([pattern])
					self.assertTrue(spec.match_file('readme.txt'))
					self.assertFalse(spec.match_file('tool.py'))
