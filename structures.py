# useful structures finding repeated use in ops and frameworks
from collections import MutableMapping, OrderedDict
import os, copy, functools
from edRig.lib.python import Signal, AbstractTree

# FilePathTree = FilePathTree # back compatibility

class DataAesthetics(object):
	"""set appearance for different datatypes"""
	data = { # RGB
		"default" : {"colour" : (90, 90, 90)},
		"nD" : {"colour" : (175, 175, 168)}, #grey
		"0D" : {"colour" : (239, 130, 40)}, # orange
		# "1D" : {"colour" : (40, 20, 239)}, # blue
		"1D": {"colour": (1, 12, 160)},  # must restrain urge
		# "2D" : {"colour" : (98, 19, 216)},# purple?
		"2D": {"colour": (198, 42, 27)},  # alternatively red?

	}

	def __getitem__(self, item):
		if item in self.data.keys():
			return self.data[item]
		else:
			return self.data["default"]
DataStyle = DataAesthetics()

class EnvironmentSettings(object):
	"""persistent class, containing any common variables
	needed by all elements of a program"""

	def __init__(self):
		self.logger = None
		self.logMethod = None

	def log(self, message, **kwargs):
		"""destined to be overridden by proper logging system"""
		if self.logMethod:
			self.logMethod(message, **kwargs)
		else:
			print message

class AttributeWrapper(object):
	"""might be useful idk"""

class Completer(object):
	"""passed to any ui searchbars that support autocompletion"""
	def __init__(self, items=[]):
		self.items = [str(i) for i in items]
		self.itemDict = {i : None for i in items}

	def addItem(self, item):
		item = str(item)
		if not item in self.items:
			self.items.append(item)

	def getSorted(self):
		return sorted(self.items)

class AttrItem(AbstractTree):
	"""base used to define a tree of connectable attributes
	consider eventually inheriting from abstractTree
	does not inherit properly yet, need to conform addChild, branches etc
	"""

	hTypes = ["leaf", "compound", "array", "root", "dummy"]

	def __init__(self, node=None, role="input", dataType="0D",
	             hType="leaf", name="blankName", desc="", default=None,
	             *args, **kwargs):
		super(AttrItem, self).__init__(name=name, val=default)
		self.node = node
		self.role = role
		self.default = default
		self.children = []
		self._dataType = dataType
		self._hType = hType  # hierarchy type - leaf, compound, array, root, dummy

		self.desc = desc
		# self.extras = SafeDict(kwargs) # can't account for everything
		self.extras = kwargs

		self.connections = [] # override with whatever the hell you want
		self.colour = DataStyle[self.dataType]["colour"]

		self.connectionChanged = Signal()
		self.childrenChanged = Signal()

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, val):
		self._name = val

	@property
	def dataType(self):
		return self._dataType

	@dataType.setter
	def dataType(self, val):
		self._dataType = val

	@property
	def hType(self):
		return self._hType

	@hType.setter
	def hType(self, val):
		self._hType = val

	@property
	def value(self):
		if not self._value and self.default:
			return self.default
		return self._value

	@value.setter
	def value(self, val):
		oldVal = self._value
		self._value = val
		if not oldVal == self._value:
			self.valueChanged( (self, self._value) )

	def isLeaf(self):
		return self.hType == "leaf"

	def isCompound(self):
		return self.hType == "compound"

	def isArray(self):
		return self.hType == "array"

	def isConnectable(self):
		return self.hType == "leaf" or self.hType == "compound"

	def isSimple(self):
		"""can attr be set simply by user in ui?"""
		simpleTypes = ["int", "float", "string", "enum", "colour", "boolean"]
		if any(self.dataType == i for i in simpleTypes):
			return True
		return False


	def isInteractible(self):
		"""not all ui widgets should be connectable"""
		return self.isConnectable() or self.isDummy()

	def isDummy(self):
		"""used if you want input functionality but not an actual connection
		not recommended"""
		return  self.hType == "dummy"

	def isMulti(self):
		"""alright this is kind of getting away from me but this is used
		to allow multiple connections to a single input
		it's literally just for skinOp"""
		return self.extras["multi"]

	def addChild(self, newChild):
		if self.hType == "leaf":
			raise RuntimeError("CANNOT ADD CHILD ATTRIBUTES TO LEAF")
		if not newChild.hType:
			newChild.hType = "leaf"
		self.children.append(newChild)
		newChild.parent = self
		return newChild

	def getChildren(self):
		if self.isLeaf():
			return []
		return sorted(self.children)

	def getAllChildren(self):
		allChildren = []
		level = self.getChildren()
		for i in level:
			if not i.isLeaf():
				allChildren += i.getAllChildren()

			allChildren.append(i)
		#print "{} getAllChildren is {}".format(self.name, allChildren)
		return allChildren

	def getConnectedChildren(self):
		return [i for i in self.getChildren() if i.getConnections()]

	def getAllLeaves(self):
		level = self.getAllChildren()
		return [i for i in level if i.isLeaf()]

	def getAllConnectable(self):
		level = self.getAllChildren()
		levelList = [i for i in level if i.isConnectable()]
		if self.isConnectable():
			levelList.append(self)
		return levelList

	def getConnections(self):
		return self.connections

	def setConnections(self, val):
		self.connections = val


	def getAllInteractible(self):
		level = self.getAllChildren()
		levelList = [i for i in level if i.isInteractible()]
		if self.isInteractible():
			levelList.append(self)
		return levelList

	@staticmethod
	def opHierarchyFromDict(fromDict, attrClass,
	                        role="input", value=None, name="newAttr",):
		"""used in deserialisation - pass the attr class to be generated"""
		newAttr = attrClass(name=name, dataType=fromDict["dataType"],
		                     hType=fromDict["hType"], value=value, role=role,
		                     desc=fromDict["desc"])
		if "children" in fromDict.keys():
			for i in fromDict["children"]:
				newAttr.addChild(attrClass.opHierarchyFromDict(i,
					role=role, value=i["value"], name=i["name"]))
		return newAttr


	def attrFromName(self, name):
		#print "attrFromName looking for {}".format(name)
		if self.name == name:
			return self
		elif self.getChildren():
			results = [i.attrFromName(name) for i in self.getChildren()]
			return next((i for i in results if i), None)
		else:
			return None

	### user facing methods
	def addAttr(self, name="", hType="leaf", dataType="0D",
	            default=None, desc="", *args, **kwargs):
		#print "attrItem addAttr name is {}".format(name)
		if self.isLeaf():
			raise RuntimeError("CANNOT ADD ATTR TO LEAF")
		# check if attr of same name already exists
		if self.attrFromName(name):
			raise RuntimeError("ATTR OF NAME {} ALREADY EXISTS".format(name))
		newAttr = self.__class__(name=name, hType=hType, dataType=dataType,
		                     default=default, role=self.role, desc=desc,
		                     *args, **kwargs)
		self.addChild(newAttr)
		return newAttr

	def removeAttr(self, name):
		# first remove target from any attributes connected to it
		target = self.attrFromName(name)
		if not target:
			warn = "attr {} not found and cannot be removed, skipping".format(name)

			print warn
			return
		# what if target has children?
		for i in target.getChildren():
			target.removeAttr(i.name)
		for i in target.getConnections():
			conAttr = i["attr"]
			conAttr.connections = [i for i in conAttr.connections if i["attr"] != self]
		# remove attribute
		self.children = [i for i in self.getChildren() if i.name != name]
		# THE DOWNSIDE: when messing with live attributes, everything updates live
		# cannot say when to refresh connections. user must be careful when deleting

	def copyAttr(self, name="new"):
		"""used by array attrs - make sure connections are clean
		AND NAMES ARE UNIQUE"""
		newAttr = copy.deepcopy(self)
		newAttr.name = name
		for i in newAttr.getAllChildren():
			i.connections = []
		return newAttr

	def getExtra(self, lookup):
		"""get enum options and other stuff"""
		return self.extras[lookup]

	def delete(self):
		# self.__delattr__("connections")
		# self.__delattr__("value")
		for i in self.children:
			i.delete()
		del self

	def serialise(self):
		# for i in self.getConnections():
		# 	i["attr"] = i["attr"].name
		returnDict = {"hType" : self.hType,
		              "dataType" : self.dataType,
		              "role" : self.role,
		              "value" : self.value if isinstance(self.value, (int, str, float)) else None,
		              #"connections" : self.getConnections(), # managed by graph
		              "children" : [i.serialise() for i in self.getChildren()],
		              "name" : self.name,
		              "desc" : self.desc,
		              "extras" : self.extras
		              }
		return returnDict

	@classmethod
	def fromDict(cls, fromDict, node=None):
		if not fromDict:
			return

		newItem = cls(role=fromDict["role"], node=node)
		newItem.name = fromDict["name"]
		newItem.dataType = fromDict["dataType"]
		newItem.hType = fromDict["hType"]
		newItem.value = fromDict["value"]
		#newItem.connections = fromDict["connections"] # tracked by graph
		newList = [newItem.fromDict(i, node=node) for i in fromDict["children"]]
		for i in newList:
			newItem.addChild(i)
		newItem.extras = fromDict["extras"]
		newItem.desc = fromDict["desc"]
		return newItem


# simple container for passing around functions and arguments
# meta tactics would be sexier, but this is safer
# always ensure safety before sexiness
class ActionItem(object):
	def __init__(self, execDict=None, name=None):
		self.items = [None] * 3  # func, args, kwargs
		self._name = name or execDict["func"].__name__
		if not execDict:
			return
		# this can just be passed a function
		elif not isinstance(execDict, dict):
			self.items[0] = execDict
			return
		for i, val in enumerate(["func", "args", "kwargs"]):
			self.items[i] = execDict[val] if val in execDict.keys() else None

	@property
	def func(self):
		return self.items[0]

	@func.setter
	def func(self, val):
		self.items[0] = val

	@property
	def args(self):
		return self.items[1]

	@property
	def kwargs(self):
		return self.items[2]

	@property
	def name(self):
		return self._name

	def execute(self):
		# not sexy at all but could be
		if not self.items[0]:
			raise RuntimeError("action {} has no function!".format(self._name))
		#print "actionItem {} executing".format(self.name)
		if self.args or self.kwargs:
			if not self.args:
				self.func(**self.kwargs)
			elif not self.kwargs:
				self.func(*self.args)
			else:
				self.func(*self.args, **self.kwargs)
		else:
			self.func()

	@staticmethod
	def actionFromDict(actionDict, name="action"):
		return ActionItem(execDict=actionDict, name=name)

	def addAction(self, actionItem):
		"""convenience removing need for item/list checking every time"""
		newList = [self, actionItem]
		return ActionList(newList)

	@staticmethod
	def consolidateActionDicts(actionDicts=[]):
		"""assume any kind of dict, but will have action names as keys
		to leaf actionItems, and dicts must be of same depth
		retuns dict using actionLists for duplicate headings and actionItems
		otherwise"""

		def _mergeDicts(master=None, slave=None):
			#print "master is {}, slave is {}".format(master, slave)
			for k, v in slave.iteritems():
				if k not in master.keys():
					master[k] = v
				elif isinstance(v, dict):
					# key exists in master, merge
					_mergeDicts(master=master[k], slave=v)
				elif isinstance(v, ActionItem) or isinstance(v, ActionList):
					master[k].addAction(v)
			pass

		masterDict = actionDicts.pop()
		for i in actionDicts:
			_mergeDicts(master=masterDict, slave=i)
		return masterDict
	# this will break if you sneeze on it, but not if you use it properly


# def action(name=None):
# 	"""add any function to right-click action menus - at INSTANCE level
# 	intercept "self" argument from wrapped function"""
# 	inst = None
# 	print
# 	print "ADDING ACTION"
# 	def _addAction(func):
# 		newName = name or func.__name__
# 		inst = func.im_self
# 		@functools.wraps(func)
# 		def wrapperAction(*args, **kwargs):
# 			#inst = args[0]
# 			return func(*args, **kwargs)
# 		print
# 		print "inst is {}".format(inst)
# 		inst.actions.update({newName: ActionItem(
# 			{"func": func}, name=newName)})
# 		return wrapperAction
# 	print "inst is {}".format(inst)
# 	return _addAction
#
# """override at instance level: def action(self, *args, **kwargs):
# 	return assignAction(self, *args, **kwargs)"""

# def action(cls, name=None):
# 	"""outer decorator, taking """
# class action(object):
# 	"""decorator class for adding common actions to a class"""


# def action(self, ):
# 	"""decorator"""
# 	return assignAction(self, *args, **kwargs)

class ActionList(object):
	"""convenience for carting round multiple actions to be
	taken simultaneously
	expects a list of actionItems
	DEPRECATED, use actionBranch instead"""

	def __init__(self, actionList=[]):
		self._actions = actionList

	def getActions(self):
		return self._actions

	def executeAll(self):
		[i.execute() for i in self.getActions()]
		return

	def execute(self):
		[i.execute() for i in self.getActions()]
		return

	def addAction(self, action, func=None):
		# need to add better processing for concatenating groups of actions
		if isinstance(action, ActionList):
			for i in action.getActions():
				self.addAction(i)
		self._actions.append(action)


class ActionBranch(object):
	"""used to recursively build trees of action items"""
	def __init__(self, actionStuff=None, name="newBranch"):
		self.name = name
		self.children = self.buildChildren(actionStuff)
		self.leaves = []

	def buildChildren(self, items):
		"""recursively build a tree of items to feed to qmenu, dict or whatever"""





""" consider the pattern of
{keyA : {
	keyA1 : value,
	keyA2 : value
	},
keyB : {
	keyB2 : value,
	keyB3 : value
	} }
this is a common data structure, but in order to process headings, to work out
the internal structure, is necessary to convert to this:
{keyA : [keyA1, keyA2],
keyB : [keyB2, keyB3] }

conversion is involved, iteration is involved, a check is involved to process recursive structures,
it's a nightmare.

consider instead (for simple string keys at least), simply setting all leaf dict values to None
before processing. something to bear in mind for abstractTree

how would you iterate over a fully fractal structure, how would you interact with it?
without involving code generation too much, consider:

def iterate(tree, func) ? # apply function to every factorial combination of entries
	and within func, can access certain local variables parent, children, next, last, root, leaves etc?
	
	by nature it has to be more involved than a simple generator


"""
	

