
from __future__ import print_function
import inspect
from weakref import WeakSet, WeakKeyDictionary

"""frequently used methods and techniques"""
"""signal implementation from codeRecipe 576477"""

class Signal(object):
	def __init__(self):
		self._functions = WeakSet()
		self._methods = WeakKeyDictionary()

	def __call__(self, *args, **kargs):
		# Call handler functions
		for func in self._functions:
			func(*args, **kargs)

		# Call handler methods
		for obj, funcs in self._methods.items():
			for func in funcs:
				func(obj, *args, **kargs)

	def connect(self, slot):
		if inspect.ismethod(slot):
			if slot.__self__ not in self._methods:
				self._methods[slot.__self__] = set()

			self._methods[slot.__self__].add(slot.__func__)

		else:
			self._functions.add(slot)

	def disconnect(self, slot):
		if inspect.ismethod(slot):
			if slot.__self__ in self._methods:
				self._methods[slot.__self__].remove(slot.__func__)
		else:
			if slot in self._functions:
				self._functions.remove(slot)

	def clear(self):
		self._functions.clear()
		self._methods.clear()


"""TO-DO: implement context for this to gather deltas procedurally"""
class DeltaStack(object):
	"""experimental system of keeping track of successive differences in
	a system's state
	may end up forming backbone of inheritance system"""
	def __init__(self):
		self._stack = []
		self._index = 0 # represents current level within deltas - usually latest
		self.baseState = None
		"""stack may contain mix of stackItems and other DeltaStacks - 
		all that matters is the order"""
		pass

	@property
	def stack(self):
		return self._stack
	@stack.setter
	def stack(self, val):
		self._stack = val

	@property
	def index(self): # don't use this yet
		raise NotImplementedError()
		#return self._index
	@property
	def endIndex(self):
		return len(self.stack) - 1
	@property
	def topDelta(self):
		return self.stack[self.endIndex]

	@property
	def childDeltas(self):
		return [i for i in self.stack if isinstance(i, DeltaStack)]

	def setBaseState(self, state):
		"""how abstract can we keep this?"""
		self.stack = []
		self.baseState = state

	def extend(self, delta):
		self.stack.append(delta)

	def reduce(self):
		return self.stack.pop(self.endIndex)

	"""add support for walking between delta levels later if necessary - assume
	that combined delta stack is always representative of system"""
	def undo(self):
		"""return system to previous level"""
		self.topDelta.undo()
		self.reduce()

	def sum(self):
		"""?????"""


class StackDelta(object):
	"""atomic class representing a modification to a system"""
	operations = ["addition", "subtraction", "modification"] # only one
	"""should only hold, apply and undo deltas - no knowledge of base state
	or anything outside changes it represents"""

	def __init__(self, operation):
		if not operation in self.operations:
			raise RuntimeError("invalid StackDelta operation " + operation)
		self.operation = operation

	def undo(self):
		"""called to remove delta from system"""
		raise NotImplementedError()


