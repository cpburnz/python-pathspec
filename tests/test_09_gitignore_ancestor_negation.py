"""Test directory negations below an excluded ancestor."""

from unittest import TestCase
from unittest.mock import patch

from .test_06_gitignore import GitIgnoreSpecMixin


class AncestorNegationTest(GitIgnoreSpecMixin, TestCase):

	def test_excluded_ancestor(self):
		# Expected ignore decisions and pattern indices verified with
		# git check-ignore --no-index (Git 2.52.0.windows.1).
		for lines, paths in (
			(['a/', '!a/b/'], ['a/b/file.txt', 'a/b/c/deep.txt']),
			(['a/', '!a/b/', '!*.txt'], ['a/b/file.txt']),
			(['a/', '!a/b/', '*.txt'], ['a/b/file.txt']),
			(['d/**/', '!d/child/'], ['d/child/grand/deep.txt']),
			(['a/**', '!a/b/**'], ['a/b/file.txt', 'a/b/c/deep.txt']),
			(['a/**', '!*.txt'], ['a/b/file.txt']),
			(['*', '!*.txt'], ['a/top.txt', 'a/b/file.txt']),
		):
			for sub_test in self.parameterize_from_lines(lines):
				with sub_test() as spec:
					results = list(spec.check_files(iter(paths)))
					self.assertEqual(
						[(r.include, r.index) for r in results],
						[(True, 0)] * len(paths),
						(lines, results),
					)
					self.assertEqual(list(spec.match_files(iter(paths))), paths)
					self.assertEqual(list(spec.match_files(iter(paths), negate=True)), [])

	def test_reincluded_ancestors(self):
		for lines, path in (
			(['a/', '!a/', '!a/b/'], 'a/b/file.txt'),
			(['a/*', '!a/b/'], 'a/b/file.txt'),
			(['d/**/', '!d/child/'], 'd/child/top.txt'),
			(['d/**/', '!d/child/', '!d/child/grand/'], 'd/child/grand/deep.txt'),
			(['!a/b/'], 'a/b/file.txt'),
			(['a/**', '!*.txt'], 'a/top.txt'),
			(['*', '!a/', '!a/**'], 'a/b/file.txt'),
		):
			for sub_test in self.parameterize_from_lines(lines):
				with sub_test() as spec:
					self.assertFalse(spec.match_file(path), (lines, path))

	def test_ancestors_checked_once(self):
		# Keep the ancestor walk iterative even with many re-included levels.
		path = 'a/' * 40 + 'file.txt'
		for sub_test in self.parameterize_from_lines(['a/', '!a/']):
			with sub_test() as spec:
				backend_type = type(spec._backend)
				original = backend_type._match
				calls = []

				def counted_match(backend, file, check_ancestors):
					calls.append((file, check_ancestors))
					return original(backend, file, check_ancestors)

				with patch.object(backend_type, '_match', counted_match):
					self.assertFalse(spec.match_file(path))
				self.assertLessEqual(len(calls), 41)
				self.assertTrue(all(not check for _, check in calls[1:]))
