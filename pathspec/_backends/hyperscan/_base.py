"""
This module provides private data for the base implementation for the
:module:`hyperscan` library.

WARNING: The *pathspec._backends.hyperscan* package is not part of the public
API. Its contents and structure are likely to change.
"""
from __future__ import annotations

from dataclasses import (
	dataclass)


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
