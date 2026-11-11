"""
This module provides the simple backend for :class:`~pathspec.pathspec.PathSpec`.

WARNING: The *pathspec._backends.simple* package is not part of the public API.
Its contents and structure are likely to change.
"""

import platform
import re
from collections.abc import (
	Sequence)
from typing import (
	Optional)  # Replaced by `X | None` in 3.10.

from pathspec.backend import (
	_Backend)
from pathspec.pattern import (
	Pattern,
	RegexPattern)
from pathspec._typing import (
	override)  # Added in 3.12.

from .._utils import (
	enumerate_patterns)

_USE_REGEX = platform.python_implementation() != 'PyPy'
"""
*_USE_REGEX* (:class:`bool`) is whether to test a pattern with its regex
directly. It is faster on CPython, but not on PyPy, where the JIT already
removes the cost of :meth:`.RegexPattern.match_file`.
"""


class SimplePsBackend(_Backend):
	"""
	The :class:`SimplePsBackend` class is the default (or simple) implementation
	used by :class:`~pathspec.pathspec.PathSpec` for matching files.
	"""

	def __init__(
		self,
		patterns: Sequence[Pattern],
		*,
		no_filter: Optional[bool] = None,
		no_reverse: Optional[bool] = None,
	) -> None:
		"""
		Initialize the :class:`SimplePsBackend` instance.

		*patterns* (:class:`Sequence` of :class:`.Pattern`) contains the compiled
		patterns.

		*no_filter* (:class:`bool`) is whether to keep no-op patterns (:data:`True`),
		or remove them (:data:`False`).

		*no_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""

		self._is_reversed: bool = not no_reverse
		"""
		*_is_reversed* (:class:`bool`) is whether to the pattern order was reversed.
		"""

		self._patterns: list[tuple[int, Pattern]] = enumerate_patterns(
			patterns, filter=not no_filter, reverse=not no_reverse,
		)
		"""
		*_patterns* (:class:`list` of :class:`tuple`) contains the enumerated
		patterns.
		"""

		self._tests: list[tuple[int, bool, Optional[re.Pattern], Pattern]] = [
			(index, pattern.include, (
				pattern.regex
				if _USE_REGEX
				and type(pattern).match_file is RegexPattern.match_file
				and type(pattern.regex) is re.Pattern
				else None
			), pattern)
			for index, pattern in self._patterns
			if pattern.include is not None
		]
		"""
		*_tests* (:class:`list` of :class:`tuple`) contains the index, include,
		regex, and pattern of each pattern with an include. The regex is set when
		the pattern uses :meth:`.RegexPattern.match_file` with a :class:`re.Pattern`.
		Then the file is tested with the regex search, which gives the same result
		without creating a :class:`.RegexMatchResult`. Otherwise, the regex is
		:data:`None` and the file is tested with :meth:`.Pattern.match_file`.
		"""

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		tests = self._tests
		if self._is_reversed:
			# The first pattern that matches takes precedence.
			for index, include, regex, pattern in tests:
				if (
					regex.search(file) if regex is not None else pattern.match_file(file)
				) is not None:
					return (include, index)

			return (None, None)

		# The last pattern that matches takes precedence.
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		for index, include, regex, pattern in tests:
			if (
				regex.search(file) if regex is not None else pattern.match_file(file)
			) is not None:
				out_include = include
				out_index = index

		return (out_include, out_index)
