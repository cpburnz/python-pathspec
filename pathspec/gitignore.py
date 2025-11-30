"""
This module provides :class:`.GitIgnoreSpec` which replicates *.gitignore*
behavior.
"""
from __future__ import annotations

from collections.abc import (
	Callable,
	Iterable,
	Sequence)
from typing import (
	AnyStr,
	Optional,  # Replaced by `X | None` in 3.10.
	TypeVar,
	Union,  # Replaced by `X | Y` in 3.10.
	cast,
	overload)

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from ._backends.base import (
	Backend,
	BackendNamesHint)
from ._backends.agg import (
	make_gitignore_backend)
from .pathspec import (
	PathSpec)
from .pattern import (
	Pattern)
from .patterns.gitwildmatch import (
	GitWildMatchPattern)
from ._typing import (
	override)  # Added in 3.12.
from .util import (
	_is_iterable)

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
		backend: Union[BackendNamesHint, str, None] = None,
		_test_backend_factory: Optional[Callable[[Sequence[Pattern]], Backend]] = None,
	) -> Self:
		...

	@overload
	@classmethod
	def from_lines(
		cls: type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		backend: Union[BackendNamesHint, str, None] = None,
		_test_backend_factory: Optional[Callable[[Sequence[Pattern]], Backend]] = None,
	) -> Self:
		...

	@override
	@classmethod
	def from_lines(
		cls: type[Self],
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
		*,
		backend: Union[BackendNamesHint, str, None] = None,
		_test_backend_factory: Optional[Callable[[Sequence[Pattern]], Backend]] = None,
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

		*backend* (:class:`str` or :data:`None`) is the pattern (or regex) matching
		backend to use. Default is :data:`None` for "best" to use the best available
		backend. Priority of backends is: "re2", "hyperscan", "simple". The "simple"
		backend is always available.

		Returns the :class:`GitIgnoreSpec` instance.
		"""
		if pattern_factory is None:
			pattern_factory = GitWildMatchPattern

		elif (isinstance(lines, (str, bytes)) or callable(lines)) and _is_iterable(pattern_factory):
			# Support reversed order of arguments from PathSpec.
			pattern_factory, lines = lines, pattern_factory

		self = super().from_lines(pattern_factory, lines, backend=backend, _test_backend_factory=_test_backend_factory)
		return cast(Self, self)

	@override
	@staticmethod
	def _make_backend(
		name: BackendNamesHint,
		patterns: Sequence[Pattern],
	) -> Backend:
		"""
		Create the backend for the patterns.

		*name* (:class:`str`) is the name of the backend.

		*patterns* (:class:`.Sequence` of :class:`.Pattern`) contains the compiled
		patterns.

		Returns the backend (:class:`.Backend`).
		"""
		return make_gitignore_backend(name, patterns)
