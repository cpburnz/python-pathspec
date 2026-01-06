
1.0.0 (2026-01-05)
------------------

Major changes:

- `Issue #91`_: Dropped support of EoL Python 3.8.
- Added concept of backends to allow for faster regular expression matching. The backend can be controlled using the `backend` argument to `PathSpec()`, `PathSpec.from_lines()`, `GitIgnoreSpec()`, and `GitIgnoreSpec.from_lines()`.
- Renamed "gitwildmatch" pattern back to "gitignore". The "gitignore" pattern behaves slightly differently when used with `PathSpec` (*gitignore* as documented) than with `GitIgnoreSpec` (replicates *Git*'s edge cases).

API changes:

- Breaking: protected method `pathspec.pathspec.PathSpec._match_file()` (with a leading underscore) has been removed and replaced by backends. This does not affect normal usage of `PathSpec` or `GitIgnoreSpec`. Only custom subclasses will be affected. If this breaks your usage, let me know by `opening an issue <https://github.com/cpburnz/python-pathspec/issues>`_.
- Deprecated: "gitwildmatch" is now an alias for "gitignore".
- Deprecated: `pathspec.patterns.GitWildMatchPattern` is now an alias for `pathspec.patterns.gitignore.spec.GitIgnoreSpecPattern`.
- Deprecated: `pathspec.patterns.gitwildmatch` module has been replaced by the `pathspec.patterns.gitignore` package.
- Deprecated: `pathspec.patterns.gitwildmatch.GitWildMatchPattern` is now an alias for `pathspec.patterns.gitignore.spec.GitIgnoreSpecPattern`.
- Deprecated: `pathspec.patterns.gitwildmatch.GitWildMatchPatternError` is now an alias for `pathspec.patterns.gitignore.GitIgnorePatternError`.
- Removed: `pathspec.patterns.gitwildmatch.GitIgnorePattern` has been deprecated since v0.4 (2016-07-15).
- Signature of method `pathspec.pattern.RegexPattern.match_file()` has been changed from `def match_file(self, file: str) -> RegexMatchResult | None` to `def match_file(self, file: AnyStr) -> RegexMatchResult | None` to reflect usage.
- Signature of class method `pathspec.pattern.RegexPattern.pattern_to_regex()` has been changed from `def pattern_to_regex(cls, pattern: str) -> tuple[str, bool]` to `def pattern_to_regex(cls, pattern: AnyStr) -> tuple[AnyStr | None, bool | None]` to reflect usage and documentation.

New features:

- Added optional "hyperscan" backend using `hyperscan`_ library. It will automatically be used when installed. This dependency can be installed with ``pip install 'pathspec[hyperscan]'``.
- Added optional "re2" backend using the `google-re2`_ library. It will automatically be used when installed. This dependency can be installed with ``pip install 'pathspec[re2]'``.
- Added optional dependency on `typing-extensions`_ library to improve some type hints.

Bug fixes:

- `Issue #93`_: Do not remove leading spaces.
- `Issue #95`_: Matching for files inside folder does not seem to behave like .gitignore's.
- `Issue #98`_: UnboundLocalError in RegexPattern when initialized with `pattern=None`.
- Type hint on return value of `pathspec.pattern.RegexPattern.match_file()` to match documentation.

Improvements:

- Mark Python 3.13 and 3.14 as supported.
- No-op patterns are now filtered out when matching files, slightly improving performance.
- Fix performance regression in `iter_tree_files()` from v0.10.


.. _`Issue #38`: https://github.com/cpburnz/python-pathspec/issues/38
.. _`Issue #91`: https://github.com/cpburnz/python-pathspec/issues/91
.. _`Issue #93`: https://github.com/cpburnz/python-pathspec/issues/93
.. _`Issue #95`: https://github.com/cpburnz/python-pathspec/issues/95
.. _`Issue #98`: https://github.com/cpburnz/python-pathspec/issues/98
.. _`google-re2`: https://pypi.org/project/google-re2/
.. _`hyperscan`: https://pypi.org/project/hyperscan/
.. _`typing-extensions`: https://pypi.org/project/typing-extensions/
