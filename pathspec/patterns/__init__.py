"""
The *pathspec.patterns* package contains the pattern matching implementations.
"""

# Load pattern implementations.
from .gitignore import basic as _
from .gitignore import spec as _

# DEPRECATED: Expose the GitWildMatchPattern class in this module for backward
# compatibility with v0.5.
from .gitwildmatch import GitWildMatchPattern
