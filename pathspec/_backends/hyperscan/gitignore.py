"""
This module provides the :module:`hyperscan` backend for :class:`~pathspec.gitignore.GitIgnoreSpec`.

WARNING: The *pathspec._backends.hyperscan* package is not part of the public
API. Its contents and structure are likely to change.
"""
from __future__ import annotations

try:
	import hyperscan
except ModuleNotFoundError:
	hyperscan = None

from .base import (
	hyperscan_error)
