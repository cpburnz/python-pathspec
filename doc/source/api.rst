:tocdepth: 2

API
===

pathspec
--------

.. automodule:: pathspec


pathspec.pathspec
-----------------

.. automodule:: pathspec.pathspec

	.. autoclass:: PathSpec
		:members:
		:show-inheritance:
		:special-members: __init__, __eq__, __len__


pathspec.gitignore
------------------

.. automodule:: pathspec.gitignore

	.. autoclass:: GitIgnoreSpec
		:members:
		:inherited-members:
		:show-inheritance:
		:special-members: __init__, __eq__


pathspec.pattern
----------------

.. automodule:: pathspec.pattern

	.. autoclass:: Pattern
		:members:
		:show-inheritance:
		:special-members: __init__

	.. autoclass:: RegexPattern
		:members:
		:show-inheritance:
		:special-members: __init__, __eq__

	.. autoclass:: RegexMatchResult
		:members:
		:show-inheritance:
		:special-members: __init__


pathspec.patterns.gitignore
---------------------------

.. automodule:: pathspec.patterns.gitignore


pathspec.patterns.gitignore.base
--------------------------------

.. automodule:: pathspec.patterns.gitignore.base

	.. autoclass:: _GitIgnoreBasePattern
		:show-inheritance:

	.. autoclass:: GitIgnorePatternError
		:members:
		:show-inheritance:


pathspec.patterns.gitignore.basic
---------------------------------

.. automodule:: pathspec.patterns.gitignore.basic

	.. autoclass:: GitIgnoreBasicPattern
		:members:
		:inherited-members:
		:show-inheritance:


pathspec.patterns.gitignore.spec
--------------------------------

.. automodule:: pathspec.patterns.gitignore.spec

	.. autoclass:: GitIgnoreSpecPattern
		:members:
		:inherited-members:
		:show-inheritance:


pathspec.util
-------------

.. automodule:: pathspec.util
	:members:
	:show-inheritance:
