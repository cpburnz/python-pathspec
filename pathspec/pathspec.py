# encoding: utf-8
"""
This module provides an object oriented interface for pattern matching
of files.
"""

import collections

from . import util
from .compat import string_types, viewkeys


class PathSpec(object):
	"""
	The ``PathSpec`` instance is a wrapper around a list of compiled
	``pathspec.Pattern`` instances.
	"""

	def __init__(self, patterns):
		"""
		Initializes the ``PathSpec`` instance.

		*patterns* (``collections.Container`` or ``collections.Iterable``)
		yields each compiled pattern (``pathspec.Pattern``).
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

		*pattern_factory* can be either the name of a registered pattern
		factory (``str``), or a ``callable`` used to compile patterns. It
		must accept an uncompiled pattern (``str``) and return the compiled
		pattern (``pathspec.Pattern``).

		*lines* (``collections.Iterable``) yields each uncompiled pattern
		(``str``). This simply has to yield each line so it can be a
		``file`` (e.g., ``open(file)`` or ``io.StringIO(text)``) or the
		result from ``str.splitlines()``.

		Returns the ``PathSpec`` instance.
		"""
		if isinstance(pattern_factory, string_types):
			pattern_factory = util.lookup_pattern(pattern_factory)
		if not callable(pattern_factory):
			raise TypeError("pattern_factory:{!r} is not callable.".format(pattern_factory))

		lines = [pattern_factory(line) for line in lines if line]
		return cls(lines)

	def match_file(self, file, separators=None):
		"""
		Matches the file to this path-spec.

		*file* (``str``) is the file path to be matched against
		`self.patterns`.

		*separators* (``collections.Container`` of ``str``) optionally
		contains the path separators to normalize. This does not need to
		include the POSIX path separator (`/`), but including it will not
		affect the results. Default is ``None`` to determine the separators
		based upon the current operating system by examining `os.sep` and
		`os.altsep`. To prevent normalization, pass an empty container
		(e.g., an empty tuple `()`).

		Returns ``True`` if *file* matched; otherwise, ``False``.
		"""
		norm_file = util.normalize_file(file, separators=separators)
		return util.match_file(self.patterns, norm_file)

	def match_files(self, files, separators=None):
		"""
		Matches the files to this path-spec.

		*files* (``collections.Iterable`` of ``str``) contains the file
		paths to be matched against *patterns*.

		*separators* (``collections.Container`` of ``str``) optionally
		contains the path separators to normalize. This does not need to
		include the POSIX path separator (`/`), but including it will not
		affect the results. Default is ``None`` to determine the separators
		based upon the current operating system by examining `os.sep` and
		`os.altsep`. To prevent normalization, pass an empty container
		(e.g., an empty tuple `()`).

		Returns the matched files (``collections.Iterable`` of ``str``).
		"""
		file_map = util.normalize_files(files, separators=separators)
		matched_files = util.match_files(self.patterns, viewkeys(file_map))
		for path in matched_files:
			yield file_map[path]

	def match_tree(self, root):
		"""
		Walks the specified root path for all files and matches them to this
		path-spec.

		*root* (``str``) is the root directory to search for files.

		Returns the matched files (``collections.Iterable`` of ``str``).
		"""
		files = util.iter_tree(root)
		return self.match_files(files)
