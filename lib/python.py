"""general lib for nifty python things like decorators and debugs"""
from __future__ import print_function
import inspect,importlib, pprint, pkgutil
from weakref import WeakSet, WeakKeyDictionary
from collections import OrderedDict
import string
from edRig import naming

class Decorator(object):
	"""base decorator class for functions
	to be assigned ui buttons"""

	def __init__(self, func, *args, **kwargs):
		self.func = func
		self.args = args
		self.kwargs = kwargs

	def __call__(self, *args, **kwargs):
		raise NotImplementedError

def getUserInput(prompt=None, default="eyyy"):
	prompt = prompt or "user input"
	try:
		name = raw_input(prompt)
	except EOFError:
		# nothing entered
		print("nothing entered, defaulting")
		name = default
	return name

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


class StringLike(object):
	""" tried to implement this behaviour enough to merit this
	DECORATOR for classes having to act like strings in normal operations etc"""

	def __init__(self, c, *args, **kwargs):
		self.c = c

	def __call__(self, *args, **kwargs):
		new = self.c.__new__(self.c, *args, **kwargs)
		self.wireMethods(new)

	def wireMethods(self, c):
		""" supplant various magic methods to have them draw
		directly from class' __str__ when called"""

		shuffleMethods = [
			c.__repr__,
			c.__len__,
			c.__iter__,
			c.__contains__,
			c.__eq__,
		] # etc

		for i in shuffleMethods:
			### now what
			lambda i : c.__str__().ad
		# how do you dynamically assign this



	pass

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
	def __init__(self, name=None, val=None):
		self.name = name
		self.parent = None
		self._val = val
		self.valueChanged = Signal()
		self.structureChanged = Signal()
		self._map = OrderedDict()
		self.extras = {}

	def _setParent(self, tree):
		"""sets new abstractTree to be parent"""
		self.parent = tree
		self.valueChanged = tree.valueChanged
		self.structureChanged = tree.structureChanged
	def addChild(self, branch):
		if branch.name in self.keys():
			raise RuntimeError(
				"cannot add duplicate child of name {}".format(branch.name))
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

	def items(self):
		return self._map.items()

	def values(self):
		return self._map.values()

	@property
	def branches(self):
		"""more explicit that it returns the child tree objects"""
		return self.values()

	def keys(self):
		return self._map.keys()

	def iteritems(self):
		return zip([self._map.keys()], [i.value for i in self._map.items()])

	def getAddress(self, prev=""):
		"""returns string path from root to this tree"""
		path = ".".join( (self.name, prev) )
		if self.root == self:
			return path
		else:
			return self.parent.getAddress(prev=path)

	def setName(self, name):
		"""renames and syncs parent's map
		currently destroys orderedDict order - oh well"""
		if name == self.name: # we aint even mad
			return name
		if self.parent:
			oldName = self.name
			name = self.parent.getValidName(name)
			self.parent._map.pop(oldName)
			self.parent._map[name] = self
		self.name = name
		self.structureChanged()
		return name

	def getValidName(self, name=""):
		"""checks if name is already in children, returns valid one"""
		if not name in self.keys():
			return name
		else:
			return self.getValidName(naming.incrementName(name))

	def remove(self, address=None):
		"""removes address, or just removes the tree if no address is given"""
		if not address:
			if self.parent:
				self.parent._map.pop(self.name)


	def __getitem__(self, address):
		""" allows lookups of string form "root.branchA.leaf" """
		if isinstance(address, basestring): # if you look up [""] this will break
			address = address.split(".")
		if not address: # empty list
			return self
		first = address.pop(0)
		if not first in self._map: # add it if doesn't exist
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
	def address(self):
		return self.getAddress()

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

def flatten(in_list):
	"""Flatten a given list recursively.
	Args: in_list (list or tuple): Can contain scalars, lists or lists of lists.
	Returns: list: List of depth 1; no inner lists, only strings, ints, floats, etc.
			flatten([1, [2, [3], 4, 5], 6])
			>>> [1, 2, 3, 4, 5, 6]	"""
	flattened_list = []
	for item in in_list:
		if isinstance(item, (list, tuple)):
			flattened_list.extend(flatten(item))
		else:
			flattened_list.append(item)
	return flattened_list

def itersubclasses(cls, _seen=None):
	"""
	itersubclasses(cls)
	http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
	Generator over all subclasses of a given class, in depth first order.

	>>> list(itersubclasses(int)) == [bool]
	True
	>>> class A(object): pass
	>>> class B(A): pass
	>>> class C(A): pass
	>>> class D(B,C): pass
	>>> class E(D): pass
	>>>
	>>> for cls in itersubclasses(A):
	...     print(cls.__name__)
	B
	D
	E
	C
	>>> # get ALL (new-style) classes currently defined
	>>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
	['type', ...'tuple', ...]
	"""

	if not isinstance(cls, type):
		raise TypeError('itersubclasses must be called with '
		                'new-style classes, not %.100r' % cls)
	if _seen is None: _seen = set()
	try:
		subs = cls.__subclasses__()
	except TypeError:  # fails only when cls is type
		subs = cls.__subclasses__(cls)
	for sub in subs:
		if sub not in _seen:
			_seen.add(sub)
			yield sub
			for sub in itersubclasses(sub, _seen):
				yield sub

def iterSubModuleNames(package=None, path=None, fullPath=True, debug=False):
	"""yields names of all modules in package - DOES NOT import them"""
	names = []
	if not path:
		loader = pkgutil.get_loader(package)
		if not loader.is_package(loader.fullname):
			names.append(package.__name__)
			return names

		path = [loader.filename]

		if debug: print("path {}".format(path))

	for loader, module_name, is_pkg in pkgutil.walk_packages(path):
		if debug: print("module name {}".format(module_name))

		names.append(module_name)
	if fullPath:
		names = [package.__name__ + "." + i for i in names]
	return names

def safeLoadModule(mod, logFunction=None):
	"""takes string name of module
	DEPRECATED, use lib/python/safeLoadModule"""
	logFunction = logFunction or print
	module = None
	try:
		module = importlib.import_module(mod)
	except Exception as e:
		logFunction("ERROR in loading module {}".format(mod))
		logFunction("error is {}".format(str(e)))
	return module