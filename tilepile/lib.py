
from __future__ import print_function
import traceback

"""frequently used methods and techniques"""
"""signal implementation from codeRecipe 576477"""


class GeneralExecutionManager(object):
	"""placeholder"""
	def __init__(self, real):
		self.real = real

	@staticmethod
	def printTraceback(tb_type, tb_val, tb):
		traceback.print_exception(tb_type, tb_val, tb)

