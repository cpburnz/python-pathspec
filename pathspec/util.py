# encoding: utf-8
"""
This module provides utility methods for dealing with path-specs.
"""

import collections
import os
import os.path

from .compat import string_types

NORMALIZE_PATH_SEPS = [sep for sep in [os.sep, os.altsep] if sep and sep != '/']
"""
*NORMALIZE_PATH_SEPS* (``list`` of ``str``) contains the path separators
that need to be normalized to the POSIX separator for the current
operating system.
"""

_registered_patterns = {}
"""
*_registered_patterns* (``dict``) maps a name (``str``) to the
registered pattern factory (``callable``).
"""

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

def lookup_pattern(name):
	"""
	Lookups a registered pattern factory by name.

	*name* (``str``) is the name of the pattern factory.

	Returns the registered pattern factory (``callable``). If no pattern
	factory is registered, raises ``KeyError``.
	"""
	return _registered_patterns[name]

def match_files(patterns, files):
	"""
	Matches the files to the patterns.

	*patterns* (``Iterable`` of ``pathspec.Pattern``) contains the
	patterns to use.

	*files* (``Iterable`` of ``str``) contains the normalized files to be
	matched against *patterns*.

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

def normalize_files(files, separators=None):
	"""
	Normalizes the file paths to use the POSIX path separator (i.e., `/`).

	*files* (``Iterable`` of ``str``) contains the file paths to be
	normalized.

	*separators* (``Container`` of ``str``) optionally contains the path
	separators to normalize.

	Returns a ``dict`` mapping the normalized file path (``str``) to the
	original file path (``str``)
	"""
	if separators is None:
		separators = NORMALIZE_PATH_SEPS
	file_map = {}
	for path in files:
		norm = path
		for sep in separators:
			norm = norm.replace(sep, '/')
		file_map[norm] = path
	return file_map

def register_pattern(name, pattern_factory, override=None):
	"""
	Registers the specified pattern factory.

	*name* (``str``) is the name to register the pattern factory under.

	*pattern_factory* (``callable``) is used to compile patterns. It must
	accept an uncompiled pattern (``str``) and return the compiled pattern
	(``pathspec.Pattern``).

	*override* (``bool``) optionally is whether to allow overriding an
	already registered pattern under the same name (``True``), instead of
	raising an ``AlreadyRegisteredError`` (``False``). Default is ``None``
	for ``False``.
	"""
	if not isinstance(name, string_types):
		raise TypeError("name:{!r} is not a string.".format(name))
	if not callable(pattern_factory):
		raise TypeError("pattern_factory:{!r} is not callable.".format(pattern_factory))
	if name in _registered_patterns and not override:
		raise AlreadyRegisteredError(name, _registered_patterns[name])
	_registered_patterns[name] = pattern_factory


class AlreadyRegisteredError(Exception):
	"""
	The ``AlreadyRegisteredError`` exception is raised when a pattern
	factory is registered under a name already in use.
	"""

	def __init__(self, name, pattern_factory):
		"""
		Initializes the ``AlreadyRegisteredError`` instance.

		*name* (``str``) is the name of the registered pattern.

		*pattern_factory* (``callable``) is the registered pattern factory.
		"""
		super(AlreadyRegisteredError, self).__init__(name, pattern_factory)

	@property
	def message(self):
		"""
		*message* (``str``) is the error message.
		"""
		return "{name!r} is already registered for pattern factory:{!r}.".format(
			name=self.name,
			pattern_factory=self.pattern_factory,
		)

	@property
	def name(self):
		"""
		*name* (``str``) is the name of the registered pattern.
		"""
		return self.args[0]

	@property
	def pattern_factory(self):
		"""
		*pattern_factory* (``callable``) is the registered pattern factory.
		"""
		return self.args[1]


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
