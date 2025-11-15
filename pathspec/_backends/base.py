"""
This module defines base classes for implementing pattern (or regex) matching
backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

from typing import (
	Literal,
	Optional)

BackendNamesHint = Literal['best', 'hyperscan', 'simple']


class Backend(object):
	"""
	The :class:`Backend` class is the abstract base class defining how to match
	files against patterns.
	"""

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		raise NotImplementedError((
			f"{self.__class__.__module__}.{self.__class__.__qualname__}.match_file() "
			f"must be implemented."
		))  # NotImplementedError
