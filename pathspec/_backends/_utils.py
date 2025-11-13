"""
This module provides private utility functions for backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

from collections.abc import (
	Iterable)
from typing import (
	Optional,  # Replaced by `X | None` in 3.10.
	TypeVar,
	Union,  # Replaced by `X | Y` in 3.10.
	overload)

from ..pattern import (
	Pattern)

T = TypeVar("T")
U = TypeVar("U")
TPattern = TypeVar("TPattern", bound=Pattern)


def enumerate_patterns(
	patterns: Iterable[TPattern],
	filter: bool,
	reverse: bool,
) -> list[tuple[int, TPattern]]:
	"""
	Enumerate the patterns.

	*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the patterns.

	*filter* (:class:`bool`) is whether to remove no-op patterns (:data:`True`),
	or keep them (:data:`False`).

	*reverse* (:class:`bool`) is whether to reverse the pattern order
	(:data:`True`), or keep the order (:data:`True`).

	Returns the enumerated patterns (:class:`list` of :class:`tuple`).
	"""
	out_patterns = [
		(__i, __pat)
		for __i, __pat in enumerate(patterns)
		if not filter or __pat.include is not None
	]
	if reverse:
		out_patterns.reverse()

	return out_patterns


@overload
def first(iterable: Iterable[T], default: T) -> T:
	...


@overload
def first(iterable: Iterable[T], default: None) -> Optional[T]:
	...


def first(iterable: Iterable[T], default: Optional[T]) -> Optional[T]:
	"""
	Get the first value of the iterable.

	*iterable* (:class:`.Iterable`) is the iterable.

	*default* is the default value to return if the iterable is empty.

	Returns the first value of the iterable or the default value.
	"""
	for val in iterable:
		return val

	return default
