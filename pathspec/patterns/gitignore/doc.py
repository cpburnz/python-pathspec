"""
This module implements Git's `gitignore`_ patterns exactly as documented. This
differs from how Git actually behaves when including files in excluded
directories.

.. _`gitignore`: https://git-scm.com/docs/gitignore
"""

from typing import (
	AnyStr,
	Optional)  # Replaced by `X | None` in 3.10.

from pathspec import (
	util)
from pathspec._typing import (
	override)

from .base import (
	_BYTES_ENCODING,
	_GitIgnoreBasePattern)


class GitIgnoreDocPattern(_GitIgnoreBasePattern):
	"""
	The :class:`GitIgnoreDocPattern` class represents a compiled gitignore
	pattern exactly as documented.
	"""

	# Keep the dict-less class hierarchy.
	__slots__ = ()

	@override
	@classmethod
	def pattern_to_regex(
		cls,
		pattern: AnyStr,
	) -> tuple[Optional[AnyStr], Optional[bool]]:
		"""
		Convert the pattern into a regular expression.

		*pattern* (:class:`str` or :class:`bytes`) is the pattern to convert into a
		regular expression.

		Returns the uncompiled regular expression (:class:`str`, :class:`bytes`, or
		:data:`None`); and whether matched files should be included (:data:`True`),
		excluded (:data:`False`), or if it is a null-operation (:data:`None`).
		"""
		if isinstance(pattern, str):
			return_type = str
		elif isinstance(pattern, bytes):
			return_type = bytes
			pattern = pattern.decode(_BYTES_ENCODING)
		else:
			raise TypeError(f"pattern:{pattern!r} is not a unicode or byte string.")

		# TODO

		if regex is not None and return_type is bytes:
			regex = regex.encode(_BYTES_ENCODING)

		return (regex, include)


util.register_pattern('gitignore-doc', GitIgnoreDocPattern)
