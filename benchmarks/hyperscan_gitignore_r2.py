"""
This module defines the hyperscan backends for `.GitIgnoreSpec`, revision 2,
used in benchmarking, but not included in the released library.
"""
from __future__ import annotations

from collections.abc import (
	Sequence)
from typing import (
	Any,
	Callable,  # Replaced by `collections.abc.Callable` in 3.9.2.
	Optional,  # Replaced by `X | None` in 3.10.
	Union)  # Replaced by `X | Y` in 3.10.
from typing_extensions import (
	override)  # Added in 3.12.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from pathspec._backends.hyperscan._base import (
	HS_FLAGS,
	HyperscanExprDat)
from pathspec._backends.hyperscan.gitignore import (
	_DIR_MARK_CG,
	_DIR_MARK_OPT)
from pathspec._backends.hyperscan.pathspec import (
	HyperscanPsBackend)
from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern,
	_BYTES_ENCODING)


class _HyperscanGiR2BaseBackend(HyperscanPsBackend):
	"""
	The :class:`_HyperscanGiR2BaseBackend` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@override
	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		debug: bool,
		patterns: list[tuple[int, RegexPattern]],
		sort_ids: Optional[Callable[[list[int]], None]],
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

			use_regexes: list[tuple[Union[str, bytes], bool]] = []
			if isinstance(pattern, GitIgnoreSpecPattern):
				# GitWildMatch uses capture groups for its directory marker but
				# Hyperscan does not support capture groups. Check for this scenario.
				if isinstance(regex, str):
					regex_str = regex
				else:
					assert isinstance(regex, bytes), regex
					regex_str = regex.decode(_BYTES_ENCODING)

				if _DIR_MARK_CG in regex_str:
					# Found directory marker.
					if regex_str.endswith(_DIR_MARK_OPT):
						# Regex has optional directory marker. Split regex into directory
						# and file variants.
						base_regex = regex_str[:-len(_DIR_MARK_OPT)]
						use_regexes.append((f'{base_regex}/', True))
						use_regexes.append((f'{base_regex}$', False))
					else:
						# Remove capture group.
						base_regex = regex_str.replace(_DIR_MARK_CG, '/')
						use_regexes.append((base_regex, True))

			if not use_regexes:
				# No special case for regex.
				use_regexes.append((regex, False))

			for regex, is_dir_pattern in use_regexes:
				if isinstance(regex, bytes):
					regex_bytes = regex
				else:
					assert isinstance(regex, str), regex
					regex_bytes = regex.encode('utf8')

				expr_data.append(HyperscanExprDat(
					include=pattern.include,
					index=pattern_index,
					is_dir_pattern=is_dir_pattern,
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


class _HyperscanGiR2BlockBaseBackend(_HyperscanGiR2BaseBackend):
	"""
	The :class:`_HyperscanGiR2BlockBaseBackend` base class uses a hyperscan
	database in block mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class HyperscanGiR2BlockClosureBackend(_HyperscanGiR2BlockBaseBackend):
	"""
	The :class:`HyperscanGiR2BlockClosureBackend` class uses a hyperscan database
	in block mode for matching files, and uses a closure to capture state.
	"""

	# Prevent accidental usage.
	_out: tuple[()]

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = -1
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]

			is_dir_pattern = expr_dat.is_dir_pattern
			if is_dir_pattern:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			# WARNING: Hyperscan does not guarantee matches will be produced in
			# order!
			include = expr_dat.include
			index = expr_dat.index
			if (
				(include and is_dir_pattern and index > out_index)
				or (priority == out_priority and index > out_index)
				or priority > out_priority
			):
				out_include = include
				out_index = index
				out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)

		if out_index == -1:
			out_index = None

		return (out_include, out_index)


class HyperscanGiR2BlockStateBackend(_HyperscanGiR2BlockBaseBackend):
	"""
	The :class:`HyperscanGiR2BlockStateBackend` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	# Change type hint.
	_out: tuple[Optional[bool], int, int]

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self._out = (None, -1, 0)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self._out = (None, -1, 0)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)

		out_include, out_index = self._out[:2]
		if out_index == -1:
			out_index = None

		return (out_include, out_index)

	@override
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		expr_dat = self._expr_data[expr_id]

		is_dir_pattern = expr_dat.is_dir_pattern
		if is_dir_pattern:
			# Pattern matched by a directory pattern.
			priority = 1
		else:
			# Pattern matched by a file pattern.
			priority = 2

		# WARNING: Hyperscan does not guarantee matches will be produced in order!
		include = expr_dat.include
		index = expr_dat.index
		prev_index = self._out[1]
		prev_priority = self._out[2]
		if (
			(include and is_dir_pattern and index > prev_index)
			or (priority == prev_priority and index > prev_index)
			or priority > prev_priority
		):
			self._out = (include, index, priority)


class _HyperscanGiR2StreamBaseBackend(_HyperscanGiR2BaseBackend):
	"""
	The :class:`_HyperscanGiR2StreamBaseBackend` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanGiR2StreamClosureBackend(_HyperscanGiR2StreamBaseBackend):
	"""
	The :class:`HyperscanGiR2StreamClosureBackend` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	# Prevent accidental usage.
	_out: tuple[()]

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = -1
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]

			is_dir_pattern = expr_dat.is_dir_pattern
			if is_dir_pattern:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			# WARNING: Hyperscan does not guarantee matches will be produced in
			# order!
			include = expr_dat.include
			index = expr_dat.index
			if (
				(include and is_dir_pattern and index > out_index)
				or (priority == out_priority and index > out_index)
				or priority > out_priority
			):
				out_include = include
				out_index = index
				out_priority = priority

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		if out_index == -1:
			out_index = None

		return (out_include, out_index)
