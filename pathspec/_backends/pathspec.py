"""
This module provides backend utility functions used by :class:`~pathspec.pathspec.PathSpec`.

WARNING: The *pathspec._backends* package is not part of the public API. Its
contents and structure are likely to change.
"""

from collections.abc import (
	Iterable)
from typing import (
	Literal,
	cast)

from ..pattern import (
	Pattern,
	RegexPattern)

from .base import (
	Backend)
from .hyperscan.pathspec import (
	HyperscanPsBackend)
from .simple.pathspec import (
	SimplePsBackend)
from ._utils import (
	get_best_backend)


def make_backend(
	name: Literal['best', 'hyperscan', 'simple'],
	patterns: Iterable[Pattern],
) -> Backend:
	"""
	Create the specified backend with the supplied patterns.

	*name* (:class:`str`) is the name of the backend.

	*patterns* (:class:`.Iterable` of :class:`.Pattern`) contains the compiled
	patterns.

	Returns the backend (:class:`.Backend`).
	"""
	if name == 'best':
		name = get_best_backend()

	if name == 'hyperscan':
		return HyperscanPsBackend(cast(Iterable[RegexPattern], patterns))
	elif name == 'simple':
		return SimplePsBackend(patterns)
	else:
		raise ValueError(f"Backend {name=!r} is invalid.")
