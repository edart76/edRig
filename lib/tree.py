
""" mutable tree data structure """
from __future__ import print_function
import inspect,importlib, pprint, pkgutil, string, re, os
from weakref import WeakSet, WeakKeyDictionary, proxy
from collections import OrderedDict, MutableSet
from functools import partial, wraps
from abc import ABCMeta
import types

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

	def emit(self, *args, **kwargs):
		""" brings this object up to parity with qt """
		self(*args, **kwargs)

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


def rawToList(listString):
	""" given any raw input string of form [x, 1, ["ed", w] ]
	coerces string values to ints and floats and runs recursively on interior lists
	"""
	tokens = [i.strip() for i in listString[1:-1].split(",")]
	result = []
	for token in tokens:
		try:
			result.append(eval(token))
		except:
			result.append(str(token))

	return result


def incrementName(name, currentNames=None):
	"""checks if name is already in children, returns valid one"""
	if currentNames and name not in currentNames:
		return name
	if name[-1].isdigit(): # increment digit like basic bitch
		new = int(name[-1]) + 1
		return name[:-1] + str(new)
	if name[-1] in string.ascii_uppercase: # ends with capital letter
		if name[-1] == "Z": # start over
			name += "A"
		else: # increment with letter, not number
			index = string.ascii_uppercase.find(name[-1])
			name = name[:-1] + string.ascii_uppercase[index+1]
	else: # ends with lowerCase letter
		name += "B"

	# check if name already taken
	if currentNames and name in currentNames:
		return incrementName(name, currentNames)
	return name

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

uniqueSign = "|@|" # something that will never appear in file path
def saveObjectClass(obj, regenFunc="fromDict", relative=True, uniqueKey=True,
					legacy=False):
	""" saves a module and class reference for any object
	if relative, will return path from root folder"""
	keys = [ "NAME", "CLASS", "MODULE", "regenFn" ]
	if uniqueKey: # not always necessary
		for i in range(len(keys)): keys[i] = "?" + keys[i]

	#path = convertRootPath(obj.__class__.__module__, toRelative=relative)
	path = obj.__class__.__module__
	if legacy: # old inefficient dict method
		return {
			keys[0]: obj.__name__,
			keys[1]: obj.__class__.__name__,
			keys[2]: path,
			keys[3]: regenFunc
		}
	data = uniqueSign.join([obj.__class__.__name__, path])
	return data

def loadObjectClass(objData):
	""" recreates a class object from any known module """
	if isinstance(objData, dict):
		for i in ("?MODULE", "?CLASS"):
			if not objData.get(i):
				print("objectData {} has no key {}, cannot reload class".format(objData, i))
				return None
		path = objData["?MODULE"]
		className = objData["?CLASS"]

	elif isinstance(objData, (tuple, list)):
		# sequence [ class, modulepath, regenFn ]
		path = objData[1]
		className = objData[0]
	elif isinstance(objData, basestring):
		className, path = objData.split(uniqueSign)

	#module = convertRootPath( path, toAbsolute=True)
	module = path
	loadedModule = safeLoadModule(module)
	try:
		newClass = getattr(loadedModule, className)
		return newClass
	except Exception as e:
		print("ERROR in reloading class {} from module {}")
		print("has it moved, or module files been shifted?")
		print( "error is {}".format(str(e)) )
		return None

####### THE MAIN EVENT ########
""" there is the capability to change the separator token used by
tree addresses - I don't know the best way to do that, short of making
it an instance attribute """
separator = "."
# separator = "/"
parentToken = "^"
# parentToken = ".."
class Tree(object):
	"""fractal tree-like data structure
	each branch having both name and value"""
	branchesInherit = False

	def __init__(self, name=None, val=None):
		self._name = name
		self._parent = None
		self._value = val
		self.valueChanged = Signal()
		self.structureChanged = Signal()
		self._map = OrderedDict()
		self.extras = {}
		self.overrides = {}

		# read-only attr
		self.readOnly = False
		self.active = True

	@classmethod
	def _defaultCls(cls):
		return Tree

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
	def siblings(self):
		if self.parent:
			return self.parent.branches.remove(self)
		return []

	@property
	def root(self):
		"""returns root tree object
		consider possibly denoting arbitrary points in tree as breakpoints,
		roots only to branches under them """
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
		:rtype list( AbstractTree )"""
		return self.values()


	def _setParent(self, tree):
		"""sets new abstractTree to be parent"""
		self._parent = tree
		if tree: # setting to none can happen
			self.valueChanged = tree.valueChanged
			self.structureChanged = tree.structureChanged

	def addChild(self, branch, index=None, force=False):
		if branch in self.branches:
			print("cannot add existing branch, named " + branch.name)
			return branch
		if branch.name in self.keys():
			if force: # override old branch with new
				pass
			else:
				print("cannot add duplicate child of name {}".format(branch.name))
				newName = incrementName(branch.name, currentNames=self.keys())
				branch._setName(newName)

		if index is None:
			self._map[branch.name] = branch
		else: # more complex ordered dict management
			newMap = OrderedDict()
			oldBranches = self._map.values()
			if index > len(oldBranches) - 1:
				index = len(oldBranches)
			oldBranches.insert(index, branch)
			for newBranch in oldBranches:
				newMap[newBranch.name] = newBranch
			self._map = newMap
		branch._setParent(self)
		self.structureChanged()
		return branch


	def get(self, lookup, default=None):
		""" same implementation as normal dict
		addresses will recurse into child branches
		duplication here from main address system, fix it """
		if isinstance(lookup, basestring):
			lookup = lookup.split(".")
		name = lookup.pop(0)
		if name not in self._map.keys():
			return default
		if lookup:
			return self._map[name].get(lookup)
		return self._map[name]


	def index(self, lookup=None, *args, **kwargs):
		if lookup is None: # get tree's own index
			return self.ownIndex()
		if lookup in self._map.keys():
			return self._map.keys().index(lookup, *args, **kwargs)
		else:
			return -1

	def ownIndex(self):
		if self.parent:
			return self.parent.index(self.name)
		else: return -1

	def flattenedIndex(self):
		""" return the index of this branch if entire tree were flattened """
		index = self.index()
		if self.parent:
			index += self.parent.flattenedIndex()
		return index



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

	def allBranches(self, includeSelf=True):
		""" returns list of all tree objects
		depth first """
		found = [ self ] if includeSelf else []
		#found = [ self ]
		for i in self.branches:
			found.extend(i.allBranches())
		return found

	def getAddress(self, prev=""):
		"""returns string path from root to this tree
		does not include root"""
		if self.root == self:
			return prev
		path = ".".join( (self.name, prev) ) if prev else self.name
		# else:
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
		toCheck = self.branches if onlyChildren else self.allBranches(True)
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

	def remove(self, address=None):
		"""removes address, or just removes the tree if no address is given"""
		if not address:
			if self.parent:
				self.parent._map.pop(self.name)
				#self.structureChanged()
				self.parent.structureChanged()
				return self
		branch = self(address)
		branch.remove()
		branch.parent.structureChanged()
		return branch


	def __getitem__(self, address):
		""" allows lookups of string form "root.branchA.leaf"
		"""
		return self(address).value

	def __setitem__(self, key, value):
		""" assuming that setting tree values is far more frequent than
		setting actual tree objects """
		self(key).value = value

	def __call__(self, address):
		""" allows lookups of string form "root.branchA.leaf"
		:returns AbstractTree
		:rtype AbstractTree"""
		#debug(address)
		if isinstance(address, basestring): # if you look up [""] this will break
			address = str(address).split(".") # effectively maya attribute syntax
		elif isinstance(address, (list, tuple)): # already split
			pass
		if not address: # empty list
			return self
		first = address.pop(0)
		if first == "^": # aka unix ../
			return self.parent(address)
		if not first in self._map: # add it if doesn't exist
			if self.readOnly:
				raise RuntimeError( "readOnly tree accessed improperly - "
									"no address {}".format(first))
			# check if branch should inherit directly, or
			# remain basic tree object
			if self.branchesInherit:
				obj = self.__class__(first, None)
			else:
				obj = self._defaultCls()(first, None)
			branch = self.addChild(obj)
		else: # branch name might be altered
			branch = self._map[first]
		return branch(address)

	def __repr__(self):
		return "<{} ({}) : {}>".format(self.__class__, self.name, self.value)

	def __copy__(self):
		""" create shallow copy of this tree -
		new tree object, new internal map, same
		tree objects in map """
		tree = self.__class__(self.name)
		if self.value is not None:
			tree.value = type(self.value)(self.value)
		tree._map = OrderedDict(self._map)
		return tree

	def __deepcopy__(self):
		return self.fromDict(self.serialise())


	def setIndex(self, index):
		""" reorders tree branch to given index
		negative indices not yet supported """
		if not self.parent:
			return
		if index < 0: # ?
			index = len(self.siblings) + index
		newMap = OrderedDict()
		oldKeys = self.parent._map.keys()
		oldKeys.remove(self.name)
		oldKeys.insert(index, self.name)
		for key in oldKeys:
			newMap[key] = self.parent._map[key]
		self.parent._map = newMap


	### basic hashing system, after stackOverflow
	# def __key(self):
	# 	debug(self)
	# 	return (self._name, str(self._value), self._map)
	#
	# def __hash__(self):
	# 	return hash(self.__key())
	#
	# def __eq__(self, other):
	# 	if isinstance(other, AbstractTree):
	# 		return self.__key() == other.__key()
	# 	return NotImplemented

	#def __copy__(self):

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
		objData = regenDict.get("objData") or {}
		if objData:
			cls = loadObjectClass( objData )
			cls = cls or cls._defaultCls()

		# if branch is same type as parent, no info needed
		# a tree of one type will mark all branches as same type
		# until a new type is flagged
		val = regenDict.get("?VALUE") or None
		name = regenDict.get("?NAME") or None
		children = regenDict.get("?CHILDREN") or []
		if not (val or name or children): # skip branch
			print("regenDict {}".format(regenDict))
			print("no name, val or children found")
			return None
		new = cls(name=name, val=val)
		new.extras = regenDict.get("?EXTRAS") or {}

		# regnerate children
		for i in children:
			branch = cls.fromDict(i)
			if branch is None:
				continue
			new.addChild(branch)
		return new


	def serialise(self):
		serial = {
			"?NAME" : self.name,
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
				# it now costs exactly one extra line to define the child class
				# it's worth it to avoid the pain of adaptive definition

		# always returns dict
		return serial

	def display(self):
		seq = pprint.pformat( self.serialise() )
		return seq

	@staticmethod
	def _setTreeValue(tree, value):
		""" stub for setting tree values asynchronously """
		tree.value = value