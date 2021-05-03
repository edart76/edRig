
from edRig.lib.python import Decorator

class UiTool(Decorator):
	"""base decorator class for functions
	to be assigned ui buttons"""

	def __init__(self, func, header="main", *args, **kwargs):
		super(UiTool, self).__init__(func, *args, **kwargs)
		self.header = header

	def __call__(self, *args, **kwargs):
		return self.func(*args, **kwargs)

