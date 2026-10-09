"""
This module provides private data for the base implementation for the
:module:`hyperscan` library.

WARNING: The *pathspec._backends.hyperscan* package is not part of the public
API. Its contents and structure are likely to change.
"""
from __future__ import annotations

import re
from dataclasses import (
	dataclass)
from typing import (
	Union)  # Replaced by `X | Y` in 3.10.

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None  # type: ignore[assignment]
	HS_FLAGS = 0
	HS_VERSION = (-1, -1, -1)
else:
	HS_FLAGS = hyperscan.HS_FLAG_SINGLEMATCH | hyperscan.HS_FLAG_UTF8
	HS_VERSION = tuple(map(int, hyperscan.__version__.split('.')[:3]))

_COMPAT_CONVERT_UNICODE = re.compile(r'\\(.)|([^\x00-\x7F])', re.DOTALL)
"""
Regex to match non-ASCII characters, and escaped characters.
"""

HS_FLAGS: int  # type: ignore[no-redef]
"""
The hyperscan flags to use:

-	HS_FLAG_SINGLEMATCH is needed to ensure the partial patterns only match once.

-	HS_FLAG_UTF8 is required to support unicode paths.
"""

HS_VERSION: tuple[int, int, int]  # type: ignore[no-redef]
"""
The hyperscan version tuple.
"""

HS_VERSION_0_9_1 = (0, 9, 1)
"""
The hyperscan version tuple for version 0.9.1.
"""


def compat_convert_utf8(regex: str) -> bytes:
	"""
	Encode unicode characters to an encoded representation. This is needed because
	hyperscan versions before 0.9.1 on Linux fail on multibyte UTF-8 characters.

	See <https://github.com/darvid/python-hyperscan/issues/274>.

	*regex* (:class:`str`) is the unicode regex.

	Returns the ASCII regex (:class:`bytes`).
	"""
	return _COMPAT_CONVERT_UNICODE.sub(_replace_unicode, regex).encode('ascii')


def _encode_uchar(uchar: str) -> str:
	"""
	Encode the unicode character.

	*uchar* (:class:`str`) is the unicode character.

	Returns the encoded string (:class:`str`).
	"""
	cp = ord(uchar)
	if cp <= 0xFF:
		return f'\\x{{{cp:02X}}}'
	else:
		return f'\\x{{{cp:04X}}}'


def _replace_unicode(match: re.Match) -> str:
	"""
	Replaces the matched unicode character with an encoded representation, handling
	potential invalid byte sequences gracefully by substituting them with the
	replacement character.

	*match* (:class:`re.Match`) is the match object.

	Returns the string replacement (:class:`str`).
	"""
	escaped, uchar = match.groups()  # type: str
	if uchar is not None:
		# Unicode character.
		return _encode_uchar(uchar)
	elif escaped.isascii():
		# Escaped ASCII character.
		return match[0]
	else:
		# Escaped unicode character.
		return _encode_uchar(escaped)


@dataclass(frozen=True)
class HyperscanExprDat(object):
	"""
	The :class:`HyperscanExprDat` class is used to store data related to an
	expression.
	"""

	# The slots argument is not supported until Python 3.10.
	__slots__ = [
		'include',
		'index',
		'is_dir_pattern',
	]

	include: bool
	"""
	*include* (:class:`bool`) is whether is whether the matched files should be
	included (:data:`True`), or excluded (:data:`False`).
	"""

	index: int
	"""
	*index* (:class:`int`) is the pattern index.
	"""

	is_dir_pattern: bool
	"""
	*is_dir_pattern* (:class:`bool`) is whether the pattern is a directory
	pattern for gitignore.
	"""


@dataclass(frozen=True)
class HyperscanExprDebug(HyperscanExprDat):
	"""
	The :class:`HyperscanExprDebug` class stores additional debug information
	related to an expression.
	"""

	# The slots argument is not supported until Python 3.10.
	__slots__ = ['regex']

	regex: Union[str, bytes]
	"""
	*regex* (:class:`str` or :class:`bytes`) is the regular expression.
	"""
