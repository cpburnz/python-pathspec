"""
The *pathspec* package provides pattern matching for file paths. So far this
only includes Git's *gitignore* patterns.

The following classes are exposed from the root of the `pathspec` package:

-	:class:`pathspec.gitignore.GitIgnoreSpec`

-	:class:`pathspec.pathspec.PathSpec`

-	:class:`pathspec.pattern.Pattern`

-	:class:`pathspec.pattern.RegexPattern`

-	:class:`pathspec.util.RecursivePathError`

The following functions are also exposed:

-	:func:`pathspec.util.lookup_pattern`

The following deprecated classes are exposed to maintain backward
compatibility:

-	`pathspec.util.RecursionError`

The following deprecated functions are also exposed to maintain backward
compatibility:

-	:func:`pathspec.util.iter_tree`

-	:func:`pathspec.util.match_files`
"""

import warnings

from .gitignore import (
	GitIgnoreSpec)
from .pathspec import (
	PathSpec)
from .pattern import (
	Pattern,
	RegexPattern)
from .util import (
	RecursivePathError,
	iter_tree,  # Deprecated since 0.10.0.
	lookup_pattern,
	match_files)  # Deprecated since 0.10.0.

from ._meta import (
	__author__,
	__copyright__,
	__credits__,
	__license__)
from ._version import (
	__version__)

# Load pattern implementations.
from . import patterns

# Declare private imports as part of the public interface. Deprecated imports
# are deliberately excluded.
__all__ = [
	'GitIgnoreSpec',
	'PathSpec',
	'Pattern',
	'RecursivePathError',
	'RegexPattern',
	'__author__',
	'__copyright__',
	'__credits__',
	'__license__',
	'__version__',
	'lookup_pattern',
]


def __getattr__(name: str):
	"""
	Look up a deprecated module-level attribute.
	"""
	if name == 'RecursionError':
		# Deprecated since 1.2.0. It conflicts with Python 3.5's built-in
		# RecursionError.
		warnings.warn((
			"pathspec.util.RecursionError is deprecated, use RecursivePathError "
			"instead."
		), DeprecationWarning, stacklevel=2)
		return RecursivePathError

	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
