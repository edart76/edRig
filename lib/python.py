"""general lib for nifty python things like decorators and debugs"""
from __future__ import print_function
import inspect,importlib, pprint, pkgutil
from weakref import WeakSet, WeakKeyDictionary
from collections import OrderedDict
from abc import ABCMeta
import types


# from Tkinter import *
#
# import Tkinter, tkFileDialog
#
# def fileDialog(defaultPath="", title="Select File"):
# 	""" absolute most basic file selection possible"""
# 	path = defaultPath or "/"
# 	root = Tkinter.Tk()
# 	root.withdraw()
# 	return tkFileDialog.askopenfilename(
# 		initialdir=path, title=title
# 	)
#




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


#class StringLikeMeta(ABCMeta):
class StringLikeMeta(type):

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


	def __new__(mcs, *args, **kwargs):
	#def __new__(mcs, base):

		#new = super(StringLikeMeta, mcs).__new__(mcs)
		#new = str.__new__(mcs, base)
		#new = str.__new__(mcs, *args, **kwargs)
		# mcs.register(str)
		new = super(StringLikeMeta, mcs).__new__(mcs, *args, **kwargs)
		return new
	
	def __call__(cls, *args, **kwargs):
		#cls.register(basestring)
		new = super(StringLikeMeta, cls).__call__(*args, **kwargs)
		#StringLikeMeta.register(cls)
	# 	for i in StringLikeMeta.stringMethods:
	# 		if i in str.__dict__:
	# 			new.__dict__[i] = str.__dict__[i]
	# 			new.__dict__[i] = lambda *args, **kwargs : \
	# 				str.__dict__[i](*args, **kwargs)
	#
	 	return new

#StringLikeMeta.register(str)
#StringLikeMeta.register(basestring)
#StringLikeMeta.register(type("") )

""" beginning to think there is something specifically wrong with maya
cmds, everything else works without directly inheriting from string
registering str as a false type is the next step, but I can't get that
to work either """


#class StringLike(str, object):
#class StringLike(object, str):
class StringLike(str): # best I can do for now
#class StringLike(object):
	""" a proper, usable user string
	intelligent maya nodes, maya plugs, self-formatting email addresses
	we can do it"""

	__metaclass__ = StringLikeMeta

	def __init__(self, base=""):
		self._base = str(base) # no unicode

	# basic interface for core _base object ---
	@property
	def value(self):
		""" sets internal string directly, for subclass use """
		return str(self._base)
	@value.setter
	def value(self, val):
		""" :rtype : str """
		self._base = str(val) # no unicode


	# def __getattr__(self, item):
	# 	try:
	# 		return object.__getattr__(item)
	# 	except:
	# 		return self._base.__getattribute__(item )
	#
	# def __getattribute__(self, item):
	# 	try:
	# 		return object.__getattribute__(self, item)
	# 	except:
	# 		return str.__getattribute__(self._base, item)

	def __repr__(self):
		return self.__str__()
	def __str__(self):
		return str(self._base)

	# def __unicode__(self):
	# 	return unicode(self.__str__())

	# string magic methods -------------
	def __add__(self, other):
		return str.__add__(self.value, other)
	def __contains__(self, item):
		return str.__contains__(self.value, item)
	def __delslice__(self, i, j):
		return str.__delslice__(self.value, i, j)
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
	# def __iter__(self):
	# 	return str.__iter__(self.value)
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
	def __hash__(self):
		return str.__hash__(self.value)

#StringLike.register(str)

if __name__ == '__main__':

	print(StringLike)
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
	print(test)
	print(test + "ei")


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

	""" should branches created by calling
	directly inherit the parent class,
	or fall back to basic tree? """
	branchesInherit = False

	def __init__(self, name=None, val=None):
		self._name = name
		self._parent = None
		self._value = val
		self.valueChanged = Signal()
		self.structureChanged = Signal()
		self._map = OrderedDict()
		self.extras = {}

		# read-only attr
		self.readOnly = False
		self.active = True

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, val):
		""" update parent map """
		self._setName(val)

	@property
	def parent(self):
		""":rtype AbstractTree"""
		return self._parent
	@parent.setter
	def parent(self, val):
		self._setParent(val)

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
		oldVal = self._value
		self._value = val
		if oldVal != val:
			self.valueChanged(self)

	@property
	def branches(self):
		"""more explicit that it returns the child tree objects
		:rtype list( AbstractTree )
		always returns all branches, regardless of class"""
		return self.values()

	@property
	def children(self):
		""" :rtype list( AbstractTree )
		override for custom filtering"""
		return self.branches

	def _setParent(self, tree):
		"""sets new abstractTree to be parent"""
		self._parent = tree
		self.valueChanged = tree.valueChanged
		self.structureChanged = tree.structureChanged

	def addChild(self, branch):
		if branch in self.branches:
			print("cannot add existing branch")
			return branch
		if branch.name in self.keys():
			print("cannot add duplicate child of name {}".format(branch.name))
			newName = self.getValidName(branch.name)
			branch._setName(newName)
			# raise RuntimeError(
			# 	"cannot add duplicate child of name {}".format(branch.name))
		self._map[branch.name] = branch
		branch._setParent(self)
		self.structureChanged()
		return branch

	def addDirectChild(self, branch):
		""" only called when adding an inherited branch? """

	def get(self, lookup, default=None):
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

	def keys(self):
		return self._map.keys()

	def iteritems(self):
		return zip(self._map.keys(), [i.value for i in self._map.values()])

	def iterBranches(self):
		return self._map.iteritems()

	def allBranches(self):
		""" returns list of all tree objects
		depth first """
		found = [ self ]
		for i in self.branches:
			found.extend(i.allBranches())
		return found

	def getAddress(self, prev=""):
		"""returns string path from root to this tree"""
		path = ".".join( (self.name, prev) )
		if self.root == self:
			return path
		else:
			return self.parent.getAddress(prev=path)

	def search(self, path, onlyChildren=True, found=None):
		""" searches branches for trees matching a partial path,
		and returns ALL THAT MATCH
		so for a tree
		root
		+ branchA
		  + leaf
		+ branchB
		  + leaf
		search("leaf") -> two trees
		right now would also return both for search( "lea" ) -
		basic contains check is all I have

		if onlyChildren, only searches through children -
		else checks through all branches

		"""

		found = []
		if path in self.name:
			found.append(self)
		toCheck = self.children if onlyChildren else self.branches
		for i in toCheck:
			found.extend( i.search(path) )
		return found


	def _setName(self, name):
		"""renames and syncs parent's map
		currently destroys orderedDict order - oh well"""
		if name == self._name: # we aint even mad
			return name

		# we need to preserve order across renaming
		if self.parent:
			newDict = OrderedDict()
			oldName = self._name
			name = self.parent.getValidName(name)
			for k, v in self.parent.iterBranches():
				if k == oldName:
					newDict[name] = self
					continue
				newDict[k] = v
			self.parent._map = newDict
		self._name = name
		self.structureChanged()
		return name

	def getValidName(self, name=""):
		"""checks if name is already in children, returns valid one"""
		if not name in self.keys():
			return name
		else:
			#return self.getValidName(naming.incrementName(name))
			pass

	def remove(self, address=None):
		"""removes address, or just removes the tree if no address is given"""
		if not address:
			if self.parent:
				self.parent._map.pop(self.name)
				self.structureChanged()


	def __getitem__(self, address):
		""" allows lookups of string form "root.branchA.leaf"
		:returns AbstractTree"""
		return self(address).value

	def __setitem__(self, key, value):
		""" assuming that setting tree values is far more frequent than
		setting actual tree objects """
		self(key).value = value

	def __call__(self, address):
		""" allows lookups of string form "root.branchA.leaf"

		:returns AbstractTree"""
		if isinstance(address, basestring): # if you look up [""] this will break
			address = address.split(".") # effectively maya attribute syntax
		if not address: # empty list
			return self
		first = address.pop(0)
		if not first in self._map: # add it if doesn't exist

			if self.readOnly:
				raise RuntimeError( "readOnly tree accessed improperly - "
				                    "no address {}".format(first))

			# check if branch should inherit directly, or
			# remain basic tree object

			if self.branchesInherit:
				obj = self.__class__(first, None)
			else:
				obj = AbstractTree(first, None)
			self.addChild(obj)
		#else:
		branch = self._map[first]
		return branch(address)


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
				newBranch = AbstractTree(name=i, val=None)
				newBranch.parent = self
				newMap[i] = newBranch
		for i in self.branches:
			if destroy:
				self._map.pop(i.name)
			else:	newMap[i.name] = i
		self._map = newMap


	@classmethod
	def fromDict(cls, regenDict):
		"""expects dict of format
		name : eyy
		value : whatever
		children : [{
			etc}, {etc}]
			:param regenDict : Dict """

		# support subclass serialisation and regen -
		# check first for a saved class or module name
		objDict = regenDict.get("objData") or {}
		if "?CLASS" in objDict and "?MODULE" in objDict:
			# cls = loadObjectClass({ "?CLASS" : objDict["?CLASS"],
			#                   "?MODULE" : objDict["?MODULE"]})
			cls = loadObjectClass( objDict )

		# if branch is same type as parent, no info needed
		# a tree of one type will mark all branches as same type
		# until a new type is flagged
		val = regenDict.get("?VALUE") or None
		new = cls(name=regenDict["?NAME"], val=val)
		new.extras = regenDict.get("?EXTRAS") or {}

		children = regenDict.get("?CHILDREN") or []



		# regnerate children with correct indices
		length = len(children)
		for n in range(length):
			for i in children:
				if not i["?INDEX"] == n:
					continue

				""" check some rules on deserialisation """
				# is there any kind of override?
				if i.get("objData"):
					childCls = loadObjectClass(i["objData"])
				else:
					if cls.branchesInherit:
						childCls = cls
					else:
						childCls = AbstractTree

				branch = cls.fromDict(i)
				#branch = childCls.fromDict(i)
				new.addChild(branch)
		return new

	def serialise(self):
		# print("key {} index {}".format(self.name, self.ownIndex()))
		# print("keys are {}".format(self.keys()))
		serial = {
			"?NAME" : self.name,
			"?INDEX" : self.ownIndex()
		}
		if self.value:
			serial["?VALUE"] = self.value
		if self.branches:
			serial["?CHILDREN"] = [i.serialise() for i in self._map.values()]
		if self.extras:
			serial["?EXTRAS"] = self.extras
		if self.parent:

			if self.parent.__class__ != self.__class__:
				objData = saveObjectClass(self)
				serial["objData"] = objData

			if 0: # doesn't work yet
				# class type saving

				# save class if parent type DOES inherit,
				# and this type is not parent
				if self.parent.branchesInherit:
					if self.parent.__class__ != self.__class__:
						objData = saveObjectClass(self)
						serial["objData"] = objData

				# save class if parent type DOES NOT inherit,
				# and this is not a normal AbstractTree
				else:
					if self.__class__ != AbstractTree:
						objData = saveObjectClass(self)
						serial[ "objData" ] = objData

		# always returns dict
		return serial

	def display(self):
		seq = pprint.pformat( self.serialise() )
		return seq

if __name__ == '__main__':


	# test for interfaces with the tree structure
	testTree = AbstractTree("TestRoot")
	testTree("asdf").value = "firstKey"
	testTree("parent").value = "nonas"
	testTree("parent.childA").value = 930
	testTree("parent.childB").value = True

	print(testTree["parent"])
	print(testTree["parent.childA"])
	print(testTree["parent.childB"])


def movingMask(seq, maskWidth=1, nullVal=None):
	""" generates a symmetrical moving frame over sequence
	eg seq = [ 1, 2, 3, 4, 5, 6 ]
	mask = movingMask(seq, maskWidth=1)
	mask = [ ( None, 1, 2 ), (1, 2, 3), (2, 3, 4)... ] etc
	"""


def flatten(in_list, ltypes=(list, tuple)):
	"""better flattening courtesy of Mike C Fletcher (I think)
	"""
	ltype = type(in_list)
	in_list = list(in_list)
	i = 0
	while i < len(in_list):
		while isinstance( in_list[i], ltypes):
			if not in_list[i]:
				in_list.pop(i)
				i -= 1
				break
			else:
				in_list[ i : i+1 ] = in_list[i]
		i += 1
	return ltype( in_list )


def itersubclasses(cls, _seen=None):
	"""
	itersubclasses(cls)
	http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
	Generator over all subclasses of a given class, in depth first order.

	True

	B
	D
	E
	C

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
	logFunction = logFunction or print
	module = None
	try:
		module = importlib.import_module(mod)
	except ImportError() as e:
		logFunction("ERROR in loading module {}".format(mod))
		logFunction("error is {}".format(str(e)))
	return module

def saveObjectClass(obj, regenFunc="fromDict", uniqueKey=True):
	""" saves a module and class reference for any object
	if relative, will return path from root folder"""
	keys = [ "?NAME", "?CLASS", "?MODULE", "regenFn" ]
	# if uniqueKey: # not always necessary
	# 	for i in range(len(keys)): keys[i] = "?" + keys[i]

	#path = convertRootPath(obj.__class__.__module__, toRelative=relative)
	path = obj.__class__.__module__
	return {
		#keys[0]: obj.__name__,
		keys[1]: obj.__class__.__name__,
		keys[2]: path,
		keys[3]: regenFunc
	}

def loadObjectClass(objData):
	""" recreates a class object from any known module """
	for i in ("?MODULE", "?CLASS"):
		if not objData.get(i):
			print("objectData {} has no key {}, cannot reload class".format(objData, i))
			return None
	module = objData["?MODULE"]
	loadedModule = safeLoadModule(module)
	try:
		newClass = getattr(loadedModule, objData["?CLASS"])
		return newClass
	except Exception as e:
		print("ERROR in reloading class {} from module {}")
		print("has it moved, or module files been shifted?")
		print( "error is {}".format(str(e)) )
		return None
