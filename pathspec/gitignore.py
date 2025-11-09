"""
This module provides :class:`.GitIgnoreSpec` which replicates *.gitignore*
behavior.
"""

import itertools
from collections.abc import (
	Callable,
	Iterable,
	Sequence)
from typing import (
	Any,
	AnyStr,
	Literal,
	Optional,  # Replaced by `X | None` in 3.10.
	TypeVar,
	Union,  # Replaced by `X | Y` in 3.10.
	cast,
	overload)

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from .match import (
	DefaultMatcher,
	HyperscanMatcher,
	Matcher,
	_HyperscanExprDat,
	_OPTIMIZE_LIB)
from .pathspec import (
	PathSpec)
from .pattern import (
	Pattern,
	RegexPattern)
from .patterns.gitwildmatch import (
	GitWildMatchPattern,
	_BYTES_ENCODING,
	_DIR_MARK)
from .util import (
	_is_iterable)

_DIR_MARK_CG = f'(?P<{_DIR_MARK}>/)'
"""
This regular expression matches the directory marker.
"""

_DIR_MARK_OPT = f'(?:{_DIR_MARK_CG}.*)?$'
"""
This regular expression matches the optional directory marker and sub-path.
"""

Self = TypeVar("Self", bound="GitIgnoreSpec")
"""
:class:`GitIgnoreSpec` self type hint to support Python v<3.11 using PEP 673
recommendation.
"""


class GitIgnoreSpec(PathSpec):
	"""
	The :class:`GitIgnoreSpec` class extends :class:`pathspec.pathspec.PathSpec`
	to replicate *.gitignore* behavior.
	"""

	def __eq__(self, other: object) -> bool:
		"""
		Tests the equality of this gitignore-spec with *other* (:class:`GitIgnoreSpec`)
		by comparing their :attr:`~pathspec.pattern.Pattern` attributes. A
		non-:class:`GitIgnoreSpec` will not compare equal.
		"""
		if isinstance(other, GitIgnoreSpec):
			return super().__eq__(other)
		elif isinstance(other, PathSpec):
			return False
		else:
			return NotImplemented

	# Support reversed order of arguments from PathSpec.
	@overload
	@classmethod
	def from_lines(
		cls: type[Self],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern]],
		lines: Iterable[AnyStr],
		*,
		optimize: Union[bool, Literal['hyperscan'], None] = None,
	) -> Self:
		...

	@overload
	@classmethod
	def from_lines(
		cls: type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		optimize: Union[bool, Literal['hyperscan'], None] = None,
	) -> Self:
		...

	@classmethod
	def from_lines(
		cls: type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		optimize: Union[bool, Literal['hyperscan'], None] = None,
	) -> Self:
		"""
		Compiles the pattern lines.

		*lines* (:class:`~collections.abc.Iterable`) yields each uncompiled pattern
		(:class:`str`). This simply has to yield each line so it can be a
		:class:`io.TextIOBase` (e.g., from :func:`open` or :class:`io.StringIO`) or
		the result from :meth:`str.splitlines`.

		*pattern_factory* can be :data:`None`, the name of a registered pattern
		factory (:class:`str`), or a :class:`~collections.abc.Callable` used to
		compile patterns. The callable must accept an uncompiled pattern
		(:class:`str`) and return the compiled pattern (:class:`pathspec.pattern.Pattern`).
		Default is :data:`None` for :class:`.GitWildMatchPattern`.

		*optimize* (:class:`bool`, :class:`str`, or :data:`None`) is whether to
		optimize the patterns, and optionally which library to use. If :data:`True`,
		use the best available library. If :class:`str`, must be one of the
		following libraries: "hyperscan". Default is :data:`None` for :data:`False`.

		Returns the :class:`GitIgnoreSpec` instance.
		"""
		if pattern_factory is None:
			pattern_factory = GitWildMatchPattern

		elif (isinstance(lines, (str, bytes)) or callable(lines)) and _is_iterable(pattern_factory):
			# Support reversed order of arguments from PathSpec.
			pattern_factory, lines = lines, pattern_factory

		self = super().from_lines(pattern_factory, lines, optimize=optimize)
		return cast(Self, self)

	@staticmethod
	def _make_matcher(
		patterns: Sequence[Pattern],
		optimize: Union[bool, Literal['hyperscan']],
	) -> Matcher:
		"""
		Create the matcher for the patterns.

		*patterns* (:class:`~collections.abc.Sequence`) contains each compiled
		pattern (:class:`.Pattern`).

		*optimize* (:class:`bool` or :class:`str`) is whether to optimize the
		patterns, and optionally which library to use.

		Returns the matcher (:class:`Matcher`).
		"""
		if optimize is True:
			optimize = _OPTIMIZE_LIB

		if optimize == 'hyperscan':
			return _GiHyperscanMatcher(cast(Sequence[RegexPattern], patterns))
		else:
			return _GiDefaultMatcher(patterns)


class _GiDefaultMatcher(DefaultMatcher):
	"""
	The :class:`_GiDefaultMatcher` class is the default implementation used by
	:class:`.GitIgnoreSpec` for matching files.
	"""

	_patterns: list[tuple[int, GitWildMatchPattern]]

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		is_reversed = self._is_reversed

		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0
		for index, pattern in self._patterns:
			if (
				(include := pattern.include) is not None
				and (match := pattern.match_file(file)) is not None
			):
				# Pattern matched.

				# Check for directory marker.
				dir_mark = match.match.groupdict().get(_DIR_MARK)

				if dir_mark:
					# Pattern matched by a directory pattern.
					priority = 1
				else:
					# Pattern matched by a file pattern.
					priority = 2

				if is_reversed:
					if priority > out_priority:
						out_include = include
						out_index = index
						out_priority = priority
				else:
					# Forward.
					if (include and dir_mark) or priority >= out_priority:
						out_include = include
						out_index = index
						out_priority = priority

				if is_reversed and priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with priority 2 takes precedence.
					break

		return out_include, out_index


class _GiHyperscanMatcher(HyperscanMatcher):
	"""
	The :class:`_GiHyperscanMatcher` class uses a hyperscan database in block mode
	for matching files.
	"""

	_out: tuple[Optional[bool], Optional[int], int]

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		"""
		Initialize the :class:`HyperscanMatcher` instance.

		*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the compiled
		patterns.
		"""
		super().__init__(patterns)
		self._out = (None, None, 0)

	@staticmethod
	def _init_db(
		db: hyperscan.Database,
		patterns: list[tuple[int, RegexPattern]],
	) -> list[_HyperscanExprDat]:
		"""
		Create the hyperscan database from the given patterns.

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

	def match_file(self, file: str) -> tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		# NOTICE: According to benchmarking, a method callback is 13% faster than
		# using a closure here.
		self._out = (None, None, 0)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self._out[:2]

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
		if (include := expr_dat.include) is not None:
			is_dir_pattern = expr_dat.is_dir_pattern
			if is_dir_pattern:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			if (include and is_dir_pattern) or priority >= self._out[2]:
				self._out = (include, expr_dat.index, priority)
