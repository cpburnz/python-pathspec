
Upgrade Guide
=============


From 0.12.0 to 1.0.0
--------------------

`PathSpec`:

- The "gitwildmatch" pattern has been replaced by "gitignore". Use ``PathSpec.from_lines('gitignore', ...)`` instead of ``PathSpec.from_lines('gitwildmatch', ...)``.

`PathSpec.from_lines('gitignore', ...)`:

- Patterns of the form "``foo/*``" will no longer match files in subdirectories. "``foo/test.json``" will match, but "``foo/bar/hello.c``" will no longer match. `GitIgnoreSpec` will continue to match those files. See `Issue #95`_.
- The exact pattern "``/``" will now match every file (equivalent to "``**``"). `GitIgnoreSpec` will continue to discard this pattern.

`PathSpec.from_lines('gitwildmatch', ...)`:

- "gitwildmatch" patterns are deprecated and will be removed in a future version.
- Its behavior is unchanged and does not have the changes documented above for "gitignore" patterns.
- To maintain this exact behavior, `GitIgnoreSpecPattern` can be used, though this use is discouraged because it's a hybrid between Git's behavior and the `gitignore`_ docs.

`GitIgnoreSpec`:

- No changes.

`GitWildMatchPattern`:

- This class is deprecated and will be removed in a future version.
- This has been split into `pathspec.patterns.gitignore.basic.GitIgnoreBasicPattern` and `pathspec.patterns.gitignore.spec.GitIgnoreSpecPattern`. `GitIgnoreSpecPattern` is the unchanged implementation. `GitIgnoreBasicPattern` has the changes documented above for "gitignore".

`GitWildMatchPatternError`:

- This class is deprecated and will be removed in a future version.
- This has been renamed to `pathspec.patterns.gitignore.GitIgnorePatternError`.


.. _`Issue #95`: https://github.com/cpburnz/python-pathspec/issues/95
.. _`gitignore`: https://git-scm.com/docs/gitignore
