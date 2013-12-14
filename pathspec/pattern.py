# coding: utf-8
"""
This module provides the base definition for patterns.
"""

import re

from .compat import string_types


class Pattern(object):
	"""
	The ``Pattern`` class is the abstract definition of a pattern.
	"""

	# Make the class dict-less.
	__slots__ = ('include',)

	def __init__(self, include):
		"""
		Initializes the ``Pattern`` instance.

		*include* (``bool``) is whether the matched files should be included
		(``True``), excluded (``False``), or is a null-operation (``None``).
		"""

		self.include = include
		"""
		*include* (``bool``) is whether the matched files should be included
		(``True``), excluded (``False``), or is a null-operation (``None``).
		"""

	def match(self, files):
		"""
		Matches this pattern against the specified files.

		*files* (``Iterable``) contains each file (``str``) relative to the
		root directory (e.g., "relative/path/to/file").

		Returns an ``Iterable`` yielding each matched file path (``str``).
		"""
		raise NotImplementedError("{}.{} must override match().".format(self.__class__.__module__, self.__class__.__name__))


class RegexPattern(Pattern):
	"""
	The ``RegexPattern`` class is an implementation of a pattern using
	regular expressions.
	"""

	# Make the class dict-less.
	__slots__ = ('regex',)

	def __init__(self, regex, *args, **kw):
		"""
		Initializes the ``RegexPattern`` instance.

		*regex* (``RegexObject`` or ``str``) is the regular expression for
		the pattern.

		`*args` are positional arguments to send to the ``Pattern``
		constructor.

		`**kw` are keyword arguments to send to the ``Pattern`` constructor.
		"""

		self.regex = None
		"""
		*regex* (``RegexObject``) is the regular expression for the pattern.
		"""

		# NOTE: Make sure to allow a null regex pattern to be passed for a
		# null-operation.
		if isinstance(regex, string_types):
			regex = re.compile(regex)

		super(RegexPattern, self).__init__(*args, **kw)

		self.regex = regex

	def match(self, files):
		"""
		Matches this pattern against the specified files.

		*files* (``Iterable``) contains each file (``str``) relative to the
		root directory (e.g., "relative/path/to/file").

		Returns an ``Iterable`` yielding each matched file path (``str``).
		"""
		if self.include is not None:
			for path in files:
				if self.regex.match(path) is not None:
					yield path
