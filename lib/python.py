"""general lib for nifty python things like decorators and debugs"""
#from __future__ import print_function
import inspect,importlib, pprint, pkgutil
from weakref import WeakSet, WeakKeyDictionary
from collections import OrderedDict
from abc import ABCMeta

#from edRig import naming

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


class StringLikeMeta(str):

	__metaclass__ = ABCMeta

	"""hopefully a more efficient 'mutable string' than doing directly that -
	works on an internal _base string, which is free to change

	leaving all the weird and wonderful attempts at method shuffling here
	for curiosity, in the end I just overrode them one by one manually"""

	stringMethods = ['__add__', '__contains__',
	                 '__delslice__', '__doc__', '__eq__',
	                 '__format__', '__ge__', '__getitem__', #'__hash__',
	                 '__getslice__', '__gt__', '__iadd__', '__imul__',
	                 '__iter__', '__le__', '__len__', '__lt__',
	                 '__mul__', '__ne__', '__new__', '__reduce__',
	                 '__reduce_ex__', '__repr__', '__reversed__', '__rmul__',
	                 #'__setattr__', #'__setitem__', #'__setslice__',
	                 ]


	#def __new__(mcs, *args, **kwargs):
	def __new__(mcs, base):

		#new = super(StringLikeMeta, mcs).__new__(mcs, *args, **kwargs)
		#new = super(StringLikeMeta, mcs).__new__(mcs)
		new = str.__new__(mcs, base)
		#StringLikeMeta.register(new, str)

		return new
	
	def __call__(cls, *args, **kwargs):
		#cls.register(basestring)
		new = super(StringLikeMeta, cls).__call__(*args, **kwargs)
		#StringLikeMeta.register(cls, str)
	# 	for i in StringLikeMeta.stringMethods:
	# 		if i in str.__dict__:
	# 			new.__dict__[i] = str.__dict__[i]
	# 			new.__dict__[i] = lambda *args, **kwargs : \
	# 				str.__dict__[i](*args, **kwargs)
	#
	 	return new


class StringLike(StringLikeMeta):
	""" a proper, usable user string
	intelligent maya nodes, maya plugs, self-formatting email addresses
	we can do it"""

	def __init__(self, base=""):
		self._base = base

	# basic interface for core _base object ---
	@property
	def value(self):
		""" sets internal string directly, for subclass use """
		return str(self._base)
	@value.setter
	def value(self, val):
		""" :rtype : str """
		self._base = val


	def __getattr__(self, item):
		return self._base.__getattribute__(item)

	def __getattribute__(self, item):
		try:
			return object.__getattribute__(self, item)
		except:
			return str.__getattribute__(self._base, item)

	def __repr__(self):
		return self.__str__()
	def __str__(self):
		return self._base

	# string magic methods -------------
	def __add__(self, other):
		return str.__add__(self.value, other)
	def __contains__(self, item):
		return str.__contains__(self.value, item)
	def __delslice__(self, i, j):
		return str.__delslice__(self.base, i, j)
	def __eq__(self, other):
		return str.__eq__(self.value, other)
	def __format__(self, format_spec):
		return str.__format__(self.value, format_spec)
	def __ge__(self, other):
		return str.__ge__(self.value, other)
	def __getitem__(self, item):
		return str.__getitem__(self.value, item)
	def __getslice__(self, start, stop):
		return str.__getslice__(self.value, start, stop)
	def __gt__(self, other):
		return str.__gt__(self.value, other)
	def __iadd__(self, other):
		self.value = self.value + other
		return self.value
	def __imul__(self, other):
		self.value = self.value * other
		return self.value
	def __iter__(self):
		return str.__iter__(self.value)
	def __le__(self, other):
		return str.__le__(self.value, other)
	def __len__(self):
		return len(self.value)
	def __lt__(self, other):
		return str.__lt__(self.value, other)
	def __mul__(self, other):
		return str.__mul__(self.value, other)
	def __ne__(self, other):
		return str.__ne__(self.value, other)
	def __reversed__(self):
		return reversed(self.value)
	def __rmul__(self, other):
		return str.__rmul__(self.value, other)


if __name__ == '__main__':

	print StringLike
	#print type(StringLike)

	#assert issubclass(str, StringLike)
	test = StringLike("test")
	assert isinstance("this is a string", str)
	assert isinstance(test, str)
	print("jhgf" + test)
	#print(True)
	print(test.value)
	print(test)
	test.value = "eyyy"
	print test
	print test + "ei"


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
		self._name = name
		self.parent = None
		self._value = val
		self.valueChanged = Signal()
		self.structureChanged = Signal()
		self._map = OrderedDict()
		self.extras = {}

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, val):
		self._name = val

	def _setParent(self, tree):
		"""sets new abstractTree to be parent"""
		self.parent = tree
		self.valueChanged = tree.valueChanged
		self.structureChanged = tree.structureChanged

	def addChild(self, branch):
		if branch in self.branches:
			print("cannot add existing branch")
			return branch
		if branch.name in self.keys():
			print("cannot add duplicate child of name {}".format(branch.name))
			newName = self.getValidName(branch.name)
			branch.setName(newName)
			# raise RuntimeError(
			# 	"cannot add duplicate child of name {}".format(branch.name))
		self._map[branch.name] = branch
		branch._setParent(self)
		self.structureChanged()
		return branch

	def get(self, lookup, default):
		"""same implementation as normal dict"""
		return self._map.get(lookup, default)

	def index(self, lookup, *args, **kwargs):
		if lookup in self._map.keys():
			return self._map.keys().index(lookup, *args, **kwargs)
		else:
			return -1

	def ownIndex(self):
		if self.parent:
			return self.parent.index(self.name)
		else: return -1

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
		return zip(self._map.keys(), [i.value for i in self._map.values()])

	def iterBranches(self):
		return self._map.iteritems()

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

		# we need to preserve order across renaming
		if self.parent:
			newDict = OrderedDict()
			oldName = self.name
			name = self.parent.getValidName(name)
			for k, v in self.parent.iterBranches():
				if k == oldName:
					newDict[name] = self
					continue
				newDict[k] = v
			self.parent._map = newDict
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
		""" allows lookups of string form "root.branchA.leaf"
		:returns AbstractTree"""
		if isinstance(address, basestring): # if you look up [""] this will break
			address = address.split(".") # effectively maya attribute syntax
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
		return self._value
	@value.setter
	def value(self, val):
		self._value = val
		self.valueChanged(self)

	def matchBranchesToSequence(self, sequence,
	                            create=True, destroy=True):
		"""reorders, adds or deletes branches as necessary
		for the current tree's branches to match the target
		create and destroy govern whether new branches will be
		created or destroyed
		created branches are simple branches
		:type sequence list"""
		newMap = OrderedDict()
		for i in sequence:
			if i in self.keys():
				newMap[i] = self._map.pop(i)
			elif create:
				newBranch = AbstractTree(name=i, value=None)
				newBranch.parent = self
				newMap[i] = newBranch
		for i in self.branches:
			if destroy:
				self._map.pop(i.name)
			else:	newMap[i.name] = i
		self._map = newMap


	@staticmethod
	def fromDict(regenDict):
		"""expects dict of format
		name : eyy
		value : whatever
		children : [{
			etc}, {etc}]"""
		new = AbstractTree(regenDict["name"], regenDict["value"])
		new.extras = regenDict["extras"]

		# regnerate children with correct indices
		length = len(regenDict["children"])
		for n in range(length):
			for i in regenDict["children"]:
				if not i["?INDEX"] == n:
					continue
				branch = AbstractTree.fromDict(i)
				new.addChild(branch)
		return new

	def serialise(self):
		# print("key {} index {}".format(self.name, self.ownIndex()))
		# print("keys are {}".format(self.keys()))
		serial = {
			"name" : self.name,
			"value" : self.value,
			"extras" : self.extras,
			"children" : [i.serialise() for i in self._map.values()],
			"?INDEX" : self.ownIndex()
		}
		return serial

# test for interfaces with the tree structure
testTree = AbstractTree("TestRoot")
testTree["asdf"].value = "firstKey"
testTree["parent"].value = "nonas"
testTree["parent"]["childA"].value = 930
testTree["parent"]["childB"].value = True


#### REFERENCE IMPLEMENTATION BY LUMA ####

NOT_PROXY_WRAPPED = ['__new__', '__getattribute__', '__getattr__', '__setattr__',
					 '__class__', '__weakref__', '__subclasshook__',
					 '__reduce_ex__', '__reduce__', '__dict__', '__sizeof__',
					 '__module__', '__init__', '__doc__']

def proxyClass(cls, classname, dataAttrName=None, dataFuncName=None,
			   remove=(), makeDefaultInit = False, sourceIsImmutable=True,
			   module=None):
	"""
	This function will generate a proxy class which keeps the internal data separate from the wrapped class. This
	is useful for emulating immutable types such as str and tuple, while using mutable data.  Be aware that changing data
	will break hashing.  not sure the best solution to this, but a good approach would be to subclass your proxy and implement
	a valid __hash__ method.
	:Parameters:
	cls : `type`
		The class to wrap
	classname : `string`
		The name to give the resulting proxy class
	dataAttrName : `string`
		The name of an attribute on which an instance of the wrapped class will
		be stored.
		Either dataAttrname or dataFuncName must be given, but not both.
	dataFuncName : `string`
		The name of an attribute on which reside a function, which takes no
		arguments, and when called, will return an instance of the wrapped
		class.
		Either dataAttrname or dataFuncName must be given, but not both.
	remove : `string` iterable
		An iterable of name of attributes which should NOT be wrapped.
		Note that certain attributes will never be wrapped - the list of
		such items is found in the NOT_PROXY_WRAPPED constant.
	makeDefaultInit : `bool`
		If True and dataAttrName is True, then a 'default' __init__ function
		will be created, which creates an instance of the wrapped class, and
		assigns it to the dataAttr. Defaults to False
		If dataAttrName is False, does nothing
	sourceIsImmutable : `bool`
		This parameter is included only for backwards compatibility - it is
		ignored.
	:rtype: `type`
	"""

	assert not (dataAttrName and dataFuncName), 'Cannot use attribute and function for data storage. Choose one or the other.'

	if dataAttrName:
		class ProxyAttribute(object):

			def __init__(self, name):
				self.name = name

			def __get__(self, proxyInst, proxyClass):
				if proxyInst is None:
					return getattr(cls, self.name)
				else:
					return getattr(getattr(proxyInst, dataAttrName),
								   self.name)

		def _methodWrapper(method):
			def wrapper(self, *args, **kwargs):
				return method(getattr(self, dataAttrName), *args, **kwargs)

			wrapper.__doc__ = method.__doc__
			wrapper.__name__ = method.__name__
			return wrapper

	elif dataFuncName:
		class ProxyAttribute(object):

			def __init__(self, name):
				self.name = name

			def __get__(self, proxyInst, proxyClass):
				if proxyInst is None:
					return getattr(cls, self.name)
				else:
					return getattr(getattr(proxyInst, dataFuncName)(),
								   self.name)

		def _methodWrapper(method):
			# print method
			#@functools.wraps(f)
			def wrapper(self, *args, **kwargs):
				return method(getattr(self, dataFuncName)(), *args, **kwargs)

			wrapper.__doc__ = method.__doc__
			wrapper.__name__ = method.__name__
			return wrapper
	else:
		raise TypeError, 'Must specify either a dataAttrName or a dataFuncName'

	class Proxy(object):
		# make a default __init__ which sets the dataAttr...
		# if __init__ is in remove, or dataFuncName given,
		# user must supply own __init__, and set the dataAttr/dataFunc
		# themselves
		if makeDefaultInit and dataAttrName:
			def __init__(self, *args, **kwargs):
				# We may wrap __setattr__, so don't use 'our' __setattr__!
				object.__setattr__(self, dataAttrName, cls(*args, **kwargs))

		# For 'type' objects, you can't set the __doc__ outside of
		# the class definition, so do it here:
		if '__doc__' not in remove:
			__doc__ = cls.__doc__

	remove = set(remove)
	remove.update(NOT_PROXY_WRAPPED)
	#remove = [ '__init__', '__getattribute__', '__getattr__'] + remove
	for attrName, attrValue in inspect.getmembers(cls):
		if attrName not in remove:
			# We wrap methods using _methodWrapper, because if someone does
			#    unboundMethod = MyProxyClass.method
			# ...they should be able to call unboundMethod with an instance
			# of MyProxyClass as they expect (as opposed to an instance of
			# the wrapped class, which is what you would need to do if
			# we used ProxyAttribute)

			# ...the stuff with the cls.__dict__ is just to check
			# we don't have a classmethod - since it's a data descriptor,
			# we have to go through the class dict...
			if ((inspect.ismethoddescriptor(attrValue) or
				 inspect.ismethod(attrValue)) and
				not isinstance(cls.__dict__.get(attrName, None),
							   (classmethod, staticmethod))):
				try:
					setattr(Proxy, attrName, _methodWrapper(attrValue))
				except AttributeError:
					print "proxyClass: error adding proxy method %s.%s" % (classname, attrName)
			else:
				try:
					setattr(Proxy, attrName, ProxyAttribute(attrName))
				except AttributeError:
					print "proxyClass: error adding proxy attribute %s.%s" % (classname, attrName)

	Proxy.__name__ = classname
	if module is not None:
		Proxy.__module__ = module
	return Proxy


# Note - for backwards compatibility reasons, PyNodes still inherit from
# ProxyUnicode, even though we are now discouraging their use 'like strings',
# and ProxyUnicode itself has now had so many methods removed from it that
# it's no longer really a good proxy for unicode.

# NOTE: This may move back to core.general, depending on whether the __getitem__ bug was fixed in 2009, since we'll have to do a version switch there
# ProxyUnicode = proxyClass( unicode, 'ProxyUnicode', dataFuncName='name', remove=['__getitem__', 'translate']) # 2009 Beta 2.1 has issues with passing classes with __getitem__
ProxyUnicode = proxyClass(unicode, 'ProxyUnicode', module=__name__, dataFuncName='name',
						  remove=['__doc__', '__getslice__', '__contains__', '__len__',
								  '__mod__', '__rmod__', '__mul__', '__rmod__', '__rmul__',  # reserved for higher levels
								  'expandtabs', 'translate', 'decode', 'encode', 'splitlines',
								  'capitalize', 'swapcase', 'title',
								  'isalnum', 'isalpha', 'isdigit', 'isspace', 'istitle',
								  'zfill'])


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
	"""
	logFunction = logFunction# or print
	module = None
	try:
		module = importlib.import_module(mod)
	except Exception() as e:
		logFunction("ERROR in loading module {}".format(mod))
		logFunction("error is {}".format(str(e)))
	return module