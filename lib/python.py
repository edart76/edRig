"""general lib for nifty python things like decorators and debugs"""
from __future__ import print_function
import inspect,importlib, pprint
from weakref import WeakSet, WeakKeyDictionary
from collections import OrderedDict



# thank you code recipe 576925
def caller():
	"""whatever called this"""
	return inspect.getouterframes(inspect.currentframe())[1][1:4]
def callee():
	"""this specific function
	:returns (modulePath, line, funcname)"""
	return inspect.getouterframes(inspect.currentframe())[2][1:4]

def debug(var):
	"""prints the name and value of var, in the scope it comes from
	eg a = 23, debug (a) - 'a is 23' """
	callerFrame = inspect.stack()[1][0]
	name = [k for k, v in callerFrame.f_locals.iteritems() if v is var][0]
	print("{} is {}".format(name, pprint.pformat(var)))
	return name # part of me is sad this isn't more crazy

def outerVars():
	"""returns a dict of variable names from the outer scope of the call
	used mainly to add actions to classes because decorators drive me mad"""
	callerFrame = inspect.stack()[1][0]
	return callerFrame.f_locals


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


# move the module import here from pipeline

class AbstractTree(object):
	"""fractal tree-like data structure
	each branch having both name and value"""
	def __init__(self, name, val):
		self.name = name
		self.parent = None
		self._val = val
		# if self.parent:
		# 	self.setParent(parent)
		# else:
		self.valueChanged = Signal()
		self._map = OrderedDict()
		self.extras = {}

	def _setParent(self, tree):
		"""sets new abstractTree to be parent"""
		self.parent = tree
		self.valueChanged = tree.valueChanged
	def addChild(self, branch):
		self._map[branch.name] = branch
		branch._setParent(self)
		return branch

	def get(self, lookup, default):
		"""same implementation as normal dict"""
		return self._map.get(lookup, default)

	def index(self, lookup, *args, **kwargs):
		if lookup in self._map.keys():
			return self._map.keys().index(lookup, *args, **kwargs)
		else:
			return -1

	def getAddress(self, prev=""):
		"""returns string path from root to this tree"""
		path = ".".join( (self.name, prev) )
		if self.root == self:
			return path
		else:
			return self.parent.getAddress(prev=path)



	def __getitem__(self, address):
		""" allows lookups of string form "root.branchA.leaf" """
		if isinstance(address, basestring): # if you look up [""] this will break
			address = address.split(".")
		if not address: # empty list
			return self
		first = address.pop(0)
		if not first in self._map:
			branch = self.addChild(AbstractTree(first, None))
		else:
			branch = self._map[first]
		return branch[address]

	# def __set__(self, instance, value):
	# 	if isinstance(value, AbstractTree):
	# 		raise RuntimeError
	# 	self.value = value

	@property
	def root(self):
		"""returns root tree object"""
		return self.parent.root if self.parent else self

	@property
	def value(self):
		return self._val
	@value.setter
	def value(self, val):
		self._val = val
		self.valueChanged(self)

	@staticmethod
	def fromDict(regenDict):
		"""expects dict of format
		name : eyy
		value : whatever
		children : [{
			etc}, {etc}]"""
		new = AbstractTree(regenDict["name"], regenDict["value"])
		new.extras = regenDict["extras"]
		for i in regenDict["children"]:
			branch = AbstractTree.fromDict(i)
			new.addChild(branch)
		return new

	def serialise(self):
		serial = {
			"name" : self.name,
			"value" : self.value,
			"extras" : self.extras,
			"children" :
				[v.serialise() for v in self._map.itervalues()]
		}
		return serial
