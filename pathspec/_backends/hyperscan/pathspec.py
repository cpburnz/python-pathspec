"""
This module provides the :module:`hyperscan` backend for :class:`~pathspec.pathspec.PathSpec`.

WARNING: The *pathspec._backends.hyperscan* package is not part of the public
API. Its contents and structure are likely to change.
"""
from __future__ import annotations

import itertools
from collections.abc import (
	Sequence)
from typing import (
	Any,
	ClassVar,
	Optional)  # Replaced by `X | None` in 3.10.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from ...pattern import (
	RegexPattern)
from ..._typing import (
	override)  # Added in 3.12.

from ..base import (
	Backend)
from .._utils import (
	enumerate_patterns)

from .base import (
	hyperscan_error)
from ._base import (
	HyperscanExprDat,
	HyperscanExprDebug)


class HyperscanPsBackend(Backend):
	"""
	The :class:`HyperscanPsBackend` class is the :module:`hyperscan`
	implementation used by :class:`~pathspec.pathspec.PathSpec` for matching
	files. The Hyperscan database uses block mode for matching files.
	"""

	_reverse_patterns: ClassVar[bool] = False
	"""
	*_reverse_patterns* (:class:`bool`) is whether the patterns are reversed.
	"""

	def __init__(
		self,
		patterns: Sequence[RegexPattern],
		*,
		_debug_exprs: Optional[bool] = None,
	) -> None:
		"""
		Initialize the :class:`HyperscanPsBackend` instance.

		*patterns* (:class:`Sequence` of :class:`.Pattern`) contains the compiled
		patterns.
		"""
		if hyperscan is None:
			raise hyperscan_error

		if not patterns:
			raise ValueError(f"{patterns=!r} cannot be empty.")
		elif not isinstance(patterns[0], RegexPattern):
			raise TypeError(f"{patterns[0]=!r} must be a RegexPattern.")

		use_patterns = enumerate_patterns(
			patterns, filter=True, reverse=self._reverse_patterns,
		)

		self._db = self._make_db()
		"""
		*_db* (:class:`hyperscan.Database`) is the Hyperscan database.
		"""

		self._debug_exprs = bool(_debug_exprs)
		"""
		*_debug_exprs* (:class:`bool`) is whether to include additional debugging
		information for the expressions.
		"""

		self._expr_data: list[HyperscanExprDat] = self._init_db(
			db=self._db, debug=self._debug_exprs, patterns=use_patterns,
		)
		"""
		*_expr_data* (:class:`list`) maps expression index (:class:`int`) to
		expression data (:class:`:class:`HyperscanExprDat`).
		"""

		self._out: tuple[Optional[bool], Optional[int]] = (None, None)
		"""
		*_out* (:class:`tuple`) stores the current match.
		"""

		self._patterns: dict[int, RegexPattern] = dict(use_patterns)
		"""
		*_patterns* (:class:`dict`) maps pattern index (:class:`int`) to pattern
		(:class:`RegexPattern`).
		"""

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		debug: bool,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[HyperscanExprDat]:
		"""
		Initialize the Hyperscan database from the given patterns.

		*db* (:class:`hyperscan.Hyperscan`) is the Hyperscan database.

		*debug* (:class:`bool`) is whether to include additional debugging
		information for the expressions.

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

			if debug:
				expr_data.append(HyperscanExprDebug(
					include=pattern.include,
					index=pattern_index,
					is_dir_pattern=False,
					regex=regex,
				))
			else:
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

	@override
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
		Create the Hyperscan database.

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
