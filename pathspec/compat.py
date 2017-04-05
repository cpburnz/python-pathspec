# encoding: utf-8
"""
This module provides compatibility between Python 2 and 3. Hardly
anything is used by this project to constitute including `six`_.

.. _`six`: http://pythonhosted.org/six
"""

import sys

if sys.version_info[0] < 3:
	# Python 2.
	string_types = (basestring,)

	from itertools import izip_longest

	def viewkeys(mapping):
		return mapping.viewkeys()

else:
	# Python 3.
	string_types = (str,)

	from itertools import zip_longest as izip_longest

	def viewkeys(mapping):
		return mapping.keys()
