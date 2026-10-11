"""
This module provides private utility functions for backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

import re
from collections.abc import (
	Iterable)
from typing import (
	Union,  # Replaced by `X | Y` in 3.10.
	TypeVar,
	overload)

from pathspec.pattern import (
	Pattern,
	RegexPattern)
from pathspec._typing import (
	AnyStr)

_END_ANCHOR_BYTES = re.compile(rb'\\.', re.DOTALL)
"""
Regular expression to match an escaped character.
"""

_END_ANCHOR_STR = re.compile(r'\\.', re.DOTALL)
"""
Regular expression to match an escaped character.
"""

TPattern = TypeVar("TPattern", bound=Pattern)

_TRANSLATABLE_FLAGS = (
	(int(re.IGNORECASE), 'i'),
	(int(re.MULTILINE), 'm'),
	(int(re.DOTALL), 's'),
)
"""
The compile flags that both RE2 and Hyperscan understand as global inline flags
at the start of an expression (`(?ims)`).

RE2 rejects `(?x)` (it has no verbose mode), and both engines reject `(?a)`,
`(?u)`, `(?U)`, and `(?L)`. Note that RE2 reads `(?U)` as *non-greedy*, which
is not what Python's `re.UNICODE` means.
"""

_NOOP_FLAGS = int(re.UNICODE | re.DEBUG)
r"""
The compile flags that need no translation.

-	`re.UNICODE` is implied for str patterns, and both engines match `\w`, `\d`,
	`\s`, and `\b` as ASCII regardless.

-	`re.DEBUG` only affects how Python compiles the expression.
"""

_ASCII_FLAGS = int(re.ASCII)
"""
The compile flags that both engines satisfy by default because their character
classes and word boundaries are ASCII-only.

`re.ASCII` cannot be relied upon this way when it is combined with
`re.IGNORECASE`: the engines fold the case of Unicode characters that Python
would leave alone.
"""


def supports_regex_flags(flags: int) -> bool:
	"""
	Check whether a native backend can preserve the compile *flags*.

	*flags* (:class:`int`) is the flags of a compiled :class:`re.Pattern`.

	Returns the answer (:class:`bool`).
	"""
	representable = (
		_NOOP_FLAGS | _ASCII_FLAGS
		| int(re.IGNORECASE | re.MULTILINE | re.DOTALL)
	)
	if flags & ~representable:
		return False

	if flags & re.ASCII and flags & re.IGNORECASE:
		return False

	return True


@overload
def translate_regex_flags(regex: str, flags: int) -> str:
	...


@overload
def translate_regex_flags(regex: bytes, flags: int) -> bytes:
	...


@overload
def translate_regex_flags(regex: Union[str, bytes], flags: int) -> Union[str, bytes]:
	...


def translate_regex_flags(
	regex: Union[str, bytes],
	flags: int,
) -> Union[str, bytes]:
	"""
	Prepend the global inline flags that a native backend understands.

	*regex* (:class:`bytes` or :class:`str`) is the regular expression.

	*flags* (:class:`int`) is the flags of the compiled :class:`re.Pattern`
	that *regex* came from. Only flags accepted by
	:func:`supports_regex_flags` may be translated.

	Returns the regular expression (:class:`bytes` or :class:`str`).
	"""
	letters = ''.join(
		letter
		for flag, letter in _TRANSLATABLE_FLAGS
		if flags & flag
	)
	if not letters:
		return regex

	prefix = f'(?{letters})'
	if isinstance(regex, bytes):
		return prefix.encode('ascii') + regex

	return prefix + regex


def get_regex_flags(regex: Union[re.Pattern, str, bytes, None]) -> int:
	"""
	Get the compile flags of a pattern's regular expression.

	*regex* (:class:`re.Pattern`, :class:`bytes`, :class:`str`, or
	:data:`None`) is the regular expression of a :class:`.RegexPattern`.

	Returns the flags (:class:`int`) of a regular expression compiled by
	Python's *re* module, or zero (:class:`int`) for anything else (a native
	backend only ever sees the expression of a foreign pattern).
	"""
	if isinstance(regex, re.Pattern):
		return int(regex.flags)

	return 0


def has_unsupported_flags(patterns: Iterable[Pattern]) -> bool:
	"""
	Check for active patterns with compile flags a native backend can't keep.

	*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the patterns.

	Returns the answer (:class:`bool`).
	"""
	for pattern in patterns:
		if pattern.include is None or not isinstance(pattern, RegexPattern):
			continue

		regex = pattern.regex
		if not isinstance(regex, re.Pattern):
			# The pattern was not compiled by Python's *re* module. Its flags
			# are unknown, and only the simple backend can use it faithfully.
			continue

		if not supports_regex_flags(regex.flags):
			return True

	return False


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
def translate_end_anchor(regex: str) -> str:
	...


@overload
def translate_end_anchor(regex: bytes) -> bytes:
	...


@overload
def translate_end_anchor(regex: Union[str, bytes]) -> Union[str, bytes]:
	...


def translate_end_anchor(regex: Union[str, bytes]) -> Union[str, bytes]:
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
