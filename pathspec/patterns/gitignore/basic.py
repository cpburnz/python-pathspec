"""
This module provides :class:`GitIgnoreBasicPattern` which implements Git's
`gitignore`_ patterns as documented. This differs from how Git actually behaves
when including files in excluded directories.

.. _`gitignore`: https://git-scm.com/docs/gitignore
"""

from typing import (
	AnyStr,
	Optional)  # Replaced by `X | None` in 3.10.

from pathspec import (
	util)
from pathspec._typing import (
	override)

from .base import (
	GitIgnorePatternError,
	_BYTES_ENCODING,
	_GitIgnoreBasePattern)


class GitIgnoreBasicPattern(_GitIgnoreBasePattern):
	"""
	The :class:`GitIgnoreBasicPattern` class represents a compiled gitignore
	pattern as documented. This is registered as "gitignore".
	"""

	# Keep the dict-less class hierarchy.
	__slots__ = ()

	@override
	@classmethod
	def pattern_to_regex(
		cls,
		pattern: AnyStr,
	) -> tuple[Optional[AnyStr], Optional[bool]]:
		"""
		Convert the pattern into a regular expression.

		*pattern* (:class:`str` or :class:`bytes`) is the pattern to convert into a
		regular expression.

		Returns the uncompiled regular expression (:class:`str`, :class:`bytes`, or
		:data:`None`); and whether matched files should be included (:data:`True`),
		excluded (:data:`False`), or if it is a null-operation (:data:`None`).
		"""
		if isinstance(pattern, str):
			pattern_str = pattern
			return_type = str
		elif isinstance(pattern, bytes):
			pattern_str = pattern.decode(_BYTES_ENCODING)
			return_type = bytes
		else:
			raise TypeError(f"{pattern=!r} is not a unicode or byte string.")

		original_pattern = pattern_str
		del pattern

		if pattern_str.endswith('\\ '):
			# EDGE CASE: Spaces can be escaped with backslash. If a pattern that ends
			# with backslash followed by a space, only strip from left.
			pattern_str = pattern_str.lstrip()
		else:
			pattern_str = pattern_str.strip()

		regex: Optional[str]
		include: Optional[bool]

		if not pattern_str:
			# A blank pattern is a null-operation (neither includes nor excludes
			# files).
			return (None, None)

		elif pattern_str.startswith('#'):
			# A pattern starting with a hash ('#') serves as a comment (neither
			# includes nor excludes files). Escape the hash with a backslash to match
			# a literal hash (i.e., '\#').
			return (None, None)

		if pattern_str.startswith('!'):
			# A pattern starting with an exclamation mark ('!') negates the pattern
			# (exclude instead of include). Escape the exclamation mark with a back
			# slash to match a literal exclamation mark (i.e., '\!').
			include = False
			# Remove leading exclamation mark.
			pattern_str = pattern_str[1:]
		else:
			include = True

		# Allow a regex override for edge cases that cannot be handled through
		# normalization.
		override_regex: Optional[str] = None

		# Split pattern into segments.
		pattern_segs = pattern_str.split('/')

		# Check whether the pattern is specifically a directory pattern before
		# normalization.
		is_dir_pattern = not pattern_segs[-1]

		if pattern_str == '/':
			# EDGE CASE: A single slash ('/') is not addressed by the gitignore
			# documentation. Git treats it as a no-op (does not match any files). The
			# straight forward interpretation is to treat it as '**' to match every
			# file. Remove the directory pattern flag so that it normalizes to '**'
			# instead of '**/'.
			is_dir_pattern = False

		# Normalize pattern to make processing easier.

		if not pattern_segs[0]:
			# A pattern beginning with a slash ('/') should match relative to the root
			# directory. Remove the empty first segment to make the pattern relative
			# to root.
			del pattern_segs[0]

		elif len(pattern_segs) == 1 or (len(pattern_segs) == 2 and not pattern_segs[1]):
			# A single segment pattern with or without a trailing slash ('/') will
			# match any descendant path. This is equivalent to "**/{pattern}". Prepend
			# double-asterisk segment to make pattern relative to root.
			if pattern_segs[0] != '**':
				pattern_segs.insert(0, '**')

		else:
			# A pattern without a beginning slash ('/') but contains at least one
			# prepended directory (e.g., "dir/{pattern}") should match relative to the
			# root directory. No segment modification is needed.
			pass

		if not pattern_segs:
			# After normalization, we end up with no pattern at all. This must be
			# because the pattern is invalid.
			raise GitIgnorePatternError(f"Invalid git pattern: {original_pattern!r}")

		if not pattern_segs[-1] and (len(pattern_segs) < 2 or pattern_segs[-2] != '**'):
			# A pattern ending with a slash ('/') will match all descendant paths if
			# it is a directory but not if it is a regular file. This is equivalent
			# to "{pattern}/**". Set empty last segment to a double-asterisk to
			# include all descendants.
			pattern_segs[-1] = '**'

		# EDGE CASE: Collapse duplicate double-asterisk sequences (i.e., '**/**').
		# Iterate over the segments in reverse and remove the duplicate double
		# asterisks as we go.
		for i in range(len(pattern_segs) - 1, 0, -1):
			prev = pattern_segs[i-1]
			seg = pattern_segs[i]
			if prev == '**' and seg == '**':
				del pattern_segs[i]

		if override_regex is None:
			seg_count = len(pattern_segs)
			if seg_count == 1 and pattern_segs[0] == '**':
				if is_dir_pattern:
					# The pattern "**/" will be normalized to "**", but it should match
					# everything except for files in the root. Special case this pattern.
					override_regex = '/'
				else:
					# The pattern "**" will match every path. Special case this pattern.
					override_regex = '.'

			elif (
				seg_count == 2
				and pattern_segs[0] == '**'
				and pattern_segs[1] == '*'
			):
				# The pattern "*" will be normalized to "**/*" and will match every
				# path. Special case this pattern for efficiency.
				override_regex = '.'

			elif (
				seg_count == 3
				and pattern_segs[0] == '**'
				and pattern_segs[1] == '*'
				and pattern_segs[2] == '**'
			):
				# The pattern "*/" will be normalized to "**/*/**" which will match
				# every file not in the root directory. Special case this pattern for
				# efficiency.
				override_regex = '/'

		if override_regex is None:
			# Build regular expression from pattern.
			output = []
			need_slash = False
			end = len(pattern_segs) - 1
			for i, seg in enumerate(pattern_segs):
				if seg == '**':
					if i == 0:
						# A normalized pattern beginning with double-asterisks ('**') will
						# match any leading path segments.
						output.append('^(?:.+/)?')

					elif i < end:
						# A pattern with inner double-asterisks ('**') will match multiple
						# (or zero) inner path segments.
						output.append('(?:/.+)?')
						need_slash = True

					else:
						assert i == end, (i, end)
						# A normalized pattern ending with double-asterisks ('**') will
						# match any trailing path segments.
						output.append('/')

				else:
					# Match path segment.
					if i == 0:
						# Anchor to root directory.
						output.append('^')

					if need_slash:
						output.append('/')

					if seg == '*':
						# Match whole path segment.
						output.append('[^/]+')

					else:
						# Match segment glob pattern.
						try:
							output.append(cls._translate_segment_glob(seg))
						except ValueError as e:
							raise GitIgnorePatternError(f"Invalid git pattern: {original_pattern!r}") from e

					if i == end:
						if seg == '*':
							# A pattern ending with an asterisk ('*') will match a file or
							# directory (without matching descendant paths). E.g., "foo/*"
							# matches "foo/test.json", "foo/bar/", but not "foo/bar/hello.c".
							output.append('/?$')

						else:
							# A pattern ending without a slash ('/') will match a file or a
							# directory (with paths underneath it). E.g., "foo" matches "foo",
							# "foo/bar", "foo/bar/baz", etc.
							output.append('(?:/|$)')

					need_slash = True

			regex = ''.join(output)

		else:
			# Use regex override.
			regex = override_regex

		# Encode regex if needed.
		out_regex: AnyStr
		if regex is not None and return_type is bytes:
			out_regex = regex.encode(_BYTES_ENCODING)
		else:
			out_regex = regex

		return (out_regex, include)


# Register GitIgnoreBasicPattern as "gitignore".
util.register_pattern('gitignore', GitIgnoreBasicPattern)
