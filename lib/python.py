"""general lib for nifty python things like decorators and debugs"""
from __future__ import print_function
import inspect,importlib, pprint, pkgutil, string, re, os
from weakref import WeakSet, WeakKeyDictionary, proxy
from collections import OrderedDict, MutableSet
from functools import partial, wraps
from abc import ABCMeta
import types



class Decorator(object):
	"""base decorator class for functions
	to be assigned ui buttons"""

	def __init__(self, func, *args, **kwargs):
		self.func = func
		self.args = args
		self.kwargs = kwargs

	def __call__(self, *args, **kwargs):
		raise NotImplementedError

class ContextDecorator(object):
	""" class to wrap functions with context through decorator """
	def __init__(self, *decoratorArgs, **decoratorKwargs):
		""" called when object or decorator is created """
		self.args = decoratorArgs
		self.kwargs = decoratorKwargs
	def __enter__(self):
		raise NotImplementedError
	def __exit__(self, exc_type, exc_val, exc_tb):
		raise NotImplementedError

	def __call__(self, fn):
		""" called to wrap function, returns wrapper """
		@wraps(fn)
		def wrap( *args, **kwargs):
			""" receives arguments of function call """
			with self:
				return fn( *args, **kwargs)
		return wrap


def getUserInput(prompt=None, default="eyyy"):
	prompt = prompt or "user input"
	try:
		name = raw_input(prompt)
	except EOFError:
		# nothing entered
		print("nothing entered, defaulting")
		name = default
	return name

def incrementName(name, currentNames=None):
	"""checks if name is already in children, returns valid one"""
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
	#print( "found name is {}".format(name))
	return name

def camelCase(name):
	return name[0].lower() + name[1:]

def camelJoin():
	pass

""" stack introspection
FrameInfo(frame, filename, lineno, function, code_context, index)
function: function name
code_context : list of lines from where stack was called
index : index of calling line within that list
"""
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
	callerStack = inspect.stack()[1]
	callerFrame = callerStack[0] # frame object from stack above this one
	try:
		# reloading issues prevent us from relying directly
		# on line content of caller stack
		callingFile = callerStack[1]
		with open( callingFile, "r") as f:
			lines = f.readlines()
			callingLine = lines[ callerStack[2]] # line number
			#print("callingLine {}".format(callingLine))

		content = re.findall("debug\(([^)]*)\)", callingLine)
		# regex to find 'debug( *random string here* )
		if not content:
			# backup for dynamic code
			callingLine = callerStack[4][callerStack[5] ]
			content = re.findall("debug\(([^)]*)\)", callingLine)

			if not content:

				print("debug failed, has the function name been reassigned?")
				#print("callerStack {}".format(callerStack))
				#print("callerLines {}".format(lines))
				# print("callingLine {}".format(callingLine))
				#print("content {}".format(callingLine))
				return None
		#print("callerStack {}".format(callerStack))
		#print("callingLine {}".format(callingLine))
		content = content[0].strip()
		print("{} is {}".format(content, pprint.pformat(var)))
		return content

	finally:
		del callerFrame
		del callerStack

def outerVars():
	"""returns a dict of variable names from the outer scope of the call
	used mainly to add actions to classes because decorators drive me mad"""
	callerFrame = inspect.stack()[1][0]
	return callerFrame.f_locals


def rawToList(listString):
	""" given any raw input string of form [x, 1, ["ed", w] ]
	coerces string values to ints and floats and runs recursively on interior lists
	"""
	tokens = [i.strip() for i in listString[1:-1].split(",")]
	result = []
	for token in tokens:
		# if token.startswith("[") and token.endswith("]"):
		# 	result.append(rawToList(token))
		# no parsers here, cannot handle nested lists
		try:
			result.append(eval(token))
		except:
			result.append(str(token))

	return result


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
	# def __class__(self):

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

# if __name__ == '__main__':
#
# 	print(StringLike)
# 	#print type(StringLike)
#
# 	#assert issubclass(str, StringLike)
# 	test = StringLike("test")
# 	assert isinstance("this is a string", str)
# 	assert isinstance(test, str)
# 	print("jhgf" + test)
# 	#print(True)
# 	print(test.value)
# 	print(test)
# 	test.value = "eyyy"
# 	print(test)
# 	print(test + "ei")


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
	def listValue(self):
		""" convenience for iteration - converts tree value to list """
		if str(self._value).endswith("]") and str(self._value).startswith("["):
			""" convert to list and eval """
			return rawToList(self._value)

		if isinstance(self._value, (int, float, basestring)):
			return [self._value]
		if self._value is None: return []
		return []

	# extras properties
	@property
	def options(self):
		if not self.extras.get("options"):
			self.extras["options"] = []
		return self.extras["options"]
	@options.setter
	def options(self, val):
		self.extras["options"] = val

	@property
	def branches(self):
		"""more explicit that it returns the child tree objects
		:rtype list( AbstractTree )"""
		return self.values()

	@property
	def children(self):
		""" :rtype list( AbstractTree )
		override for custom filtering"""
		return self.branches

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
				newName = self.getValidName(branch.name)
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

	def addDirectChild(self, branch):
		""" only called when adding an inherited branch? """

	def get(self, lookup, default=None):
		"""same implementation as normal dict
		addresses will recurse into child branches """
		#return self._map.get(lookup, default)
		if isinstance(lookup, basestring):
			lookup = lookup.split(".")
		name = lookup.pop(0)
		if name not in self._map.keys():
			return None
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
			#return self.getValidName(incrementName(name))
			return incrementName(name, currentNames=self.keys())
			pass

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
				obj = AbstractTree(first, None)
			branch = self.addChild(obj)
		else: # branch name might be altered
			branch = self._map[first]
		return branch(address)

	def __repr__(self):
		return "<{} ({}) : {}>".format(self.__class__, self.name, self.value)


	""" shaky support for 'array attribute' branch generation """
	def makeChildBranch(self, name=None, *args, **kwargs):
		""" to be overridden """
		defaultKwargs = { "val" : None }
		newBranch = self.__class__(name=name, **defaultKwargs)
		return newBranch

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
				#newBranch = self.__class__(name=i, val=None)
				newBranch = self.makeChildBranch(name=i)
				newBranch.parent = self
				newMap[i] = newBranch
		for i in self.branches:
			if destroy:
				self._map.pop(i.name)
			else:	newMap[i.name] = i
		self._map = newMap

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
			cls = cls or AbstractTree

		# if branch is same type as parent, no info needed
		# a tree of one type will mark all branches as same type
		# until a new type is flagged
		val = regenDict.get("?VALUE") or None
		name = regenDict.get("?NAME") or None
		children = regenDict.get("?CHILDREN") or []
		if not (val or name or children): # skip branch
			print("regenDict {}".format(regenDict))
			print("no name, val or children found")
			pass
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


# string stuff
def stripNonAlphaNumeric(line, replace="_"):
	""" replaces all non-alphaNumeric characters with given item """
	return re.sub('[\W_]+', replace, line)

def conformPathSeparators(line):
	""" ensures that any slash of any kind is os.path.separator"""
	return line.replace("\\", os.path.sep).replace("/", os.path.sep)

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


def matchSequence():
	""" ?????????? """

def removeDuplicates( baseList ):
	existing = set()
	result = []
	for i in baseList:
		if i not in existing:
			result.append(i)
			existing.add(i)
	return result


class Link(object):
	__slots__ = 'prev', 'next', 'key', '__weakref__'

class DataRef(object):
	""" wrapper for consistent references to primitive data types """
	def __init__(self, val):
		self._val = val
	def __repr__(self):
		return self._val
	def __call__(self, *args, **kwargs):
		self._val = args[0]


class OrderedSet(MutableSet):
	"""Set the remembers the order elements were added
	code recipe 576696 """

	def __init__(self, iterable=None):
		self.__root = root = Link()         # sentinel node for doubly linked list
		root.prev = root.next = root
		self.__map = {}                     # key --> link
		if iterable is not None:
			self |= iterable

	def __len__(self):
		return len(self.__map)

	def __contains__(self, key):
		return key in self.__map

	def add(self, key):
		# Store new key in a new link at the end of the linked list
		if key not in self.__map:
			self.__map[key] = link = Link()
			root = self.__root
			last = root.prev
			link.prev, link.next, link.key = last, root, key
			last.next = root.prev = proxy(link)

	def discard(self, key):
		# Remove an existing item using self.__map to find the link which is
		# then removed by updating the links in the predecessor and successors.
		if key in self.__map:
			link = self.__map.pop(key)
			link.prev.next = link.next
			link.next.prev = link.prev

	def __iter__(self):
		# Traverse the linked list in order.
		root = self.__root
		curr = root.next
		while curr is not root:
			yield curr.key
			curr = curr.next

	def __reversed__(self):
		# Traverse the linked list in reverse order.
		root = self.__root
		curr = root.prev
		while curr is not root:
			yield curr.key
			curr = curr.prev

	def pop(self, last=True):
		if not self:
			raise KeyError('set is empty')
		key = next(reversed(self)) if last else next(iter(self))
		self.discard(key)
		return key

	def __repr__(self):
		if not self:
			return '%s()' % (self.__class__.__name__,)
		return '%s(%r)' % (self.__class__.__name__, list(self))

	def __eq__(self, other):
		if isinstance(other, OrderedSet):
			return len(self) == len(other) and list(self) == list(other)
		return not self.isdisjoint(other)


# test for interfaces with the tree structure
testTree = AbstractTree("TestRoot")
testTree("asdf").value = "firstKey"
testTree("parent").value = "nonas"
testTree("parent.childA").value = 930
testTree("parent.childA").extras["options"] = (930, "eyyy")
testTree("parent.childB").value = True

testTree["parent.testObj"] = saveObjectClass(testTree)

#testTree["parent.listEntry"] = "[eyyy, test, 4.3, [4e4, i, 33], 2e-10]"
# cannot do nested list inputs yet
testTree["parent.listEntry"] = "[eyyy, test, 4.3, 2e-10]"

if __name__ == '__main__':

	class NewTree(AbstractTree):
		branchesInherit = True
	class BreakTree(AbstractTree):
		branchesInherit = False

	newTree = NewTree("newTreeName", val=21)
	newTree["newTreeBranch.end"] = "jljlkjl"
	testTree.addChild(newTree)

	breakTree = BreakTree("breakTreeName", val="nope")
	breakTree["breakTreeBranch.end"] = "break this"
	testTree.addChild(breakTree)


	debug(newTree)
	#debug(testTree("parent").address)

	#print(testTree.display())
	loadedTree = AbstractTree.fromDict( testTree.serialise() )

	#print(loadedTree.display())

	print( loadedTree("parent.listEntry").value )
	print( loadedTree("parent.listEntry").listValue )
	print( loadedTree("parent.listEntry").listValue[-1] * 100)



	# for i in loadedTree.allBranches():
	# 	print(i)

	class Test(object):
		class _BoolRef(object):
			""" wrapper for consistent references to bool value """

			def __init__(self, val):
				self._val = val

			def __repr__(self):
				return self._val
			def __str__(self):
				return str(self._val)

			def __call__(self, *args, **kwargs):
				self._val = args[0]
		def __init__(self):
			self.var = self._BoolRef(False)
			self._prop = True
			self.map = [self.var, self.prop]


		@property
		def prop(self):
			return self._prop
		@prop.setter
		def prop(self, val):
			self._prop = val


	test = Test()
	print(test.var)
	test.map[0](True)
	print(test.var)
	if test.var:
		print("ye")

	print(test.prop)
	test.map[1] = False
	print(test.prop)

