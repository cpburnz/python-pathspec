"""
This module defines general pathspec matchers used in benchmarking, but not
included in the released library.
"""
from __future__ import annotations

from collections.abc import (
	Sequence)
from typing import (
	Any,
	Optional)  # Replaced by `X | None` in 3.10.
from typing_extensions import (
	override)  # Added in 3.12.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from pathspec._backends.hyperscan._base import (
	HS_FLAGS,
	HyperscanExprDat)
from pathspec._backends.hyperscan.pathspec import (
	HyperscanPsBackend)
from pathspec.pattern import (
	RegexPattern)


class HyperscanPsR1BaseBackend(HyperscanPsBackend):
	"""
	The :class:`HyperscanPsR1BaseBackend` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@override
	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		debug: bool,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[HyperscanExprDat]:
		# NOTICE: This is the current implementation.

		# Prepare patterns.
		expr_data: list[HyperscanExprDat] = []
		exprs: list[bytes] = []
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

		# Compile patterns.
		db.compile(
			expressions=exprs,
			ids=list(range(len(exprs))),
			elements=len(exprs),
			flags=HS_FLAGS,
		)
		return expr_data

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		raise NotImplementedError()


class _HyperscanPsR1BlockBaseBackend(HyperscanPsR1BaseBackend):
	"""
	The :class:`_HyperscanPsR1BlockBaseBackend` base class uses a hyperscan
	database in block mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class HyperscanPsR1BlockClosureBackend(_HyperscanPsR1BlockBaseBackend):
	"""
	The :class:`HyperscanPsR1BlockClosureBackend` class uses a hyperscan database
	in block mode for matching files, and uses a closure to capture state.
	"""

	# Prevent accidental usage.
	_out: tuple[()]

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = None

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			# WARNING: Hyperscan does not guarantee matches will be produced in order!
			nonlocal out_include, out_index
			expr_dat = self._expr_data[expr_id]
			index = expr_dat.index
			if index > out_index:
				out_include = expr_dat.include
				out_index = index

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class HyperscanPsR1BlockStateBackend(_HyperscanPsR1BlockBaseBackend):
	"""
	The :class:`HyperscanPsR1BlockStateBackend` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self._out = (None, -1)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self._out = (None, -1)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)

		out_include, out_index = self._out
		if out_index == -1:
			out_index = None

		return out_include, out_index

	@override
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		# WARNING: Hyperscan does not guarantee matches will be produced in order!
		expr_dat = self._expr_data[expr_id]
		index = expr_dat.index
		prev_index = self._out[1]
		if index > prev_index:
			self._out = (expr_dat.include, index)


class _HyperscanPsR1StreamBaseBackend(HyperscanPsR1BaseBackend):
	"""
	The :class:`_HyperscanPsR1StreamBaseBackend` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanPsR1StreamClosureBackend(_HyperscanPsR1StreamBaseBackend):
	"""
	The :class:`HyperscanPsR1StreamClosureBackend` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = -1

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			# WARNING: Hyperscan does not guarantee matches will be produced in order!
			nonlocal out_include, out_index
			expr_dat = self._expr_data[expr_id]
			index = expr_dat.index
			if index > out_index:
				out_include = expr_dat.include
				out_index = index

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		if out_index == -1:
			out_index = None

		return out_include, out_index


# WARNING: This segfaults.
class HyperscanPsR1StreamStateBackend(_HyperscanPsR1StreamBaseBackend):
	"""
	The :class:`HyperscanPsR1StreamStateBackend` class uses a hyperscan database
	in streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self._out = (None, -1)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self._out = (None, -1)

		with self._db.stream(match_event_handler=self.__on_match) as stream:
			stream.scan(file.encode('utf8'))

		out_include, out_index = self._out
		if out_index == -1:
			out_index = None

		return out_include, out_index

	@override
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		# WARNING: Hyperscan does not guarantee matches will be produced in order!
		expr_dat = self._expr_data[expr_id]
		index = expr_dat.index
		prev_index = self._out[1]
		if index > prev_index:
			self._out = (expr_dat.include, index)
