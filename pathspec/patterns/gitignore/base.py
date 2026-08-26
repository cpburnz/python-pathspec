"""
This module provides common classes for the gitignore patterns.
"""

import re

from typing import (
	Literal)

from pathspec.pattern import (
	RegexPattern)
from pathspec._typing import (
	AnyStr,  # Removed in 3.18.
	assert_unreachable)

_BYTES_ENCODING = 'latin1'
"""
The encoding to use when parsing a byte string pattern.
"""

_POSIX_CLASS_TO_REGEX = {
	# Git's wildmatch implements POSIX bracket character classes using its own
	# ASCII (locale-independent) ``is*`` functions, so each class maps to an
	# explicit ASCII set. These are NOT the Unicode-aware equivalents (``\w``,
	# ``\d``, ``\s``); using those would over-match non-ASCII characters that
	# git never matches.
	'alnum': '0-9A-Za-z',
	'alpha': 'A-Za-z',
	'blank': '\\t ',
	'cntrl': '\\x00-\\x1f\\x7f',
	'digit': '0-9',
	'graph': '\\x21-\\x7e',
	'lower': 'a-z',
	'print': '\\x20-\\x7e',
	'punct': '!-/:-@\\[-`{-~',
	'space': '\\t\\n\\r ',
	'upper': 'A-Z',
	'xdigit': '0-9A-Fa-f',
}
"""
Maps each POSIX bracket character class name to the ASCII regex range that
reproduces git's wildmatch behavior.
"""

_POSIX_CLASS_REGEX = re.compile(r'\[:(\^?)([^:\]]*):\]')
"""
Matches a POSIX bracket character class token such as ``[:alpha:]`` inside a
bracket expression. Group 1 captures a leading caret (unsupported by git);
group 2 captures the class name.
"""


class _InvalidPosixClass(Exception):
	"""
	Raised internally when a bracket expression contains an unknown or negated
	POSIX character class name. Git treats such a pattern as malformed.
	"""
	pass


def _translate_posix_class(match: 're.Match') -> str:
	"""
	Translate a single POSIX character class token to its ASCII regex range.
	Raises :class:`_InvalidPosixClass` for a negated (``[:^name:]``) or unknown
	class name, matching git's treatment of it as a malformed pattern.
	"""
	negated, name = match.group(1), match.group(2)
	class_regex = _POSIX_CLASS_TO_REGEX.get(name)
	if negated or class_regex is None:
		raise _InvalidPosixClass()
	return class_regex


class _GitIgnoreBasePattern(RegexPattern):
	"""
	.. warning:: This class is not part of the public API. It is subject to
		change.

	The :class:`_GitIgnoreBasePattern` class is the base implementation for a
	compiled gitignore pattern.
	"""

	# Keep the dict-less class hierarchy.
	__slots__ = ()

	@staticmethod
	def escape(s: AnyStr) -> AnyStr:
		"""
		Escape special characters in the given string.

		*s* (:class:`str` or :class:`bytes`) a filename or a string that you want to
		escape, usually before adding it to a ".gitignore".

		Returns the escaped string (:class:`str` or :class:`bytes`).
		"""
		if isinstance(s, str):
			return_type = str
			string = s
		elif isinstance(s, bytes):
			return_type = bytes
			string = s.decode(_BYTES_ENCODING)
		else:
			raise TypeError(f"s:{s!r} is not a unicode or byte string.")

		# Reference: https://git-scm.com/docs/gitignore#_pattern_format
		out_string = ''.join((f"\\{x}" if x in '\\[]!*#?' else x) for x in string)

		if return_type is bytes:
			out_bytes = out_string.encode(_BYTES_ENCODING)
			return out_bytes  # type: ignore[return-value]
		else:
			return out_string  # type: ignore[return-value]

	@staticmethod
	def _translate_segment_glob(
		pattern: str,
		range_error: Literal['literal', 'raise'],
	) -> str:
		"""
		Translates the glob pattern to a regular expression. This is used in the
		constructor to translate a path segment glob pattern to its corresponding
		regular expression.

		*pattern* (:class:`str`) is the glob pattern.

		*range_error* (:class:`int`) is how to handle invalid range notation in the
		pattern:

		-	:data:`"literal"`: Invalid notation will be treated as a literal string.

		-	:data:`"raise"`: Invalid notation will cause a :class:`_RangeError` to be
			raised.

		Returns the regular expression (:class:`str`).
		"""
		# NOTE: This is derived from `fnmatch.translate()` and is similar to the
		# POSIX function `fnmatch()` with the `FNM_PATHNAME` flag set.

		escape = False
		regex = ''
		i, end = 0, len(pattern)
		while i < end:
			# Get next character.
			char = pattern[i]
			i += 1

			if escape:
				# Escape the character.
				escape = False
				regex += re.escape(char)

			elif char == '\\':
				# Escape character, escape next character.
				escape = True

			elif char == '*':
				# Multi-character wildcard. Match any string (except slashes), including
				# an empty string.
				regex += '[^/]*'

			elif char == '?':
				# Single-character wildcard. Match any single character (except a
				# slash).
				regex += '[^/]'

			elif char == '[':
				# Bracket expression (range notation) wildcard. Except for the beginning
				# exclamation mark, the whole bracket expression can be used directly as
				# regex, but we have to find where the expression ends.
				# - "[][!]" matches ']', '[' and '!'.
				# - "[]-]" matches ']' and '-'.
				# - "[!]a-]" matches any character except ']', 'a' and '-'.
				bracket_start = i - 1
				j = i

				# Pass bracket expression negation.
				if j < end and (pattern[j] == '!' or pattern[j] == '^'):
					j += 1

				# Pass first closing bracket if it is at the beginning of the
				# expression.
				if j < end and pattern[j] == ']':
					j += 1

				# Find closing bracket. Stop once we reach the end or find it.
				while j < end and pattern[j] != ']':
					if pattern[j] == '[' and j + 1 < end and pattern[j + 1] == ':':
						# Skip over a POSIX character class token ("[:name:]") so its
						# internal closing bracket is not mistaken for the end of the
						# whole bracket expression.
						close = pattern.find(':]', j + 2)
						if close == -1:
							j = end
							break
						j = close + 2
					else:
						j += 1

				if j < end:
					# Found end of bracket expression. Increment j to be one past the
					# closing bracket:
					#
					#  [...]
					#   ^   ^
					#   i   j
					#
					j += 1
					expr = '['

					if pattern[i] == '!':
						# Bracket expression needs to be negated.
						expr += '^'
						i += 1
					elif pattern[i] == '^':
						# POSIX declares that the regex bracket expression negation "[^...]"
						# is undefined in a glob pattern. Python's `fnmatch.translate()`
						# escapes the caret ('^') as a literal. Git supports the using a
						# caret for negation. Maintain consistency with Git because that is
						# the expected behavior.
						expr += '^'
						i += 1

					# Build regex bracket expression. Escape slashes so they are treated
					# as literal slashes by regex as defined by POSIX.
					body = pattern[i:j].replace('\\', '\\\\')

					# Translate POSIX character classes (e.g. "[:alpha:]") into their
					# ASCII regex equivalents. Git's wildmatch supports these but
					# Python's `re` does not, so passing them through verbatim builds a
					# broken regex that silently mismatches (and warns about a nested
					# set).
					try:
						body = _POSIX_CLASS_REGEX.sub(_translate_posix_class, body)
					except _InvalidPosixClass:
						# Git treats an unknown or negated class name as a malformed
						# pattern that matches nothing.
						if range_error == 'raise':
							raise _RangeError((
								f"Invalid character class found in pattern={pattern!r}."
							))
						else:
							# Treat the whole bracket expression as a literal.
							regex += re.escape(pattern[bracket_start:j])
							i = j
							continue

					expr += body

					if range_error == 'raise':
						try:
							re.compile(expr)
						except re.error as e:
							raise _RangeError((
								f"Invalid range notation={pattern[i:j]!r} found in "
								f"pattern={pattern!r}."
							)) from e

					# Add regex bracket expression to regex result.
					regex += expr

					# Set i to one past the closing bracket.
					i = j

				else:
					# Failed to find closing bracket.
					if range_error == 'literal':
						# Treat opening bracket as a bracket literal instead of as an
						# expression.
						regex += '\\['
					elif range_error == 'raise':
						# Treat invalid range notation as an error.
						raise _RangeError((
							f"Invalid range notation={pattern[i:j]!r} found in pattern="
							f"{pattern!r}."
						))
					else:
						assert_unreachable(f"{range_error=!r} is invalid.")

			else:
				# Regular character, escape it for regex.
				regex += re.escape(char)

		if escape:
			raise ValueError((
				f"Escape character found with no next character to escape: {pattern!r}"
			))  # ValueError

		return regex


class GitIgnorePatternError(ValueError):
	"""
	The :class:`GitIgnorePatternError` class indicates an invalid gitignore
	pattern.
	"""
	pass


class _RangeError(GitIgnorePatternError):
	"""
	The :class:`_RangeError` class indicates an invalid range notation was found
	in a gitignore pattern.
	"""
	pass
