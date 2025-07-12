
from typing import (
	Iterable,
	Iterator,
	Optional,
	cast)

from pathspec import (
	PathSpec)
from pathspec.pattern import (
	RegexPattern)
from pathspec.util import (
	StrPath,
	_filter_check_patterns,
	_is_iterable,
	normalize_file)


def match_files_v0(
	self: PathSpec,
	files: Iterable[StrPath],
	separators=None,
	*,
	negate=None,
) -> Iterator[StrPath]:
	if not _is_iterable(files):
		raise TypeError(f"files:{files!r} is not an iterable.")

	# TODO: Use a matcher class?
	# - Then test performance.

	if self._PathSpec__db is not None:
		patterns = cast(list[RegexPattern], self.patterns)
		include = False

		def on_match(expr_id: int, _from: int, _to: int, _flags: int, context) -> Optional[bool]:
			nonlocal include
			include = patterns[expr_id].include
			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")

		for orig_file in files:
			include = False
			use_file = orig_file.encode('utf8')
			self._PathSpec__db.scan(use_file, match_event_handler=on_match, context=orig_file)
			if negate:
				include = not include

			if include:
				yield orig_file

		return

	use_patterns = _filter_check_patterns(self.patterns)
	for orig_file in files:
		norm_file = normalize_file(orig_file, separators)
		include, _index = self._match_file(use_patterns, norm_file)

		if negate:
			include = not include

		if include:
			yield orig_file
