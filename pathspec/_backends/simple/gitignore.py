"""
This module provides the simple backend for :class:`~pathspec.gitignore.GitIgnoreSpec`.

WARNING: The *pathspec._backends.simple* package is not part of the public API.
Its contents and structure are likely to change.
"""

from collections.abc import (
	Sequence)
from typing import (
	Optional)  # Replaced by `X | None` in 3.10.

from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitignore.spec import (
	_DIR_MARK)
from pathspec._typing import (
	override)  # Added in 3.12.

from .pathspec import (
	SimplePsBackend)


class SimpleGiBackend(SimplePsBackend):
	"""
	The :class:`SimpleGiBackend` class is the default (or simple) implementation
	used by :class:`~pathspec.gitignore.GitIgnoreSpec` for matching files.
	"""

	# Change type hint.
	_patterns: list[tuple[int, RegexPattern]]  # type: ignore[assignment]

	def __init__(
		self,
		patterns: Sequence[RegexPattern],
		*,
		no_filter: Optional[bool] = None,
		no_reverse: Optional[bool] = None,
	) -> None:
		"""
		Initialize the :class:`SimpleGiBackend` instance.

		*patterns* (:class:`Sequence` of :class:`.RegexPattern`) contains the
		compiled patterns.

		*no_filter* (:class:`bool`) is whether to keep no-op patterns (:data:`True`),
		or remove them (:data:`False`).

		*no_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""
		super().__init__(patterns, no_filter=no_filter, no_reverse=no_reverse)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		is_reversed = self._is_reversed

		# Resolve the ancestor directory and the file separately: a file negation
		# only applies while no ancestor directory is excluded.
		dir_include: Optional[bool] = None
		dir_index: Optional[int] = None
		file_include: Optional[bool] = None
		file_index: Optional[int] = None

		for index, pattern in self._patterns:
			if (
				(include := pattern.include) is not None
				and (match := pattern.match_file(file)) is not None
			):
				# Pattern matched.
				if match.match.groupdict().get(_DIR_MARK):
					# Pattern matched by a directory pattern.
					if dir_include is None or not is_reversed:
						dir_include = include
						dir_index = index
				elif file_include is None or not is_reversed:
					# Pattern matched by a file pattern.
					file_include = include
					file_index = index

		if dir_include:
			return (dir_include, dir_index)
		elif file_include is not None:
			return (file_include, file_index)
		else:
			return (dir_include, dir_index)
