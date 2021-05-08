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
			print (message)

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

# simple container for passing around functions and arguments
# meta tactics would be sexier, but this is safer
# always ensure safety before sexiness
class ActionItem(object):
	""" didn't know the word for it at the time
	but this is a janky partial """
	def __init__(self, execDict=None, name=None,
	             fn=None, args=None, kwargs=None):
		self.items = [None] * 3  # func, args, kwargs

		if fn is not None:
			self._name = name or fn.__name__
			self.items = [i for i in [fn, args, kwargs]]
			return

		self._name = name or execDict["func"].__name__
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
	

