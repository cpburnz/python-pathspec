# encoding: utf-8
"""
This script tests utility functions.
"""

import os
import os.path
import shutil
import tempfile
import unittest

from pathspec.util import iter_tree, RecursionError

class IterTreeTest(unittest.TestCase):
	"""
	The ``IterTreeTest`` class tests `pathspec.util.iter_tree()`.
	"""

	def make_dirs(self, dirs):
		"""
		Create the specified directories.
		"""
		for dir in dirs:
			os.mkdir(os.path.join(self.temp_dir, self.ospath(dir)))

	def make_files(self, files):
		"""
		Create the specified files.
		"""
		for file in files:
			self.mkfile(os.path.join(self.temp_dir, self.ospath(file)))

	def make_links(self, links):
		"""
		Create the specified links.
		"""
		for link, node in links:
			os.symlink(os.path.join(self.temp_dir, self.ospath(node)), os.path.join(self.temp_dir, self.ospath(link)))

	@staticmethod
	def mkfile(file):
		"""
		Creates an empty file.
		"""
		with open(file, 'wb'):
			pass

	@staticmethod
	def ospath(path):
		"""
		Convert the POSIX path to a native OS path.
		"""
		return os.path.join(*path.split('/'))

	def setUp(self):
		"""
		Called before each test.
		"""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""
		Called after each test.
		"""
		shutil.rmtree(self.temp_dir)

	def test_01_files(self):
		"""
		Tests to make sure all files are found.
		"""
		self.make_dirs([
			'Empty',
			'Dir',
			'Dir/Inner',
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
			'Dir/Inner/e',
			'Dir/Inner/f',
		])
		results = set(iter_tree(self.temp_dir))
		self.assertEqual(results, {
			'a',
			'b',
			'Dir/c',
			'Dir/d',
			'Dir/Inner/e',
			'Dir/Inner/f',
		})

	def test_02_links(self):
		"""
		Tests to make sure links to directories and files work.
		"""
		self.make_dirs([
			'Dir'
		])
		self.make_files([
			'a',
			'b',
			'Dir/c',
			'Dir/d',
		])
		self.make_links([
			('ax', 'a'),
			('bx', 'b'),
			('Dir/cx', 'Dir/c'),
			('Dir/dx', 'Dir/d'),
		])
		results = set(iter_tree(self.temp_dir))
		self.assertEqual(results, {
			'a',
			'ax',
			'b',
			'bx',
			'Dir/c',
			'Dir/cx',
			'Dir/d',
			'Dir/dx',
		})

	def test_03_sideways_links(self):
		"""
		Tests to make sure the same directory can be encountered multiple
		times via links.
		"""
		self.make_dirs([
			'Dir',
			'Dir/Target',
		])
		self.make_files([
			'Dir/Target/file',
		])
		self.make_links([
			('Ax', 'Dir'),
			('Bx', 'Dir'),
			('Cx', 'Dir/Target'),
			('Dx', 'Dir/Target'),
			('Dir/Ex', 'Dir/Target'),
			('Dir/Fx', 'Dir/Target'),
		])
		results = set(iter_tree(self.temp_dir))
		self.assertEqual(results, {
			'Ax/Ex/file',
			'Ax/Fx/file',
			'Ax/Target/file',
			'Bx/Ex/file',
			'Bx/Fx/file',
			'Bx/Target/file',
			'Cx/file',
			'Dx/file',
			'Dir/Ex/file',
			'Dir/Fx/file',
			'Dir/Target/file',
		})

	def test_04_recursive_links(self):
		self.make_dirs([
			'Dir',
		])
		self.make_files([
			'Dir/file',
		])
		self.make_links([
			('Dir/Self', 'Dir'),
		])
		with self.assertRaises(RecursionError) as context:
			set(iter_tree(self.temp_dir))
		self.assertEqual(context.exception.first_path, 'Dir')
		self.assertEqual(context.exception.second_path, self.ospath('Dir/Self'))

	def test_05_recursive_circular_links(self):
		self.make_dirs([
			'A',
			'B',
			'C',
		])
		self.make_files([
			'A/d',
			'B/e',
			'C/f'
		])
		self.make_links([
			('A/Bx', 'B'),
			('B/Cx', 'C'),
			('C/Ax', 'A'),
		])
		with self.assertRaises(RecursionError) as context:
			set(iter_tree(self.temp_dir))
		self.assertIn(context.exception.first_path, ('A', 'B', 'C'))
		self.assertEqual(context.exception.second_path, {
			'A': self.ospath('A/Bx/Cx/Ax'),
			'B': self.ospath('B/Cx/Ax/Bx'),
			'C': self.ospath('C/Ax/Bx/Cx'),
		}[context.exception.first_path])
