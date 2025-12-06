"""
This module implements Git's `gitignore`_ patterns, and handles edge-cases where
Git's behavior differs from what's documented. Git allows including files from
excluded directories which appears to contradict the documentation. This is used by
:class:`pathspec.gitignore.GitIgnoreSpec` to fully replicate Git's handling.

.. _`gitignore`: https://git-scm.com/docs/gitignore
"""

from typing import (
	AnyStr,
	Optional)  # Replaced by `X | None` in 3.10.

from pathspec import (
	util)
from pathspec._typing import (
	override)  # Added in 3.12.

from .base import (
	_BYTES_ENCODING,
	_GitIgnoreBasePattern,
	GitIgnorePatternError)

_DIR_MARK = 'ps_d'
"""
The regex group name for the directory marker. This is only used by
:class:`GitIgnoreSpec`.
"""

_DIR_MARK_CG = f'(?P<{_DIR_MARK}>/)'
"""
This regular expression matches the directory marker.
"""

_DIR_MARK_OPT = f'(?:{_DIR_MARK_CG}|$)'
"""
This regular expression matches the optional directory marker and sub-path.
"""


class GitIgnoreSpecPattern(_GitIgnoreBasePattern):
	"""
	The :class:`GitIgnoreSpecPattern` class represents a compiled gitignore
	pattern with special handling for edge-cases to replicate Git's behavior.
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

		if pattern_str.startswith('#'):
			# A pattern starting with a hash ('#') serves as a comment (neither
			# includes nor excludes files). Escape the hash with a backslash to match
			# a literal hash (i.e., '\#').
			regex = None
			include = None

		elif pattern_str == '/':
			# EDGE CASE: According to `git check-ignore` (v2.4.1), a single '/' does
			# not match any file.
			regex = None
			include = None

		elif pattern_str:
			if pattern_str.startswith('!'):
				# A pattern starting with an exclamation mark ('!') negates the pattern
				# (exclude instead of include). Escape the exclamation mark with a
				# back-slash to match a literal exclamation mark (i.e., '\!').
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

			# Normalize pattern to make processing easier.

			# EDGE CASE: Deal with duplicate double-asterisk sequences. Collapse each
			# sequence down to one double-asterisk. Iterate over the segments in
			# reverse and remove the duplicate double asterisks as we go.
			for i in range(len(pattern_segs) - 1, 0, -1):
				prev = pattern_segs[i-1]
				seg = pattern_segs[i]
				if prev == '**' and seg == '**':
					del pattern_segs[i]

			if len(pattern_segs) == 2 and pattern_segs[0] == '**' and not pattern_segs[1]:
				# EDGE CASE: The '**/' pattern should match everything except individual
				# files in the root directory. This case cannot be adequately handled
				# through normalization. Use the override.
				override_regex = _DIR_MARK_CG

			if not pattern_segs[0]:
				# A pattern beginning with a slash ('/') should match relative to the
				# root directory. Remove the empty first segment to make the pattern
				# relative to root.
				del pattern_segs[0]

			elif len(pattern_segs) == 1 or (len(pattern_segs) == 2 and not pattern_segs[1]):
				# A single segment pattern with or without a trailing slash ('/') will
				# match any descendant path. This is equivalent to "**/{pattern}".
				# Prepend double-asterisk segment to make pattern relative to root.
				if pattern_segs[0] != '**':
					pattern_segs.insert(0, '**')

			else:
				# A pattern without a beginning slash ('/') but contains at least one
				# prepended directory (e.g., "dir/{pattern}") should match relative to
				# the root directory. No segment modification is needed.
				pass

			if not pattern_segs:
				# After resolving the edge cases, we end up with no pattern at all. This
				# must be because the pattern is invalid.
				raise GitIgnorePatternError(f"Invalid git pattern: {original_pattern!r}")

			if not pattern_segs[-1]:
				# A pattern ending with a slash ('/') will match all descendant paths if
				# it is a directory but not if it is a regular file. This is equivalent
				# to "{pattern}/**". Set empty last segment to a double-asterisk to
				# include all descendants.
				pattern_segs[-1] = '**'

			if override_regex is None:
				seg_count = len(pattern_segs)
				if seg_count == 1 and pattern_segs[0] == '**':
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
					if is_dir_pattern:
						override_regex = _DIR_MARK_CG
					else:
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
							if is_dir_pattern:
								output.append(_DIR_MARK_CG)
							else:
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
							# A pattern ending without a slash ('/') will match a file or a
							# directory (with paths underneath it). E.g., "foo" matches "foo",
							# "foo/bar", "foo/bar/baz", etc.
							output.append(_DIR_MARK_OPT)

						need_slash = True

				regex = ''.join(output)

			else:
				# Use regex override.
				regex = override_regex

		else:
			# A blank pattern is a null-operation (neither includes nor excludes
			# files).
			regex = None
			include = None

		# Encode regex if needed.
		out_regex: AnyStr
		if regex is not None and return_type is bytes:
			out_regex = regex.encode(_BYTES_ENCODING)
		else:
			out_regex = regex

		return (out_regex, include)


util.register_pattern('gitignore-spec', GitIgnoreSpecPattern)
