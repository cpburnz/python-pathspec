"""
The *pathspec* package provides pattern matching for file paths. So far
this only includes Git's wildmatch pattern matching (the style used for
".gitignore" files).

The following classes are imported and made available from the root of
the `pathspec` package:

- :class:`pathspec.gitignore.GitIgnoreSpec`

- :class:`pathspec.pathspec.PathSpec`

- :class:`pathspec.pattern.Pattern`

- :class:`pathspec.pattern.RegexPattern`

- :class:`pathspec.util.RecursionError`

The following functions are also imported:

- :func:`pathspec.util.lookup_pattern`

The following deprecated functions are also imported to maintain
backward compatibility:

- :func:`pathspec.util.iter_tree` which is an alias for
  :func:`pathspec.util.iter_tree_files`.

- :func:`pathspec.util.match_files`
"""

from .gitignore import (
	GitIgnoreSpec as GitIgnoreSpec)
from .pathspec import (
	PathSpec as PathSpec)
from .pattern import (
	Pattern as Pattern,
	RegexPattern as RegexPattern)
from .util import (
	RecursionError as RecursionError,
	iter_tree as iter_tree,
	lookup_pattern as lookup_pattern,
	match_files as match_files)

from ._meta import (
	__author__,
	__copyright__,
	__credits__,
	__license__,
	__version__,
)

# Load pattern implementations.
from . import patterns as patterns

# Expose `GitIgnorePattern` class in the root module for backward
# compatibility with v0.4.
from .patterns.gitwildmatch import GitIgnorePattern as GitIgnorePattern
