"""
This module provides private utility functions for backends.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

import re
import warnings
from collections.abc import (
	Iterable)
from typing import (
	TypeVar)

from pathspec.pattern import (
	Pattern,
	RegexPattern)

TPattern = TypeVar("TPattern", bound=Pattern)


def has_regex_flags(patterns: Iterable[Pattern]) -> bool:
	"""
	Check for active Python regexes with flags not encoded in the expression.

	Native backends recompile the expression, losing external compile flags.
	Inline flags are already part of the expression and need no translation.
	"""
	for pattern in patterns:
		if pattern.include is None or not isinstance(pattern, RegexPattern):
			continue

		regex = pattern.regex
		if not isinstance(regex, re.Pattern):
			continue

		# UNICODE is the default for str regexes. Avoid recompiling ordinary
		# patterns (including the built-in gitignore patterns).
		if not regex.flags & ~int(re.UNICODE):
			continue

		try:
			# This expression is only a probe, not the regex used for matching.
			# Do not expose warnings from, e.g., VERBOSE comment contents.
			with warnings.catch_warnings():
				warnings.simplefilter('ignore', FutureWarning)
				inline_flags = re.compile(regex.pattern).flags
		except re.error:
			# The expression may only be valid with external flags, e.g., a
			# VERBOSE comment containing an unmatched bracket.
			return True

		if regex.flags != inline_flags:
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
