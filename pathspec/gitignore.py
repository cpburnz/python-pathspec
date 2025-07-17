"""
This module provides :class:`.GitIgnoreSpec` which replicates
*.gitignore* behavior.
"""

from typing import (
	Any,
	AnyStr,
	Callable,  # Replaced by `collections.abc.Callable` in 3.9.
	Iterable,  # Replaced by `collections.abc.Iterable` in 3.9.
	Optional,  # Replaced by `X | None` in 3.10.
	Sequence,  # Replaced by `collections.abc.Sequence` in 3.9.
	Tuple,  # Replaced by `tuple` in 3.9.
	Type,  # Replaced by `type` in 3.9.
	TypeVar,
	Union,  # Replaced by `X | Y` in 3.10.
	cast,
	overload)

from .match import (
	DefaultMatcher,
	HyperscanMatcher,
	Matcher)
from .pathspec import (
	PathSpec)
from .pattern import (
	Pattern,
	RegexPattern)
from .patterns.gitwildmatch import (
	GitWildMatchPattern,
	_DIR_MARK)
from .util import (
	_is_iterable)

Self = TypeVar("Self", bound="GitIgnoreSpec")
"""
:class:`GitIgnoreSpec` self type hint to support Python v<3.11 using PEP
673 recommendation.
"""


class GitIgnoreSpec(PathSpec):
	"""
	The :class:`GitIgnoreSpec` class extends :class:`pathspec.pathspec.PathSpec` to
	replicate *.gitignore* behavior.
	"""

	def __eq__(self, other: object) -> bool:
		"""
		Tests the equality of this gitignore-spec with *other* (:class:`GitIgnoreSpec`)
		by comparing their :attr:`~pathspec.pattern.Pattern`
		attributes. A non-:class:`GitIgnoreSpec` will not compare equal.
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
		cls: Type[Self],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern]],
		lines: Iterable[AnyStr],
		*,
		optimize: Optional[bool] = None,
	) -> Self:
		...

	@overload
	@classmethod
	def from_lines(
		cls: Type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		optimize: Optional[bool] = None,
	) -> Self:
		...

	@classmethod
	def from_lines(
		cls: Type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		optimize: Optional[bool] = None,
	) -> Self:
		"""
		Compiles the pattern lines.

		*lines* (:class:`~collections.abc.Iterable`) yields each uncompiled
		pattern (:class:`str`). This simply has to yield each line so it can
		be a :class:`io.TextIOBase` (e.g., from :func:`open` or
		:class:`io.StringIO`) or the result from :meth:`str.splitlines`.

		*pattern_factory* can be :data:`None`, the name of a registered
		pattern factory (:class:`str`), or a :class:`~collections.abc.Callable`
		used to compile patterns. The callable must accept an uncompiled
		pattern (:class:`str`) and return the compiled pattern
		(:class:`pathspec.pattern.Pattern`).
		Default is :data:`None` for :class:`.GitWildMatchPattern`).

		*optimize* (:class:`bool` or :data:`None`) is whether to optimize the
		patterns using :module:`hyperscan`. Default is :data:`None` for
		:data:`False`.

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
		optimize: bool,
	) -> Matcher:
		"""
		Create the matcher for the patterns.

		*patterns* (:class:`~collections.abc.Sequence`) contains each compiled
		pattern (:class:`.Pattern`).

		*optimize* (:class:`bool`) is whether to optimize the patterns using
		:module:`hyperscan`.

		Returns the matcher (:class:`Matcher`).
		"""
		if optimize:
			return _GiHyperscanMatcher(cast(Sequence[RegexPattern], patterns))
		else:
			return _GiDefaultMatcher(patterns)


class _GiDefaultMatcher(DefaultMatcher):
	"""
	The :class:`_GiDefaultMatcher` class is the default implementation used by
	:class:`.GitIgnoreSpec` for matching files.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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
				pattern.include is not None
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

				if pattern.include and dir_mark:
					out_include = pattern.include
					out_index = index
					out_priority = priority
				elif priority >= out_priority:
					out_include = pattern.include
					out_index = index
					out_priority = priority

				if is_reversed and priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					break

		return out_include, out_index




class _GiHyperscanMatcher(HyperscanMatcher):
	"""
	The :class:`_GiHyperscanMatcher` class uses a hyperscan database in block mode
	for matching files.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
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

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			# TODO: How to use capture group?
			# - Idea: Run Pythonregex.
			# - Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
			#   run from there.

			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")


		# TODO: Convert this.
		for index, pattern in self._patterns:
			if (
				pattern.include is not None
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

				if pattern.include and dir_mark:
					out_include = pattern.include
					out_index = index
					out_priority = priority
				elif priority >= out_priority:
					out_include = pattern.include
					out_index = index
					out_priority = priority

				if is_reversed and priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					break



		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index
