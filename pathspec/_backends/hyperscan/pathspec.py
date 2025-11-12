"""
This module provides the :module:`hyperscan` backend for :class:`~pathspec.pathspec.PathSpec`.

WARNING: The *pathspec._backends.hyperscan* package is not part of the public
API. Its contents and structure are likely to change.
"""
from __future__ import annotations

import itertools
from collections.abc import (
	Iterable)
from typing import (
	Any,
	ClassVar,
	NamedTuple,
	Optional)  # Replaced by `X | None` in 3.10.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from ...pattern import (
	RegexPattern)

from ..base import (
	Backend)
from .._utils import (
	enumerate_patterns)

from .base import (
	hyperscan_error)


class HyperscanPsBackend(Backend):
	"""
	The :class:`HyperscanPsBackend` class is the :module:`hyperscan`
	implementation used by :class:`~pathspec.pathspec.PathSpec` for matching
	files.
	"""

	_reverse_patterns: ClassVar[bool] = False

	def __init__(
		self,
		patterns: Iterable[RegexPattern],
	) -> None:
		"""
		Initialize the :class:`HyperscanMatcher` instance.

		*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the compiled
		patterns.
		"""
		if hyperscan is None:
			raise hyperscan_error

		use_patterns = enumerate_patterns(
			patterns, filter=True, reverse=self._reverse_patterns,
		)

		self._db = self._make_db()
		self._expr_data = self._init_db(self._db, use_patterns)
		self._out: tuple[Optional[bool], Optional[int]] = (None, None)
		self._patterns = dict(use_patterns)

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[HyperscanExprDat]:
		"""
		Initialize the hyperscan database from the given patterns.

		*db* (:class:`hyperscan.Hyperscan`) is the Hyperscan database.

		*patterns* (:class:`~collections.abc.Sequence` of :class:`.RegexPattern`)
		contains the patterns.

		Returns a :class:`list` indexed by expression id (:class:`int`) to its data
		(:class:`HyperscanExprDat`).
		"""
		# Prepare patterns.
		expr_data: list[HyperscanExprDat] = []
		exprs: list[bytes] = []
		id_counter = itertools.count(0)
		ids: list[int] = []
		for pattern_index, pattern in patterns:
			if pattern.include is None:
				continue

			# Encode regex.
			assert isinstance(pattern, RegexPattern), pattern
			regex = pattern.regex.pattern

			if isinstance(regex, bytes):
				regex_bytes = regex
			else:
				assert isinstance(regex, str), regex
				regex_bytes = regex.encode('utf8')

			expr_data.append(HyperscanExprDat(
				include=pattern.include,
				index=pattern_index,
				is_dir_pattern=False,
			))
			exprs.append(regex_bytes)
			ids.append(next(id_counter))

		# Compile patterns.
		db.compile(
			expressions=exprs,
			ids=ids,
			elements=len(exprs),
			flags=hyperscan.HS_FLAG_UTF8,
		)
		return expr_data

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		# NOTICE: According to benchmarking, a method callback is 20% faster than
		# using a closure here.
		self._out = (None, None)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self._out

	@staticmethod
	def _make_db() -> hyperscan.Database:
		"""
		Create the hyperscan database.

		Returns the database (:class:`hyperscan.Database`).
		"""
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		"""
		Called on each match.

		*expr_id* (:class:`int`) is the expression id (index) of the matched
		pattern.
		"""
		expr_dat = self._expr_data[expr_id]

		# Store match.
		self._out = (expr_dat.include, expr_dat.index)


class HyperscanExprDat(NamedTuple):
	"""
	The :class:`HyperscanExprDat` class is used to store data related to an
	expression.
	"""

	include: bool
	"""
	*include* (:class:`bool`) is whether is whether the matched files should be
	included (:data:`True`), or excluded (:data:`False`).
	"""

	index: int
	"""
	*index* (:class:`int`) is the pattern index.
	"""

	is_dir_pattern: bool
	"""
	*is_dir_pattern* (:class:`bool`) is whether the pattern is a directory
	pattern for gitignore.
	"""
