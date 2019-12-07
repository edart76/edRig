from collections import deque, OrderedDict

from edRig.lib.python import AbstractTree

""" so it turns out this is really hard """

class Transformation(object):
	""" any mapping which modifies, or transforms,
	a base state, returning the product of
	base and transformation"""

	OBJ_CLASS = None

	def __init__(self, obj):
		self._obj = obj

	def transformed(self):
		""" :returns result of transformation on object
		:rtype : self.OBJ_CLASS"""
		raise NotImplementedError

	def __getattr__(self, item):
		return self._obj.__getattr__(item)

class Delta(Transformation):

	def __init__(self, obj):
		super(Delta, self).__init__(obj)
		self.mask = {
			"added" : {},
			"modified" : {},
			"removed" : {}
		}

	@property
	def obj(self):
		""" defines type of returned object """
		return self._obj


class ListDelta(Delta):
	""" at some point maybe refit this to abstractTree as well"""
	OBJ_CLASS = list

	def transformed(self):
		""" is a list just a map with indices as keys?"""

	@property
	def obj(self):
		""":rtype list"""
		return super(ListDelta, self).obj or []

	def append(self, item):
		pass

	pass


class DictDelta(Delta):
	OBJ_CLASS = dict

	def transformed(self):
		"""construct a new dict for return, don't try to
		frankenstein the same bound object
		all other dict methods are overridden anyway
		:rtype dict"""

		tfData = { k : v for k, v in self.obj.iteritems()}
		for i in self.mask["removed"]:
			tfData.pop(i)
		for k, v in self.mask["added"].iteritems():
			tfData[k] = v
		for k, v in self.mask["modified"].iteritems():
			tfData[k] = v
		""" here addition and modification are the same - 
		is that true everywhere? """
		return tfData


		pass

	@property
	def obj(self):
		""":rtype dict"""
		return super(DictDelta, self).obj or {}

class AbstractTreeDelta(DictDelta):
	OBJ_CLASS = AbstractTree
	pass

class OrderedDictDelta(DictDelta):
	OBJ_CLASS = OrderedDict
	pass


DELTA_CLASSES = {
	list : ListDelta,
	dict : DictDelta,
	AbstractTree : AbstractTreeDelta,
	OrderedDict : OrderedDictDelta
}




# class DeltaStack(object):
# 	"""experimental system of keeping track of successive differences in
# 	a system's state
# 	may end up forming backbone of inheritance system"""
# 	def __init__(self, baseState=None):
# 		#self._stack = []
# 		self._stack = deque()
# 		self._index = 0 # represents current level within deltas - usually latest
# 		self.baseState = baseState
# 		"""stack may contain mix of stackItems and other DeltaStacks -
# 		all that matters is the order"""
# 		pass
#
# 	@property
# 	def stack(self):
# 		return self._stack
# 	@stack.setter
# 	def stack(self, val):
# 		self._stack = val
#
# 	@property
# 	def index(self): # don't use this yet
# 		raise NotImplementedError()
# 		#return self._index
# 	@property
# 	def endIndex(self):
# 		return len(self.stack) - 1
# 	@property
# 	def topDelta(self):
# 		return self.stack[self.endIndex]
#
# 	@property
# 	def childDeltas(self):
# 		return [i for i in self.stack if isinstance(i, DeltaStack)]
#
# 	def setBaseState(self, state):
# 		"""how abstract can we keep this?"""
# 		self.stack = deque()
# 		self.baseState = state
#
# 	def extend(self, delta):
# 		self.stack.append(delta)
#
# 	def reduce(self):
# 		return self.stack.pop()
#
# 	"""add support for walking between delta levels later if necessary - assume
# 	that combined delta stack is always representative of system"""
# 	def undo(self):
# 		"""return system to previous level"""
# 		self.topDelta.undo()
# 		self.reduce()
#
# 	def sum(self):
# 		"""?????
# 		apply all deltas sequentially i guess"""
#
# 	def transformedState(self):
# 		"""more explicit than above"""
# 		return self.sum()
#
# 	def __getattr__(self, item):
# 		pass
#
# 	def __setattr__(self, key, value):
# 		"""creates a new delta"""
#
# 		# parse key somehow to find proper level to assign delta
#
# 		# create delta by comparing current state with assigned state
# 		delta = self.createDelta(before=self.transformedState(),
# 		                  after=self.makeState(value))
# 		self.stack.append(delta)
#
# 		pass
#
# 	# saving
# 	def serialise(self):
# 		pass
#
# 	@staticmethod
# 	def fromDict(regenDict):
# 		pass
#
#
# 	# ----
# 	# methods for stack creation
# 	@staticmethod
# 	def trackObject(target):
# 		"""returns new DeltaStack with object as live base state"""
# 		return DeltaStack(baseState=target)
#
#
# class StackDelta(object):
# 	"""atomic class representing a modification to a system"""
# 	operations = ["addition", "subtraction", "modification"] # only one
# 	"""should only hold, apply and undo deltas - no knowledge of base state
# 	or anything outside changes it represents"""
#
# 	def __init__(self, operation):
# 		if not operation in self.operations:
# 			raise RuntimeError("invalid StackDelta operation " + operation)
# 		self.operation = operation
#
# 	def undo(self):
# 		"""called to remove delta from system"""
# 		raise NotImplementedError()
#


"""test case let's go


class Test(object):
	
	def __init__:
		self.A = 5
		self.B = "this is test"
		
newTest = Test()
stack = DeltaStack.trackObject(newTest)

- this will return a deltaStack with newTest as its base
this will be a top-level wrapper around newTest - any modification 
of stack's attributes will be a modification delta

eg

stack.C = "newAttr"
is an object-level modification, comprised of an attribute-level addition

does not add the attribute to stack. compares previous transformedState of stack -
this is treated as a dict for sanity - see if it contains C.

if it does, then object level is NOT MODIFIED - no object level delta is created
attribute lookup ten returns an inner stack, which handles it further.

if it doesn't, an addition delta is created at object level to add the attribute
AS NEW STACK with base state None - 
object level contains no knowledge of attribute's value

for convenience, register attribute value as stack base state. don't think it
matters, but helps for determining delta type etc

new stack processes attribute value, creates child stacks if necessary
(if need to tokenise string, etc)




is it worth returning a new deltastack around this attribute, as it has
 no base state? would only allow for undo operations
 
stack.B = "this is new test"
more interesting.

compare the source state and the target state

is it worth tracking from the top down like this? surely bottom up would
make more sense





accessing object must apply all relevant modifications

















"""

