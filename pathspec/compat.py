# coding: utf-8
"""
This module provides compatibility between Python 2 and 3. Hardly
anything is used by this project to constitute including `six`_.

.. _`six`: http://pythonhosted.org/six
"""

try:
	string_types = (basestring,)
except NameError:
	string_types = (str,)
