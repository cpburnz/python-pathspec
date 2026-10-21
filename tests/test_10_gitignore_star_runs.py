"""
Test runs of three or more asterisks that span a whole gitignore path segment.
"""

import unittest

from pathspec import GitIgnoreSpec
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern

# Each case is (pattern, paths that Git matches, paths that Git does not match).
# Git's wildmatch treats a run of asterisks that spans a whole path segment as
# a single globstar (``**``).
CASES = (
	('***/x', ('x', 'a/x', 'a/b/x'), ('xx', 'a/xx')),
	('****/x', ('x', 'a/x', 'a/b/x'), ('xx',)),
	('a/***', ('a/b', 'a/b/c'), ('a', 'b/a', 'b/a/c')),
	('a/***/b', ('a/b', 'a/x/b', 'a/x/y/b'), ('a/x', 'b/x/b')),
	('***', ('a', 'a/b', 'a/b/c'), ()),
	# A run of asterisks inside a segment is still a single asterisk.
	('a***b', ('ab', 'axxb'), ('a/b', 'a/x/b')),
)


class StarRunTest(unittest.TestCase):
	"""
	The :class:`StarRunTest` class tests asterisk runs against Git's behavior.
	"""

	def test_pattern_classes(self):
		"""
		Tests that both gitignore pattern classes treat a segment of asterisks
		like a double-asterisk.
		"""
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern):
			for line, matches, misses in CASES:
				with self.subTest(factory=factory.__name__, line=line):
					pattern = factory(line)
					for path in matches:
						self.assertTrue(pattern.match_file(path), path)
					for path in misses:
						self.assertFalse(pattern.match_file(path), path)

	def test_gitignore_spec(self):
		"""
		Tests that :class:`.GitIgnoreSpec` matches the same paths as Git.
		"""
		for line, matches, misses in CASES:
			with self.subTest(line=line):
				spec = GitIgnoreSpec.from_lines([line])
				for path in matches:
					self.assertTrue(spec.match_file(path), path)
				for path in misses:
					self.assertFalse(spec.match_file(path), path)
