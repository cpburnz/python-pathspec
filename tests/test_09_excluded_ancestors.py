"""
Tests descendant negations when a strict ancestor remains excluded.
"""

from unittest import TestCase

from .test_06_gitignore import GitIgnoreSpecMixin


class ExcludedAncestorTest(GitIgnoreSpecMixin, TestCase):
	"""
	Tests Git's rule that a file cannot be re-included under an excluded directory.
	"""

	def test_globstar_descendant_negation(self):
		"""
		A recursive file negation does not open the directories excluded by dir/**.
		"""
		for begin in self.parameterize_from_lines(['dir/**', '!dir/**/file']):
			with begin() as spec:
				self.assertEqual(spec.check_file('dir/file').include, False)
				for file in ('dir/nested/file', 'dir/a/b/c/file', 'dir/nested/'):
					with self.subTest(file=file):
						result = spec.check_file(file)
						self.assertEqual((result.include, result.index), (True, 0))
				self.assertIsNone(spec.check_file('dir/').include)
				self.assertIsNone(spec.check_file('elsewhere/file').include)

	def test_match_all_file_negation(self):
		"""
		A match-all shortcut also excludes parent directories before file negations.
		"""
		for begin in self.parameterize_from_lines(['*', '!**/a.py']):
			with begin() as spec:
				self.assertEqual(spec.check_file('a.py').include, False)
				for file in ('dir/a.py', 'dir/nested/a.py'):
					with self.subTest(file=file):
						result = spec.check_file(file)
						self.assertEqual((result.include, result.index), (True, 0))

	def test_parent_negation_does_not_open_all_descendants(self):
		"""
		Re-including one directory leaves its still-excluded nested directories closed.
		"""
		for begin in self.parameterize_from_lines(['*/', '!src/']):
			with begin() as spec:
				self.assertFalse(spec.match_file('src/a.txt'))
				for file in ('src/nested/file', 'src/a/b/file', 'src/nested/'):
					with self.subTest(file=file):
						result = spec.check_file(file)
						self.assertEqual((result.include, result.index), (True, 0))

	def test_reinclude_each_ancestor(self):
		"""
		A negated leaf becomes reachable only when each excluded ancestor is reopened.
		"""
		lines = ['dir/**', '!dir/a/', '!dir/**/file']
		for begin in self.parameterize_from_lines(lines):
			with begin() as spec:
				self.assertFalse(spec.match_file('dir/file'))
				self.assertFalse(spec.match_file('dir/a/file'))
				self.assertTrue(spec.match_file('dir/a/b/file'))
				self.assertTrue(spec.match_file('dir/a/b/c/file'))

		for begin in self.parameterize_from_lines(lines + ['!dir/a/b/']):
			with begin() as spec:
				self.assertFalse(spec.match_file('dir/a/b/file'))
				self.assertTrue(spec.match_file('dir/a/b/c/file'))

		for begin in self.parameterize_from_lines(lines + ['!dir/a/b/', '!dir/a/b/c/']):
			with begin() as spec:
				self.assertFalse(spec.match_file('dir/a/b/c/file'))

	def test_first_blocking_ancestor_index(self):
		"""
		The reported index belongs to the first directory preventing traversal.
		"""
		for begin in self.parameterize_from_lines([
			'dir/', 'dir/nested/', '!dir/nested/file',
		]):
			with begin() as spec:
				for file in ('dir/nested/file', 'dir/nested/'):
					result = spec.check_file(file)
					self.assertEqual((result.include, result.index), (True, 0))

		for begin in self.parameterize_from_lines([
			'dir/', 'dir/nested/', '!dir/', '!dir/nested/file',
		]):
			with begin() as spec:
				result = spec.check_file('dir/nested/file')
				self.assertEqual((result.include, result.index), (True, 1))

	def test_only_negations_and_unmatched_files(self):
		"""
		No implicit exclusion is introduced by ancestor inspection.
		"""
		for begin in self.parameterize_from_lines(['!src/', '!**/a.py']):
			with begin() as spec:
				self.assertFalse(spec.match_file('src/nested/a.py'))
				self.assertFalse(spec.match_file('src/nested/b.py'))
				self.assertIsNone(spec.check_file('elsewhere/file').include)
