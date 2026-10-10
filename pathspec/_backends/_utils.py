"""
This module provides private utility functions for backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

import re
from collections.abc import (
	Iterable)
from typing import (
	TypeVar)

from pathspec.pattern import (
	Pattern)
from pathspec._typing import (
	AnyStr)

_END_ANCHOR_BYTES = re.compile(rb'\\.')
"""
Regular expression to match an escaped character.
"""

_END_ANCHOR_STR = re.compile(r'\\.')
"""
Regular expression to match an escaped character.
"""

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


def translate_end_anchor(regex: AnyStr) -> AnyStr:
	"""
	Translate Python's strict end anchor to the RE2 and Hyperscan spelling.

	*regex* (:class:`bytes` or :class:`str`) is the regular expression.

	Returns the translated regular expression (:class:`bytes` or :class:`str`).
	"""
	# Escaped backslashes are consumed as pairs, keeping literal `\Z` names
	# intact.
	if isinstance(regex, bytes):
		return _END_ANCHOR_BYTES.sub(_sub_end_anchor_bytes, regex)
	else:
		return _END_ANCHOR_STR.sub(_sub_end_anchor_str, regex)


def _sub_end_anchor_bytes(match: re.Match) -> bytes:
	"""
	Replaces Python's strict end anchor to the RE2 and Hyperscan spelling.

	*match* (:class:`re.Match`) is the match object.

	Returns the string replacement (:class:`bytes`).
	"""
	val = match[0]
	if val == rb'\Z':
		return rb'\z'
	else:
		return val


def _sub_end_anchor_str(match: re.Match) -> str:
	"""
	Replaces Python's strict end anchor to the RE2 and Hyperscan spelling.

	*match* (:class:`re.Match`) is the match object.

	Returns the string replacement (:class:`str`).
	"""
	val = match[0]
	if val == r'\Z':
		return r'\z'
	else:
		return val
