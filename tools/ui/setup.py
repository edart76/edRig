
from edRig.lib.python import Decorator

class UiTool(Decorator):
	"""base decorator class for functions
	to be assigned ui buttons"""

	def __init__(self, func, *args, **kwargs):
		super(UiTool, self).__init__(func, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.func(*args, **kwargs)

