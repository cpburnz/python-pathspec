"""
This module provides the :module:`re2` backend for :class:`~pathspec.pathspec.PathSpec`.

WARNING: The *pathspec._backends.re2* package is not part of the public API. Its
contents and structure are likely to change.
"""

import re
from collections.abc import (
	Sequence)
from copy import (
	copy)
from typing import (
	Optional,  # Replaced by `X | None` in 3.10.
	cast)

try:
	import re2
except ModuleNotFoundError:
	re2 = None

from ...pattern import (
	RegexPattern)

from ..simple.pathspec import (
	SimplePsBackend)

from .base import (
	re2_error)


class Re2PsBackend(SimplePsBackend):
	"""
	The :class:`Re2PsBackend` class is the :module:`re2` implementation used by
	:class:`~pathspec.pathspec.PathSpec` for matching files.
	"""

	patterns: Sequence[RegexPattern]

	def __init__(
		self,
		patterns: Sequence[RegexPattern],
		*,
		no_filter: Optional[bool] = None,
		no_reverse: Optional[bool] = None,
	) -> None:
		"""
		Initialize the :class:`Re2PsBackend` instance.

		*patterns* (:class:`Sequence` of :class:`.RegexPattern`) contains the
		compiled patterns.

		*no_filter* (:class:`bool`) is whether to keep no-op patterns (:data:`True`),
		or remove them (:data:`False`).

		*no_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""
		if re2_error is not None:
			raise re2_error

		patterns = self.__recompile_patterns(patterns)
		super().__init__(patterns, no_filter=no_filter, no_reverse=no_reverse)

	@staticmethod
	def __recompile_patterns(
		in_patterns: Sequence[RegexPattern],
	) -> Sequence[RegexPattern]:
		"""
		Recompile the patterns using :module:`re2`.
		"""
		# Since re2 is a drop-in replacement for the re, recompilation is all that
		# needs to be done.
		out_patterns = []
		for pattern in in_patterns:
			if pattern.regex is not None:
				re2_regex = re2.compile(pattern.regex.pattern)
				pattern = copy(pattern)
				pattern.regex = cast(re.Pattern, re2_regex)

			out_patterns.append(pattern)

		return out_patterns
