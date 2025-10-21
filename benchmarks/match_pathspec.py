"""
This module defines general pathspec matchers used in benchmarking, but not
included in the released library.
"""
from __future__ import annotations

import itertools
from collections.abc import (
	Iterable)
from typing import (
	Any,
	Optional)  # Replaced by `X | None` in 3.10.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

# TODO: Look into re2 <https://pypi.org/project/google-re2>.

from pathspec.match import (
	HyperscanMatcher,
	_HyperscanExprDat)
from pathspec.pattern import (
	RegexPattern)


class HyperscanR1BaseMatcher(HyperscanMatcher):
	"""
	The :class:`HyperscanR1BaseMatcher` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[_HyperscanExprDat]:
		# NOTICE: This is the current implementation.

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

	@staticmethod
	def _new_db() -> hyperscan.Database:
		raise NotImplementedError()


class _HyperscanR1BlockBaseMatcher(HyperscanR1BaseMatcher):
	"""
	The :class:`_HyperscanR1BlockBaseMatcher` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class HyperscanR1BlockClosureMatcher(_HyperscanR1BlockBaseMatcher):
	"""
	The :class:`HyperscanR1BlockClosureMatcher` class uses a hyperscan database in
	block mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = None

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index
			expr_dat = self._expr_data[expr_id]
			if include := expr_dat.include:
				out_include = include
				out_index = expr_dat.index

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class HyperscanR1BlockStateMatcher(_HyperscanR1BlockBaseMatcher):
	"""
	The :class:`HyperscanR1BlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: tuple[Optional[bool], Optional[int]] = (None, None)

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self.__out

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		expr_dat = self._expr_data[expr_id]
		include = expr_dat.include
		if include:
			self.__out = (include, expr_dat.index)


class _HyperscanR1StreamBaseMatcher(HyperscanR1BaseMatcher):
	"""
	The :class:`_HyperscanR1StreamBaseMatcher` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanR1StreamClosureMatcher(_HyperscanR1StreamBaseMatcher):
	"""
	The :class:`HyperscanR1StreamClosureMatcher` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = None

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index
			expr_dat = self._expr_data[expr_id]
			if include := expr_dat.include:
				out_include = include
				out_index = expr_dat.index
				return True

			return None

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index


# WARNING: This segfaults.
class HyperscanR1StreamStateMatcher(_HyperscanR1StreamBaseMatcher):
	"""
	The :class:`HyperscanR1StreamStateMatcher` class uses a hyperscan database in
	streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: tuple[Optional[bool], Optional[int]] = (None, None)

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None)

		with self._db.stream(match_event_handler=self.__on_match) as stream:
			stream.scan(file.encode('utf8'))

		return self.__out

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		expr_dat = self._expr_data[expr_id]
		if include := expr_dat.include:
			self.__out = (include, expr_dat.index)
			return True
		else:
			return None
