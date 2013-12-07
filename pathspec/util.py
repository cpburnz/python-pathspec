# coding: utf-8
"""
This module provides utility methods for dealing with path-specs.
"""

import collections
import os
import os.path

def iter_tree(root):
	"""
	Walks the specified root path for all files.

	*root* (``str``) is the root directory to search for files.

	Raises ``RecursionError`` if recursion is detected.

	Returns an ``Iterable`` yielding each file path (``str``) relative to
	*root*.

	.. _`recursion`: http://docs.python.org/2/library/os.html#os.walk
	"""
	# Keep track of files encountered. Map real path to relative path.
	memo = {}

	root = os.path.abspath(root)
	for parent, _dirs, files in os.walk(root, followlinks=True):
		# Get parent path relative to root path.
		parent = os.path.relpath(parent, root)

		# Check for recursion.
		real = os.path.realpath(parent)
		if real in memo:
			raise RecursionError(real_path=real, first_path=memo[real], second_path=parent)
		memo[real] = parent

		# Yield files.
		for path in files:
			if parent != '.':
				path = os.path.join(parent, path)
			yield path

def match_files(patterns, files):
	"""
	Matches the files to the patterns.

	*patterns* (``Iterable`` of ``pathspec.Pattern``) contains the
	patterns to use.

	*files* (``Iterable`` of ``str``) contains the files to be matched
	against *patterns*.

	Returns the matched files (``set`` of ``str``).
	"""
	all_files = files if isinstance(files, collections.Container) else list(files)
	return_files = set()
	for pattern in patterns:
		if pattern.include is not None:
			result_files = pattern.match(all_files)
			if pattern.include:
				return_files.update(result_files)
			else:
				return_files.difference_update(result_files)
	return return_files


class RecursionError(Exception):
	"""
	The ``RecursionError`` exception is raised when recursion is detected.
	"""

	def __init__(self, real_path, first_path, second_path):
		"""
		Initializes the ``RecursionError`` instance.

		*real_path* (``str``) is the real path that recursion was
		encountered on.

		*first_path* (``str``) is the first path encountered for
		*real_path*.

		*second_path* (``str``) is the second path encountered for
		*real_path*.
		"""
		super(RecursionError, self).__init__(real_path, first_path, second_path)

	@property
	def first_path(self):
		"""
		*first_path* (``str``) is the first path encountered for
		*real_path*.
		"""
		return self.args[1]

	@property
	def message(self):
		"""
		*message* (``str``) is the error message.
		"""
		return "Real path {real!r} was encountered at {first!r} and then {second!r}.".format(
			real=self.real_path,
			first=self.first_path,
			second=self.second_path,
		)

	@property
	def real_path(self):
		"""
		*real_path* (``str``) is the real path that recursion was
		encountered on.
		"""
		return self.args[0]

	@property
	def second_path(self):
		"""
		*second_path* (``str``) is the second path encountered for
		*real_path*.
		"""
		return self.args[2]
