# coding: utf-8
"""
This module provides an object oriented interface for pattern matching
of files.
"""

import collections

from . import util


class PathSpec(object):
	"""
	The ``PathSpec`` instance is a wrapper around a list of compiled
	``pathspec.Pattern`` instances.
	"""

	def __init__(self, patterns):
		"""
		Initializes the ``PathSpec`` instance.

		*patterns* (``Iterable``) yields each compiled pattern
		(``pathspec.Pattern``).
		"""

		self.patterns = None
		"""
		*patterns* (``Container``) contains the compiled patterns,
		"""

		self.patterns = patterns if isinstance(patterns, collections.Container) else list(patterns)

	def __len__(self):
		"""
		Returns the number of compiled patterns this path-spec contains
		(``int``).
		"""
		return len(self.patterns)

	@classmethod
	def from_lines(cls, pattern_factory, lines):
		"""
		Compiles the pattern lines.

		*pattern_factory* (``callable``) is used to compile patterns. It
		must accept an uncompiled pattern (``str``) and return the compiled
		pattern (``pathspec.Pattern``).

		*lines* (``Iterable``) yields each uncompiled pattern (``str``). This
		simply has to yield each line so it can be a ``file`` (e.g., ``open(file)``
		or ``io.StringIO(text)``) or the result from ``str.splitlines()``.

		Returns the ``PathSpec`` instance.
		"""
		if not callable(pattern_factory):
			raise TypeError("pattern_factory:{!r} is not callable.".format(pattern_factory))

		lines = [pattern_factory(line) for line in lines if line]
		return cls(lines)

	def match_files(self, files):
		"""
		Matches the files to this path-spec.

		*files* (``Iterable`` of ``str``) contains the files to be matched
		against *patterns*.

		Returns the matched files (``set`` of ``str``).
		"""
		return util.match_files(self.patterns, files)

	def match_tree(self, root):
		"""
		Walks the specified root path for all files and matches them to this
		path-spec.

		*root* (``str``) is the root directory to search for files.

		Returns the matched files (``set`` of ``str``).
		"""
		files = util.iter_tree(root)
		return self.match_files(files)
