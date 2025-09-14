"""
This module defines matchers used in benchmarking, but not included in the
released library.
"""

from typing import (
	Any,
	Iterable,  # Replaced by `collections.abc.Iterable` in 3.9.
	List,  # Replaced by `list` in 3.9.
	Optional,  # Replaced by `X | None` in 3.10.
	Tuple)  # Replaced by `tuple` in 3.9.

try:
	import hyperscan
	hyperscan_error: Optional[ModuleNotFoundError] = None
except ModuleNotFoundError as e:
	hyperscan = None
	hyperscan_error = e

# TODO: Look into re2 <https://pypi.org/project/google-re2>.

from pathspec.match import (
	Matcher,
	_enumerate_patterns)
from pathspec.pattern import (
	RegexPattern)
from pathspec.patterns.gitwildmatch import (
	_DIR_MARK)


class _HyperscanBlockMatcher(Matcher):
	"""
	The :class:`_HyperscanBlockMatcher` class uses a hyperscan database in block
	mode for matching files.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		"""
		Initialize the :class:`HyperscanMatcher` instance.

		*patterns* (:class:`Iterable` of :class:`.Pattern`) contains the compiled
		patterns.

		*no_reverse* (:class:`bool`) is whether to keep the pattern order
		(:data:`True`), or reverse the order (:data:`True`).
		"""
		if hyperscan is None:
			raise hyperscan_error

		use_patterns = _enumerate_patterns(
			patterns, no_filter=False, no_reverse=True,
		)

		self._db = self.__make_db(use_patterns)
		self._patterns = dict(use_patterns)

	@staticmethod
	def __make_db(patterns: List[Tuple[int, RegexPattern]]) -> hyperscan.Database:
		"""
		Create the hyperscan database from the given patterns.

		*patterns* (:class:`~collections.abc.Sequence` of :class:`.RegexPattern`)
		contains the patterns.

		Returns the database (:class:`hyperscan.Database`).
		"""
		# Create database.
		db = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)

		# Prepare patterns.
		exprs: list[bytes] = []
		ids: list[int] = []
		for i, pattern in patterns:
			if pattern.include is None:
				continue

			assert isinstance(pattern, RegexPattern), pattern
			regex = pattern.regex.pattern

			if isinstance(regex, bytes):
				regex_bytes = regex
			else:
				assert isinstance(regex, str), regex
				regex_bytes = regex.encode('utf8')

			exprs.append(regex_bytes)
			ids.append(i)

		# Compile patterns.
		db.compile(
			expressions=exprs,
			ids=ids,
			elements=len(exprs),
			flags=hyperscan.HS_FLAG_UTF8,
		)
		return db


class HyperscanBlockClosureMatcher(_HyperscanBlockMatcher):
	"""
	The :class:`HyperscanBlockClosureMatcher` class uses a hyperscan database in
	block mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = None

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index
			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
			include = self._patterns[expr_id].include
			if include:
				out_include = include
				out_index = expr_id

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class HyperscanBlockStateMatcher(_HyperscanBlockMatcher):
	"""
	The :class:`HyperscanBlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int]] = (None, None)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None)
		self._db.scan(file.encode('utf8'), match_event_handler=self.__on_match)
		return self.__out

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		include = self._patterns[expr_id].include
		if include:
			self.__out = (include, expr_id)


class _HyperscanStreamMatcher(Matcher):
	"""
	The :class:`_HyperscanStreamMatcher` class uses a hyperscan database in
	streaming mode for matching files.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		if hyperscan is None:
			raise hyperscan_error

		use_patterns = _enumerate_patterns(
			patterns, no_filter=False, no_reverse=False,
		)

		self._db = self.__make_db(use_patterns)
		self._patterns = dict(use_patterns)

	@staticmethod
	def __make_db(patterns: List[Tuple[int, RegexPattern]]) -> hyperscan.Database:
		# Create database.
		db = hyperscan.Database(mode=hyperscan.HS_MODE_STREAM)

		# Prepare patterns.
		exprs: list[bytes] = []
		ids: list[int] = []
		for i, pattern in patterns:
			if pattern.include is None:
				continue

			assert isinstance(pattern, RegexPattern), pattern
			regex = pattern.regex.pattern

			if isinstance(regex, bytes):
				regex_bytes = regex
			else:
				assert isinstance(regex, str), regex
				regex_bytes = regex.encode('utf8')

			exprs.append(regex_bytes)
			ids.append(i)

		# Compile patterns.
		db.compile(
			expressions=exprs,
			ids=ids,
			elements=len(exprs),
			flags=hyperscan.HS_FLAG_UTF8,
		)
		return db


class HyperscanStreamClosureMatcher(_HyperscanStreamMatcher):
	"""
	The :class:`HyperscanStreamClosureMatcher` class uses a hyperscan database in
	streaming mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		out_include = False
		out_index: Optional[int] = None

		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index
			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
			include = self._patterns[expr_id].include
			if include:
				out_include = include
				out_index = expr_id
				return True

			return None

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index


# WARNING: This segfaults.
class HyperscanStreamStateMatcher(_HyperscanStreamMatcher):
	"""
	The :class:`HyperscanStreamVarMatcher` class uses a hyperscan database in
	streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int]] = (None, None)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		self.__out = (None, None)

		with self._db.stream(match_event_handler=self.__on_match) as stream:
			stream.scan(file.encode('utf8'))

		return self.__out

	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		_context: Any,
	) -> Optional[bool]:
		include = self._patterns[expr_id].include
		if include:
			self.__out = (include, expr_id)
			return True
		else:
			return None


class GiHyperscanBlockClosureMatcher(_HyperscanBlockMatcher):
	"""
	The :class:`GiHyperscanBlockClosureMatcher` class uses a hyperscan database
	in block mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
		# run from there.
		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
			pattern = self._patterns[expr_id]
			if pattern.include:
				# Rematch pattern because Hyperscan does not support capture groups.
				match = pattern.match_file(file)

				# Check for directory marker.
				dir_mark = match.match.groupdict().get(_DIR_MARK)

				if dir_mark:
					# Pattern matched by a directory pattern.
					priority = 1
				else:
					# Pattern matched by a file pattern.
					priority = 2

				if pattern.include and dir_mark:
					out_include = pattern.include
					out_index = expr_id
					out_priority = priority
				elif priority >= out_priority:
					out_include = pattern.include
					out_index = expr_id
					out_priority = priority

		self._db.scan(file.encode('utf8'), match_event_handler=on_match)
		return out_include, out_index


class GiHyperscanBlockStateMatcher(_HyperscanBlockMatcher):
	"""
	The :class:`GiHyperscanBlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		self.__out = (None, None, 0)
		self._db.scan(
			file.encode('utf8'), match_event_handler=self.__on_match, context=file,
		)
		return self.__out[:2]

	# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
	# run from there.
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
	) -> Optional[bool]:
		#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
		file: str = context
		pattern = self._patterns[expr_id]
		if pattern.include:
			# Rematch pattern because Hyperscan does not support capture groups.
			match = pattern.match_file(file)

			# Check for directory marker.
			dir_mark = match.match.groupdict().get(_DIR_MARK)

			if dir_mark:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			if pattern.include and dir_mark:
				self.__out = (pattern.include, expr_id, priority)
			elif priority >= self.__out[2]:
				self.__out = (pattern.include, expr_id, priority)


# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
# run from there.
class GiHyperscanBlockStateMatcher2(_HyperscanBlockMatcher):
	"""
	The :class:`GiHyperscanBlockStateMatcher` class uses a hyperscan database in
	block mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		self.__out = (None, None, 0)
		self._db.scan(
			file.encode('utf8'), match_event_handler=self.__on_match, context=file,
		)
		return self.__out[:2]

	# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
	# run from there.
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
	) -> Optional[bool]:
		#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
		file: str = context
		pattern = self._patterns[expr_id]
		if pattern.include:
			# Rematch pattern because Hyperscan does not support capture groups.
			match = pattern.match_file(file)

			# Check for directory marker.
			dir_mark = match.match.groupdict().get(_DIR_MARK)

			if dir_mark:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			if pattern.include and dir_mark:
				self.__out = (pattern.include, expr_id, priority)
			elif priority >= self.__out[2]:
				self.__out = (pattern.include, expr_id, priority)



class GiHyperscanStreamClosureMatcher(_HyperscanStreamMatcher):
	"""
	The :class:`GiHyperscanStreamClosureMatcher` class uses a hyperscan database
	in streaming mode for matching files, and uses a closure to capture state.
	"""

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		out_include: Optional[bool] = None
		out_index: Optional[int] = None
		out_priority = 0

		# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
		# run from there.
		def on_match(
			expr_id: int, _from: int, _to: int, _flags: int, _context: Any,
		) -> Optional[bool]:
			nonlocal out_include, out_index, out_priority
			#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
			pattern = self._patterns[expr_id]
			if pattern.include:
				# Rematch pattern because Hyperscan does not support capture groups.
				match = pattern.match_file(file)

				# Check for directory marker.
				dir_mark = match.match.groupdict().get(_DIR_MARK)

				if dir_mark:
					# Pattern matched by a directory pattern.
					priority = 1
				else:
					# Pattern matched by a file pattern.
					priority = 2

				if pattern.include and dir_mark:
					out_include = pattern.include
					out_index = expr_id
					out_priority = priority
				elif priority >= out_priority:
					out_include = pattern.include
					out_index = expr_id
					out_priority = priority

				if priority == 2:
					# Patterns are being checked in reverse order. The first pattern that
					# matches with the highest priority takes precedence.
					return True

		with self._db.stream(match_event_handler=on_match) as stream:
			stream.scan(file.encode('utf8'))

		return out_include, out_index


# WARNING: This segfaults.
class GiHyperscanStreamStateMatcher(_HyperscanStreamMatcher):
	"""
	The :class:`GiHyperscanStreamStateMatcher` class uses a hyperscan database in
	streaming mode for matching files, and stores state in variables.
	"""

	def __init__(self, patterns: Iterable[RegexPattern]) -> None:
		super().__init__(patterns)
		self.__out: Tuple[Optional[bool], Optional[int], Optional[int]] = (None, None, 0)

	def match_file(self, file: str) -> Tuple[Optional[bool], Optional[int]]:
		"""
		Check the file against the patterns.

		*file* (:class:`str`) is the normalized file path to check.

		Returns a :class:`tuple` containing whether to include *file* (:class:`bool`
		or :data:`None`), and the index of the last matched pattern (:class:`int` or
		:data:`None`).
		"""
		self.__out = (None, None, 0)
		with self._db.stream(match_event_handler=self.__on_match, context=file) as stream:
			stream.scan(file.encode('utf8'))

		return self.__out[:2]

	# TODO Idea: Generate dir-mark and non-dir-mark regexes for hyperscan, and
	# run from there.
	def __on_match(
		self,
		expr_id: int,
		_from: int,
		_to: int,
		_flags: int,
		context: Any,
	) -> Optional[bool]:
		#print(f"[{context}] {expr_id} {include}: {patterns[expr_id].pattern!r}")
		file: str = context
		pattern = self._patterns[expr_id]
		if pattern.include:
			# Rematch pattern because Hyperscan does not support capture groups.
			match = pattern.match_file(file)

			# Check for directory marker.
			dir_mark = match.match.groupdict().get(_DIR_MARK)

			if dir_mark:
				# Pattern matched by a directory pattern.
				priority = 1
			else:
				# Pattern matched by a file pattern.
				priority = 2

			if pattern.include and dir_mark:
				self.__out = (pattern.include, expr_id, priority)
			elif priority >= self.__out[2]:
				self.__out = (pattern.include, expr_id, priority)

			if priority == 2:
				# Patterns are being checked in reverse order. The first pattern that
				# matches with the highest priority takes precedence.
				return True
