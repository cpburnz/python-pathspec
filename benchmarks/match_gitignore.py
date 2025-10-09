"""
This module defines gitignore matchers used in benchmarking, but not included in
the released library.
"""
from __future__ import annotations

import itertools
from typing import (
	Any,
	Iterable,  # Replaced by `collections.abc.Iterable` in 3.9.
	List,  # Replaced by `list` in 3.9.
	Optional,  # Replaced by `X | None` in 3.10.
	Tuple,  # Replaced by `tuple` in 3.9.
	Union)  # Replaced by `X | Y` in 3.10.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

# TODO: Look into re2 <https://pypi.org/project/google-re2>.

from pathspec.gitignore import (
	_DIR_MARK_CG,
	_DIR_MARK_OPT)
from pathspec.match import (
	HyperscanMatcher,
	_HyperscanExprDat)
from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitwildmatch import (
	GitWildMatchPattern,
	_BYTES_ENCODING,
	_DIR_MARK)

from benchmarks.match_pathspec import (
	HyperscanR1BaseMatcher)


class _GiHyperscanR1BaseMatcher(HyperscanR1BaseMatcher):
	"""
	The :class:`_GiHyperscanR1BaseMatcher` base class uses a hyperscan database in
	block mode for matching files.
	"""


class _GiHyperscanR1BlockBaseMatcher(_GiHyperscanR1BaseMatcher):
	"""
	The :class:`_GiHyperscanR1BlockBaseMatcher` base class uses a hyperscan
	database in block mode for matching files.
	"""

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class GiHyperscanR1BlockClosureMatcher(_GiHyperscanR1BlockBaseMatcher):
	"""
	The :class:`GiHyperscanR1BlockClosureMatcher` class uses a hyperscan database
	in block mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

				if include and dir_mark:
					out_include = include
					out_index = index
					out_priority = priority
				elif priority >= out_priority:
					out_include = include
					out_index = index
					out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class GiHyperscanR1BlockStateMatcher(_GiHyperscanR1BlockBaseMatcher):
	"""
	The :class:`GiHyperscanR1BlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		self._db.scan(
			file.encode('utf8'), match_event_handler=self.__on_match, context=file,
		)
		return self.__out[:2]

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

			if include and dir_mark:
				self.__out = (include, index, priority)
			elif priority >= self.__out[2]:
				self.__out = (include, index, priority)


class _GiHyperscanR1StreamBaseMatcher(_GiHyperscanR1BaseMatcher):
	"""
	The :class:`_GiHyperscanR1StreamBaseMatcher` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	_reverse_patterns = True

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class GiHyperscanR1StreamClosureMatcher(_GiHyperscanR1StreamBaseMatcher):
	"""
	The :class:`GiHyperscanR1StreamClosureMatcher` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

				if include and dir_mark:
					out_include = include
					out_index = index
					out_priority = priority
				elif priority >= out_priority:
					out_include = include
					out_index = index
					out_priority = priority

				if priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					return True

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index


# WARNING: This segfaults.
class GiHyperscanR1StreamStateMatcher(_GiHyperscanR1StreamBaseMatcher):
	"""
	The :class:`GiHyperscanR1StreamStateMatcher` class uses a hyperscan database
	in streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		with self._db.stream(match_event_handler=self.__on_match, context=file) as stream:
			stream.scan(file.encode('utf8'))

		return self.__out[:2]

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
	) -> Optional[bool]:
		#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
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

			if include and dir_mark:
				self.__out = (include, index, priority)
			elif priority >= self.__out[2]:
				self.__out = (include, index, priority)

			if priority == 2:
				# Patterns are being checked in reverse order. The first pattern that
				# matches with the highest priority takes precedence.
				return True


class _GiHyperscanR2BaseMatcher(HyperscanMatcher):
	"""
	The :class:`_GiHyperscanR2BaseMatcher` base class uses a hyperscan database in
	block mode for matching files.
	"""

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: List[Tuple[int, RegexPattern]],
	) -> List[_HyperscanExprDat]:
		# NOTICE: This is the current implementation.

		# Prepare patterns.
		expr_data: List[_HyperscanExprDat] = []
		exprs: List[bytes] = []
		id_counter = itertools.count(0)
		ids: List[int] = []
		for pattern_index, pattern in patterns:
			if pattern.include is None:
				continue

			# Encode regex.
			assert isinstance(pattern, RegexPattern), pattern
			regex = pattern.regex.pattern

			use_regexes: List[Tuple[Union[str, bytes], bool]] = []
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

				expr_data.append(_HyperscanExprDat(
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

	@staticmethod
	def _new_db() -> hyperscan.Database:
		raise NotImplementedError()


class _GiHyperscanR2BlockBaseMatcher(_GiHyperscanR2BaseMatcher):
	"""
	The :class:`_GiHyperscanR2BlockBaseMatcher` base class uses a hyperscan
	database in block mode for matching files.
	"""

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)


class GiHyperscanR2BlockClosureMatcher(_GiHyperscanR2BlockBaseMatcher):
	"""
	The :class:`GiHyperscanR2BlockClosureMatcher` class uses a hyperscan database
	in block mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

				if include and is_dir_pattern:
					out_include = include
					out_index = expr_dat.index
					out_priority = priority
				elif priority >= out_priority:
					out_include = include
					out_index = expr_dat.index
					out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class GiHyperscanR2BlockStateMatcher(_GiHyperscanR2BlockBaseMatcher):
	"""
	The :class:`GiHyperscanR2BlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None, 0)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self.__out[:2]

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
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

			if include and is_dir_pattern:
				self.__out = (include, expr_dat.index, priority)
			elif priority >= self.__out[2]:
				self.__out = (include, expr_dat.index, priority)


class _GiHyperscanR2StreamBaseMatcher(_GiHyperscanR2BaseMatcher):
	"""
	The :class:`_GiHyperscanR2StreamBaseMatcher` base class uses a hyperscan
	database in streaming mode for matching files.
	"""

	_reverse_patterns = True

	@staticmethod
	def _new_db() -> hyperscan.Database:
		return hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)


class GiHyperscanR2StreamClosureMatcher(_GiHyperscanR2StreamBaseMatcher):
	"""
	The :class:`GiHyperscanR2StreamClosureMatcher` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

				if include and is_dir_pattern:
					out_include = include
					out_index = expr_dat.index
					out_priority = priority
				elif priority >= out_priority:
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
