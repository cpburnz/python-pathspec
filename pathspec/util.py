# encoding: utf-8
"""
This module provides utility methods for dealing with path-specs.
"""

import collections
import os
import os.path
import posixpath
import stat

from .compat import string_types

NORMALIZE_PATH_SEPS = [sep for sep in [os.sep, os.altsep] if sep and sep != posixpath.sep]
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
	Walks the specified directory for all files.

	*root* (``str``) is the root directory to search for files.

	Raises ``RecursionError`` if recursion is detected.

	Returns an ``collections.Iterable`` yielding the path to each file
	(``str``) relative to *root*.
	"""
	for file_rel in _iter_tree_next(os.path.abspath(root), '', {}):
		yield file_rel

def _iter_tree_next(root_full, dir_rel, memo):
	"""
	Scan the directory for all descendant files.

	*root_full* (``str``) the absolute path to the root directory.

	*dir_rel* (``str``) the path to the directory to scan relative to
	*root_full*.

	*memo* (``dict``) keeps track of ancestor directories encountered.
	Maps each ancestor real path (``str``) to relative path (``str``).
	"""
	dir_full = os.path.join(root_full, dir_rel)
	dir_real = os.path.realpath(dir_full)

	# Remember each encountered ancestor directory and its canonical
	# (real) path. If a canonical path is encountered more than once,
	# recursion has occurred.
	if dir_real not in memo:
		memo[dir_real] = dir_rel
	else:
		raise RecursionError(real_path=dir_real, first_path=memo[dir_real], second_path=dir_rel)

	for node in os.listdir(dir_full):
		node_rel = os.path.join(dir_rel, node)
		node_full = os.path.join(root_full, node_rel)
		node_stat = os.stat(node_full)

		if stat.S_ISDIR(node_stat.st_mode):
			# Child node is a directory, recurse into it and yield its
			# decendant files.
			for file_rel in _iter_tree_next(root_full, node_rel, memo):
				yield file_rel

		elif stat.S_ISREG(node_stat.st_mode):
			# Child node is a file, yield it.
			yield node_rel

	# NOTE: Make sure to remove the canonical (real) path of the directory
	# from the ancestors memo once we are done with it. This allows the
	# same directory to appear multiple times. If this is not done, the
	# second occurance of the directory will be incorrectly interpreted as
	# a recursion. See <https://github.com/cpburnz/python-path-specification/pull/7>.
	del memo[dir_real]

def lookup_pattern(name):
	"""
	Lookups a registered pattern factory by name.

	*name* (``str``) is the name of the pattern factory.

	Returns the registered pattern factory (``callable``). If no pattern
	factory is registered, raises ``KeyError``.
	"""
	return _registered_patterns[name]

def match_file(patterns, file):
	"""
	Matches the file to the patterns.

	*patterns* (``collections.Iterable`` of ``pathspec.Pattern``) contains
	the patterns to use.

	*file* (``str``) is the normalized file path to be matched against
	*patterns*.

	Returns ``True`` if *file* matched; otherwise, ``False``.
	"""
	matched = False
	for pattern in patterns:
		if pattern.include is not None:
			if file in pattern.match((file,)):
				matched = pattern.include
	return matched

def match_files(patterns, files):
	"""
	Matches the files to the patterns.

	*patterns* (``collections.Iterable`` of ``pathspec.Pattern``) contains
	the patterns to use.

	*files* (``collections.Iterable`` of ``str``) contains the normalized
	file paths to be matched against *patterns*.

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

def normalize_file(file, separators=None):
	"""
	Normalizes the file path to use the POSIX path separator (i.e., `/`).

	*file* (``str``) is the file path.

	Returns the normalized file path (``str``).
	"""
	if separators is None:
		separators = NORMALIZE_PATH_SEPS
	norm_file = file
	for sep in separators:
		norm_file = norm_file.replace(sep, posixpath.sep)
	return norm_file

def normalize_files(files, separators=None):
	"""
	Normalizes the file paths to use the POSIX path separator (i.e., `/`).

	*files* (``collections.Iterable`` of ``str``) contains the file paths
	to be normalized.

	*separators* (``collections.Container`` of ``str``) optionally
	contains the path separators to normalize.

	Returns a ``dict`` mapping the normalized file path (``str``) to the
	original file path (``str``)
	"""
	return {normalize_file(path, separators=separators): path for path in files}

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
