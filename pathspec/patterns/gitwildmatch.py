"""
DEPRECATED: This module only exists for backward compatibility with v0.12.
"""

import warnings

from pathspec import util
from pathspec._typing import (
	override)

from .gitignore.spec import (
	GitIgnoreSpecPattern)

# DEPRECATED: Expose GitWildMatchPatternError in this module for backward
# compatibility with v0.12.
from .gitignore.base import (
	GitIgnorePatternError as GitWildMatchPatternError)


# TODO: Review dvc's usage of this class.
class GitWildMatchPattern(GitIgnoreSpecPattern):
	"""
	The :class:`GitWildMatchPattern` class is deprecated and superseded by
	:class:`.GitIgnoreSpecPattern` and :class:`~pathspec.patterns.gitignore.basic.GitIgnoreBasicPattern`.
	This class only exists to maintain compatibility with v0.12.
	"""

	def __init__(self, *args, **kw) -> None:
		"""
		Warn about deprecation.
		"""
		self._deprecated()
		super(GitWildMatchPattern, self).__init__(*args, **kw)

	@staticmethod
	def _deprecated() -> None:
		"""
		Warn about deprecation.
		"""
		warnings.warn((
			"GitWildMatchPattern ('gitwildmatch') is deprecated. Use 'gitignore' for "
			"GitIgnoreBasicPattern or GitIgnoreSpecPattern instead."
		), DeprecationWarning, stacklevel=3)

	@override
	@classmethod
	def pattern_to_regex(cls, *args, **kw):
		"""
		Warn about deprecation.
		"""
		cls._deprecated()
		return super(GitWildMatchPattern, cls).pattern_to_regex(*args, **kw)


# TODO: In a future version (probably v0.14), register GitWildMatchPattern
# instead so that a deprecation warning will be triggered when using
# "gitwildmatch".
#util.register_pattern('gitwildmatch', GitWildMatchPattern)
