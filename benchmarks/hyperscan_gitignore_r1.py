"""
This module defines the hyperscan backends for `.GitIgnoreSpec`, revision 1,
used in benchmarking, but not included in the released library.
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

from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitignore.spec import (
	_DIR_MARK)

from benchmarks.hyperscan_pathspec_r1 import (
	HyperscanPsR1BaseBackend)


class _HyperscanGiR1BaseBackend(HyperscanPsR1BaseBackend):
	"""
	The :class:`_HyperscanGiR1BaseBackend` base class uses a hyperscan database in
	block mode for matching files.
	"""


class _HyperscanGiR1BlockBaseBackend(_HyperscanGiR1BaseBackend):
	"""
	The :class:`_HyperscanGiR1BlockBaseBackend` base class uses a hyperscan
	database in block mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class HyperscanGiR1BlockClosureBackend(_HyperscanGiR1BlockBaseBackend):
	"""
	The :class:`HyperscanGiR1BlockClosureBackend` class uses a hyperscan database
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
			index = expr_dat.index

			# Rematch pattern because Hyperscan does not support capture groups.
			pattern = self._patterns[index]
			match = pattern.match_file(file)

			# Check for directory marker.
			dir_mark = match.match.groupdict().get(_DIR_MARK)

			if dir_mark:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			# WARNING: Hyperscan does not guarantee matches will be produced in order!
			include = expr_dat.include
			if (
				(include and dir_mark and index > out_index)
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


class HyperscanGiR1BlockStateBackend(_HyperscanGiR1BlockBaseBackend):
	"""
	The :class:`HyperscanGiR1BlockStateBackend` class uses a hyperscan database in
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
		self._db.scan(
			file.encode('utf8'), match_event_handler=self.__on_match, context=file,
		)

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
		context: Any,
	) -> Optional[bool]:
		file: str = context
		expr_dat = self._expr_data[expr_id]
		index = expr_dat.index

		# Rematch pattern because Hyperscan does not support capture groups.
		pattern = self._patterns[index]
		match = pattern.match_file(file)

		# Check for directory marker.
		dir_mark = match.match.groupdict().get(_DIR_MARK)

		if dir_mark:
			# Pattern matched by a directory pattern.
			priority = 1
		else:
			# Pattern matched by a file pattern.
			priority = 2

		# WARNING: Hyperscan does not guarantee matches will be produced in order!
		include = expr_dat.include
		prev_index = self._out[1]
		prev_priority = self._out[2]
		if (
			(include and dir_mark and index > prev_index)
			or (priority == prev_priority and index > prev_index)
			or priority > prev_priority
		):
			self._out = (include, index, priority)


class _HyperscanGiR1StreamBaseBackend(_HyperscanGiR1BaseBackend):
	"""
	The :class:`_HyperscanGiR1StreamBaseBackend` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanGiR1StreamClosureBackend(_HyperscanGiR1StreamBaseBackend):
	"""
	The :class:`HyperscanGiR1StreamClosureBackend` class uses a hyperscan database
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
			index = expr_dat.index

			# Rematch pattern because Hyperscan does not support capture groups.
			pattern = self._patterns[index]
			match = pattern.match_file(file)

			# Check for directory marker.
			dir_mark = match.match.groupdict().get(_DIR_MARK)

			if dir_mark:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			# WARNING: Hyperscan does not guarantee matches will be produced in order!
			include = expr_dat.include
			if (
				(include and dir_mark and index > out_index)
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


# WARNING: This segfaults.
class HyperscanGiR1StreamStateBackend(_HyperscanGiR1StreamBaseBackend):
	"""
	The :class:`HyperscanGiR1StreamStateBackend` class uses a hyperscan database
	in streaming mode for matching files, and stores state in variables.
	"""

	# Change type hint.
	_out: tuple[Optional[bool], int, int]

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self._out = (None, -1, 0)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self._out = (None, -1, 0)
		with self._db.stream(match_event_handler=self.__on_match, context=file) as stream:
			stream.scan(file.encode('utf8'))

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
		context: Any,
	) -> Optional[bool]:
		file: str = context
		expr_dat = self._expr_data[expr_id]
		index = expr_dat.index

		# Rematch pattern because Hyperscan does not support capture groups.
		pattern = self._patterns[index]
		match = pattern.match_file(file)

		# Check for directory marker.
		dir_mark = match.match.groupdict().get(_DIR_MARK)

		if dir_mark:
			# Pattern matched by a directory pattern.
			priority = 1
		else:
			# Pattern matched by a file pattern.
			priority = 2

		# WARNING: Hyperscan does not guarantee matches will be produced in order!
		include = expr_dat.include
		prev_index = self._out[1]
		prev_priority = self._out[2]
		if (
			(include and dir_mark and index > prev_index)
			or (priority == prev_priority and index > prev_index)
			or priority > prev_priority
		):
			self._out = (include, index, priority)
