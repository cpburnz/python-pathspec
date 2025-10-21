"""
This module defines matchers which are used by :class:`~pathspec.PathSpec` to
actually match files against patterns.
"""
from __future__ import annotations

import itertools
from collections.abc import (
	Iterable)
from typing import (
	Any,
	ClassVar,
	Literal,
	NamedTuple,
	Optional,  # Replaced by `X | None` in 3.10.
	TypeVar)

try:
	import hyperscan
	hyperscan_error: Optional[ModuleNotFoundError] = None
except ModuleNotFoundError as e:
	hyperscan = None
	hyperscan_error = e

from .pattern import (
	Pattern,
	RegexPattern)
from .util import (
	check_match_file)

_OPTIMIZE_LIB: Optional[Literal['hyperscan']] = None
"""
*_OPTIMIZE_LIB* (:class:`str` or :data:`None`) is best library available to use
to optimize regular expressions.
"""

if hyperscan is not None:
	_OPTIMIZE_LIB = 'hyperscan'

TPattern = TypeVar("TPattern", bound=Pattern)


class Matcher(object):
	"""
	The :class:`Matcher` class is the abstract class defining how to match files
	against patterns.
	"""

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		raise NotImplementedError()


class DefaultMatcher(Matcher):
	"""
	The :class:`DefaultMatcher` class is the default implementation used by
	:class:`~pathspec.PathSpec` for matching files.
	"""

	def __init__(
		self,
		patterns: Iterable[Pattern],
		*,
		no_filter: Optional[bool] = None,
		no_reverse: Optional[bool] = None,
	) -> None:
		"""
		Initialize the :class:`DefaultMatcher` instance.

		*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the compiled
		patterns.

		*no_filter* (:class:`bool`) is whether to keep null patterns (:data:`True`),
		or remove them (:data:`False`).

		*no_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""
		self._is_reversed = not no_reverse
		self._patterns = _enumerate_patterns(
			patterns, filter=not no_filter, reverse=not no_reverse,
		)

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		return check_match_file(self._patterns, file, self._is_reversed)


class HyperscanMatcher(Matcher):
	"""
	The :class:`HyperscanMatcher` class uses a hyperscan database in block mode
	for matching files.
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

		*_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""
		if hyperscan is None:
			raise hyperscan_error

		use_patterns = _enumerate_patterns(
			patterns, filter=True, reverse=self._reverse_patterns,
		)

		self._db = self._new_db()
		self._expr_data = self._init_db(self._db, use_patterns)
		self._out: tuple[Optional[bool], Optional[int]] = (None, None)
		self._patterns = dict(use_patterns)

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[_HyperscanExprDat]:
		"""
		WARNING: This method is an implementation detail and not part of the public
		API.

		Initialize the hyperscan database from the given patterns.

		*db* (:class:`hyperscan.Hyperscan`) is the Hyperscan database.

		*patterns* (:class:`~collections.abc.Sequence` of :class:`.RegexPattern`)
		contains the patterns.

		Returns a :class:`list` indexed by expression id (:class:`int`) to its data
		(:class:`_HyperscanExprDat`).
		"""
		# Prepare patterns.
		expr_data: list[_HyperscanExprDat] = []
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

			expr_data.append(_HyperscanExprDat(
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
		# NOTICE: According to benchmarking, a method callback is 22% faster than
		# using a closure here.
		self._out = (None, None)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self._out

	@staticmethod
	def _new_db() -> hyperscan.Database:
		"""
		WARNING: This method is an implementation detail and not part of the public
		API.

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
		if include := expr_dat.include:
			# Store match.
			self._out = (include, expr_dat.index)


def _enumerate_patterns(
	patterns: Iterable[TPattern],
	filter: bool,
	reverse: bool,
) -> list[tuple[int, TPattern]]:
	"""
	Enumerate the patterns.

	*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the patterns.

	*filter* (:class:`bool`) is whether to remove null patterns (:data:`True`),
	or keep them (:data:`False`).

	*reverse* (:class:`bool`) is whether to reverse the pattern order
	(:data:`True`), or keep the order (:data:`True`).

	Returns the enumerated patterns (:class:`list` of :class:`tuple`).
	"""
	out_patterns = [
		(__i, __pat)
		for __i, __pat in enumerate(patterns)
		if not filter or __pat.include is not None
	]
	if reverse:
		out_patterns.reverse()

	return out_patterns


class _HyperscanExprDat(NamedTuple):
	include: bool
	index: int
	is_dir_pattern: bool
