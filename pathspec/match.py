"""
This module defines matchers which are used by :class:`~pathspec.PathSpec` to
actually match files against patterns.
"""
from __future__ import annotations

import itertools
from typing import (
	Any,
	Iterable,  # Replaced by `collections.abc.Iterable` in 3.9.
	List,  # Replaced by `list` in 3.9.
	Literal,
	NamedTuple,
	Optional,  # Replaced by `X | None` in 3.10.
	TypeVar,
	Tuple,  # Replaced by `tuple` in 3.9.
	Union)  # Replaced by `X | Y` in 3.10.

try:
	import hyperscan
	hyperscan_error: Optional[ModuleNotFoundError] = None
except ModuleNotFoundError as e:
	hyperscan = None
	hyperscan_error = e

from .pattern import (
	Pattern,
	RegexPattern)
from .patterns.gitwildmatch import (
	GitWildMatchPattern,
	_BYTES_ENCODING,
	_DIR_MARK)
from .util import (
	check_match_file)

_DIR_MARK_CG = f'(?P<{_DIR_MARK}>/)'
"""
This regular expression matches the directory marker.
"""

_DIR_MARK_OPT = f'(?:{_DIR_MARK_CG}.*)?$'
"""
This regular expression matches the optional directory marker and sub-path.
"""

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

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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
			patterns, no_filter=no_filter, no_reverse=no_reverse,
		)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		"""
		Initialize the :class:`HyperscanMatcher` instance.

		*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the compiled
		patterns.
		"""
		if hyperscan is None:
			raise hyperscan_error

		use_patterns = _enumerate_patterns(
			patterns, no_filter=False, no_reverse=True,
		)

		db, expr_data = self.__make_db(use_patterns)

		self._db = db
		self._expr_data = expr_data
		self._out: Tuple[Optional[bool], Optional[int]] = (None, None)
		self._patterns = dict(use_patterns)

	@staticmethod
	def __make_db(
		patterns: List[Tuple[int, RegexPattern]],
	) -> Tuple[hyperscan.Database, list[_HyperscanExprDat]]:
		"""
		Create the hyperscan database from the given patterns.

		*patterns* (:class:`~collections.abc.Sequence` of :class:`.RegexPattern`)
		contains the patterns.

		Returns :class:`tuple` containing the database (:class:`hyperscan.Database`),
		and a :class:`list` indexed by expression id (:class:`int`) to its data
		(:class:`_HyperscanExprDat`).
		"""
		# Create database.
		db = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)

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
		return db, expr_data

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		# NOTICE: According to benchmarking, a method callback is 33% faster than
		# using a closure here.
		self._out = (None, None)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self._out

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
		include = expr_dat.include
		if include:
			# Store match.
			self._out = (include, expr_id)


def _enumerate_patterns(
	patterns: Iterable[TPattern],
	no_filter: bool,
	no_reverse: bool,
) -> List[Tuple[int, TPattern]]:
	"""
	Enumerate the patterns.

	*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the patterns.

	*no_filter* (:class:`bool`) is whether to keep null patterns (:data:`True`),
	or remove them (:data:`False`).

	*no_reverse* (:class:`bool`) is whether to keep the pattern order
	(:data:`True`), or reverse the order (:data:`True`).

	Returns the enumerated patterns (:class:`list` of :class:`tuple`).
	"""
	out_patterns = [
		(__i, __pat)
		for __i, __pat in enumerate(patterns)
		if no_filter or __pat.include is not None
	]
	if not no_reverse:
		out_patterns.reverse()

	return out_patterns


class _HyperscanExprDat(NamedTuple):
	include: bool
	index: int
	is_dir_pattern: bool
