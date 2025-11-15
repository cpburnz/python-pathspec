"""
This module defines gitignore matchers used in benchmarking, but not included in
the released library.
"""
from __future__ import annotations

import itertools
from collections.abc import (
	Sequence)
from typing import (
	Any,
	Optional,  # Replaced by `X | None` in 3.10.
	Union)  # Replaced by `X | Y` in 3.10.
from typing_extensions import (
	override)  # Added in 3.12.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

# TODO: Look into re2 <https://pypi.org/project/google-re2>.

from pathspec._backends.hyperscan._base import (
	HyperscanExprDat)
from pathspec._backends.hyperscan.gitignore import (
	_DIR_MARK_CG,
	_DIR_MARK_OPT)
from pathspec._backends.hyperscan.pathspec import (
	HyperscanPsBackend)
from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitwildmatch import (
	GitWildMatchPattern,
	_BYTES_ENCODING,
	_DIR_MARK)

from benchmarks.match_pathspec import (
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

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]
			if (include := expr_dat.include) is not None:
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

				if (include and dir_mark) or priority >= out_priority:
					out_include = include
					out_index = index
					out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class HyperscanGiR1BlockStateBackend(_HyperscanGiR1BlockBaseBackend):
	"""
	The :class:`HyperscanGiR1BlockStateBackend` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		self._db.scan(
			file.encode('utf8'), match_event_handler=self.__on_match, context=file,
		)
		return self.__out[:2]

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
		if (include := expr_dat.include) is not None:
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

			if (include and dir_mark) or priority >= self.__out[2]:
				self.__out = (include, index, priority)


class _HyperscanGiR1StreamBaseBackend(_HyperscanGiR1BaseBackend):
	"""
	The :class:`_HyperscanGiR1StreamBaseBackend` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	_reverse_patterns = True

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanGiR1StreamClosureBackend(_HyperscanGiR1StreamBaseBackend):
	"""
	The :class:`HyperscanGiR1StreamClosureBackend` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			# NOTICE: Patterns are being checked in reverse order.
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]
			if (include := expr_dat.include) is not None:
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

				if priority > out_priority:
					out_include = include
					out_index = index
					out_priority = priority

				if priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					return True

			return None

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index


# WARNING: This segfaults.
class HyperscanGiR1StreamStateBackend(_HyperscanGiR1StreamBaseBackend):
	"""
	The :class:`HyperscanGiR1StreamStateBackend` class uses a hyperscan database
	in streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		with self._db.stream(match_event_handler=self.__on_match, context=file) as stream:
			stream.scan(file.encode('utf8'))

		return self.__out[:2]

	@override
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
	) -> Optional[bool]:
		# NOTICE: Patterns are being checked in reverse order.
		file: str = context
		expr_dat = self._expr_data[expr_id]
		if (include := expr_dat.include) is not None:
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

			if priority > self.__out[2]:
				self.__out = (include, index, priority)

			if priority == 2:
				# Patterns are being checked in reverse order. The first pattern that
				# matches with the highest priority takes precedence.
				return True

		return None


class _HyperscanGiR2BaseBackend(HyperscanPsBackend):
	"""
	The :class:`_HyperscanGiR2BaseBackend` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@override
	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[HyperscanExprDat]:
		# NOTICE: This is the current implementation.

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

			use_regexes: list[tuple[Union[str, bytes], bool]] = []
			if isinstance(pattern, GitWildMatchPattern):
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
						use_regexes.append((f'{base_regex}/.*$', True))
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

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]
			if (include := expr_dat.include) is not None:
				is_dir_pattern = expr_dat.is_dir_pattern
				if is_dir_pattern:
					# Pattern matched by a directory pattern.
					priority = 1
				else:
					# Pattern matched by a file pattern.
					priority = 2

				if (include and is_dir_pattern) or priority >= out_priority:
					out_include = include
					out_index = expr_dat.index
					out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class HyperscanGiR2BlockStateBackend(_HyperscanGiR2BlockBaseBackend):
	"""
	The :class:`HyperscanGiR2BlockStateBackend` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Sequence[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self.__out[:2]

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
		if (include := expr_dat.include) is not None:
			is_dir_pattern = expr_dat.is_dir_pattern
			if is_dir_pattern:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			if (include and is_dir_pattern) or priority >= self.__out[2]:
				self.__out = (include, expr_dat.index, priority)


class _HyperscanGiR2StreamBaseBackend(_HyperscanGiR2BaseBackend):
	"""
	The :class:`_HyperscanGiR2StreamBaseBackend` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	_reverse_patterns = True

	@override
	@staticmethod
	def _make_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class HyperscanGiR2StreamClosureBackend(_HyperscanGiR2StreamBaseBackend):
	"""
	The :class:`HyperscanGiR2StreamClosureBackend` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	@override
	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			# NOTICE: Patterns are being checked in reverse order.
			nonlocal out_include, out_index, out_priority
			expr_dat = self._expr_data[expr_id]
			if (include := expr_dat.include) is not None:
				is_dir_pattern = expr_dat.is_dir_pattern
				if is_dir_pattern:
					# Pattern matched by a directory pattern.
					priority = 1
				else:
					# Pattern matched by a file pattern.
					priority = 2

				if priority > out_priority:
					out_include = include
					out_index = expr_dat.index
					out_priority = priority

				if priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					return True

			return None

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index
