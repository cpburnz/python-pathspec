# coding: utf-8
"""
This module implements gitignore style pattern matching which
incorporates POSIX glob patterns.
"""

import re

from .pattern import RegexPattern
from .compat import string_types


class GitIgnorePattern(RegexPattern):
	"""
	The ``GitIgnorePattern`` class represents a compiled gitignore
	pattern.
	"""

	# Keep the dict-less class hierarchy.
	__slots__ = ()

	def __init__(self, pattern):
		"""
		Initializes the ``GitIgnorePattern`` instance.

		*pattern* (``str``) is the gitignore pattern.
		"""

		if not isinstance(pattern, string_types):
			raise TypeError("pattern:{!r} is not a string.".format(pattern))

		pattern = pattern.strip()

		if pattern.startswith('#'):
			# A pattern starting with a hash ('#') serves as a comment
			# (neither includes nor excludes files). Escape the hash with a
			# back-slash to match a literal hash (i.e., '\#').
			regex = None
			include = None

		elif pattern:

			if pattern.startswith('!'):
				# A pattern starting with an exclamation mark ('!') negates the
				# pattern (exclude instead of include). Escape the exclamation
				# mark with a back-slash to match a literal exclamation mark
				# (i.e., '\!').
				include = False
				# Remove leading exclamation mark.
				pattern = pattern[1:]
			else:
				include = True

			if pattern.startswith('\\'):
				# Remove leading back-slash escape for escaped hash ('#') or
				# exclamation mark ('!').
				pattern = pattern[1:]

			# Split pattern into segments.
			pattern_segs = pattern.split('/')

			# Normalize pattern to make processing easier.

			if not pattern_segs[0]:
				# A pattern beginning with a slash ('/') will only match paths
				# directly on the root directory instead of any descendant
				# paths. So, remove empty first segment to make pattern relative
				# to root.
				del pattern_segs[0]
			else:
				# A pattern without a beginning slash ('/') will match any
				# descendant path. This is equivilent to "**/{pattern}". So,
				# prepend with double-asterisks to make pattern relative to
				# root.
				if pattern_segs[0] != '**':
					pattern_segs.insert(0, '**')

			if not pattern_segs[-1]:
				# A pattern ending with a slash ('/') will match all descendant
				# paths of if it is a directory but not if it is a regular file.
				# This is equivilent to "{pattern}/**". So, set last segment to
				# double asterisks to include all descendants.
				pattern_segs[-1] = '**'

			# Build regular expression from pattern.
			regex = ['^']
			need_slash = False
			end = len(pattern_segs) - 1
			for i, seg in enumerate(pattern_segs):
				if seg == '**':
					if i == 0 and i == end:
						# A pattern consisting solely of double-asterisks ('**')
						# will match every path.
						regex.append('.+')
					elif i == 0:
						# A normalized pattern beginning with double-asterisks
						# ('**') will match any leading path segments.
						regex.append('(?:.+/)?')
						need_slash = False
					elif i == end:
						# A normalized pattern ending with double-asterisks ('**')
						# will match any trailing path segments.
						regex.append('/.+')
					else:
						# A pattern with inner double-asterisks ('**') will match
						# multiple (or zero) inner path segments.
						regex.append('(?:/.+)?')
						need_slash = True
				elif seg == '*':
					# Match single path segment.
					if need_slash:
						regex.append('/')
					regex.append('[^/]+')
					need_slash = True
				else:
					# Match segment glob pattern.
					if need_slash:
						regex.append('/')
					regex.append(self._translate_segment_glob(seg))
					need_slash = True
			regex.append('$')
			regex = ''.join(regex)

		else:
			# A blank pattern is a null-operation (neither includes nor
			# excludes files).
			regex = None
			include = None

		super(GitIgnorePattern, self).__init__(regex, include)

	@staticmethod
	def _translate_segment_glob(pattern):
		"""
		Translates the glob pattern to a regular expression. This is used in
		the constructor to translate a path segment glob pattern to its
		corresponding regular expression.

		*pattern* (``str``) is the glob pattern.

		Returns the regular expression (``str``).
		"""
		# NOTE: This is derived from `fnmatch.translate()` and is similar to
		# the POSIX function `fnmatch()` with the `FNM_PATHNAME` flag set.

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
				# Multi-character wildcard. Match any string (except slashes),
				# including an empty string.
				regex += '[^/]*'

			elif char == '?':
				# Single-character wildcard. Match any single character (except
				# a slash).
				regex += '[^/]'

			elif char == '[':
				# Braket expression wildcard. Except for the beginning
				# exclamation mark, the whole braket expression can be used
				# directly as regex but we have to find where the expression
				# ends.
				# - "[][!]" matchs ']', '[' and '!'.
				# - "[]-]" matchs ']' and '-'.
				# - "[!]a-]" matchs any character except ']', 'a' and '-'.
				j = i
				# Pass brack expression negation.
				if j < end and pattern[j] == '!':
					j += 1
				# Pass first closing braket if it is at the beginning of the
				# expression.
				if j < end and pattern[j] == ']':
					j += 1
				# Find closing braket. Stop once we reach the end or find it.
				while j < end and pattern[j] != ']':
					j += 1

				if j < end:
					# Found end of braket expression. Increment j to be one past
					# the closing braket:
					#
					#  [...]
					#   ^   ^
					#   i   j
					#
					j += 1
					expr = '['

					if pattern[i] == '!':
						# Braket expression needs to be negated.
						expr += '^'
						i += 1
					elif pattern[i] == '^':
						# POSIX declares that the regex braket expression negation
						# "[^...]" is undefined in a glob pattern. Python's
						# `fnmatch.translate()` escapes the caret ('^') as a
						# literal. To maintain consistency with undefined behavior,
						# I am escaping the '^' as well.
						expr += '\\^'
						i += 1

					# Build regex braket expression. Escape slashes so they are
					# treated as literal slashes by regex as defined by POSIX.
					expr += pattern[i:j].replace('\\', '\\\\')

					# Add regex braket expression to regex result.
					regex += expr

					# Set i to one past the closing braket.
					i = j

				else:
					# Failed to find closing braket, treat opening braket as a
					# braket literal instead of as an expression.
					regex += '\\['

			else:
				# Regular character, escape it for regex.
				regex += re.escape(char)

		return regex
