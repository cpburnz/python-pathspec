"""
This module provides stubs for type hints not supported by all relevant Python
versions.

NOTICE: This project should have zero required dependencies which means it
cannot simply require :module:`typing_extensions`, and I do not want to maintain
vendored copy of :module:`typing_extensions`.
"""

from collections.abc import (
	Callable)
from typing import (
	Any,
	TypeVar)

F = TypeVar('F', bound=Callable[..., Any])

try:
	from typing import override
except ImportError:
	def override(f: F) -> F:
		return f
