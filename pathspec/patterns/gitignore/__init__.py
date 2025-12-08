"""
The *pathspec.patterns.gitignore* package provides the *gitignore*
implementations.
"""

# Expose the GitIgnorePatternError for convenience.
from .base import (
	GitIgnorePatternError)

# Declare private imports as part of the public interface.
__all__ = [
	'GitIgnorePatternError',
]
