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

_POSIX_CHAR_CLASSES = {
	'alnum': '0-9A-Za-z',
	'alpha': 'A-Za-z',
	'blank': ' \\t',
	'cntrl': '\\x00-\\x1f\\x7f',
	'digit': '0-9',
	'graph': '\\x21-\\x7e',
	'lower': 'a-z',
	'print': '\\x20-\\x7e',
	'punct': '\\x21-\\x2f\\x3a-\\x40\\x5b-\\x60\\x7b-\\x7e',
	'space': ' \\t\\n\\x0b\\f\\r',
	'upper': 'A-Z',
	'xdigit': '0-9A-Fa-f',
}
"""
The ASCII ranges equivalent to each POSIX character class, matching Git's
``wildmatch`` (which evaluates them in the C locale). Python's ``re`` has no
POSIX class syntax, so ``[:alpha:]`` etc. must be expanded to these ranges.
"""


def _translate_bracket_body(body: str) -> str:
	"""
	Translate the interior of a glob bracket expression (the characters between
	``[`` and its closing ``]``, with the ``]`` included) to the body of a
	regular-expression bracket expression.

	Backslashes are escaped so they are treated as literal slashes by regex (as
	POSIX defines), and any POSIX character classes (``[:alpha:]`` etc.) are
	expanded to their equivalent ranges, because Python's ``re`` does not
	understand POSIX class syntax and would otherwise mis-parse them.

	*body* (:class:`str`) is the bracket interior including the trailing ``]``.

	Returns the regex bracket body (:class:`str`).
	"""
	out = []
	i, end = 0, len(body)
	while i < end:
		if body[i] == '[' and body[i+1:i+2] == ':':
			class_end = body.find(':]', i + 2)
			if class_end != -1:
				name = body[i+2:class_end]
				if name in _POSIX_CHAR_CLASSES:
					out.append(_POSIX_CHAR_CLASSES[name])
					i = class_end + 2
					continue
		char = body[i]
		out.append('\\\\' if char == '\\' else char)
		i += 1
	return ''.join(out)


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
				j = i

				# Pass bracket expression negation.
				if j < end and (pattern[j] == '!' or pattern[j] == '^'):
					j += 1

				# Pass first closing bracket if it is at the beginning of the
				# expression.
				if j < end and pattern[j] == ']':
					j += 1

				# Find closing bracket. Stop once we reach the end or find it.
				# A POSIX character class ("[:alpha:]" etc.) is skipped as a unit
				# so the ']' that closes the class is not mistaken for the ']'
				# that closes the whole bracket expression.
				while j < end and pattern[j] != ']':
					if pattern[j] == '[' and pattern[j+1:j+2] == ':':
						class_end = pattern.find(':]', j + 2)
						if class_end == -1:
							break
						j = class_end + 2
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
					# as literal slashes by regex as defined by POSIX, and expand any
					# POSIX character classes ("[:alpha:]" etc.), which Python's `re`
					# does not understand, to equivalent ranges (matching Git).
					expr += _translate_bracket_body(pattern[i:j])

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
