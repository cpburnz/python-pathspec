"""
This module provides private utility functions for backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

import re
from collections.abc import (
	Iterable)
from typing import (
	TypeVar,
	Union,
	overload)

from pathspec.pattern import (
	Pattern)

TPattern = TypeVar("TPattern", bound=Pattern)


@overload
def translate_end_anchor(regex: str) -> str: ...


@overload
def translate_end_anchor(regex: bytes) -> bytes: ...


def translate_end_anchor(regex: Union[str, bytes]) -> Union[str, bytes]:
	"""
	Translate Python's strict end anchor to the RE2 and Hyperscan spelling.

	Escaped backslashes are consumed as pairs, keeping literal ``\\Z`` names intact.
	"""
	if isinstance(regex, bytes):
		return re.sub(rb'\\.', lambda match: rb'\z' if match[0] == rb'\Z' else match[0], regex)
	else:
		return re.sub(r'\\.', lambda match: r'\z' if match[0] == r'\Z' else match[0], regex)


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
