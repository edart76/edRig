# # simple container for passing around functions and arguments
# # meta tactics would be sexier, but this is safer
# # always ensure safety before sexiness
# class ActionItem(object):
# 	def __init__(self, execDict=None, name="action"):
# 		self.items = [None] * 3  # func, args, kwargs
# 		self._name = name
# 		if not execDict:
# 			return
# 		for i, val in enumerate(["func", "args", "kwargs"]):
# 			self.items[i] = execDict[val] if val in execDict.keys() else None
#
# 	@property
# 	def func(self):
# 		return self.items[0]
#
# 	@func.setter
# 	def func(self, val):
# 		self.items[0] = val
#
# 	@property
# 	def args(self):
# 		return self.items[1]
#
# 	@property
# 	def kwargs(self):
# 		return self.items[2]
#
# 	@property
# 	def name(self):
# 		return self._name
#
# 	def execute(self):
# 		# not sexy at all but could be
# 		if not self.items[0]:
# 			raise RuntimeError("action {} has no function!".format(self._name))
# 		print "actionItem {} executing".format(self.name)
# 		if self.args or self.kwargs:
# 			if not self.args:
# 				self.func(**self.kwargs)
# 			elif not self.kwargs:
# 				self.func(*self.args)
# 			else:
# 				self.func(*self.args, **self.kwargs)
# 		else:
# 			self.func()
#
# 	@staticmethod
# 	def actionFromDict(actionDict, name="action"):
# 		return ActionItem(execDict=actionDict, name=name)
#
# 	def addAction(self, actionItem):
# 		"""convenience removing need for item/list checking every time"""
# 		newList = [self, actionItem]
# 		return ActionList(newList)
#
# 	@staticmethod
# 	def consolidateActionDicts(actionDicts=[]):
# 		"""assume any kind of dict, but will have action names as keys
# 		to leaf actionItems, and dicts must be of same depth
# 		retuns dict using actionLists for duplicate headings and actionItems
# 		otherwise"""
#
# 		def _mergeDicts(master=None, slave=None):
# 			print "master is {}, slave is {}".format(master, slave)
# 			for k, v in slave.iteritems():
# 				if k not in master.keys():
# 					master[k] = v
# 				elif isinstance(v, dict):
# 					# key exists in master, merge
# 					_mergeDicts(master=master[k], slave=v)
# 				elif isinstance(v, ActionItem) or isinstance(v, ActionList):
# 					master[k].addAction(v)
# 			pass
#
# 		masterDict = actionDicts.pop()
# 		for i in actionDicts:
# 			_mergeDicts(master=masterDict, slave=i)
# 		return masterDict
# 	# this will break if you sneeze on it, but not if you use it properly
#
#
# class ActionList(object):
# 	"""convenience for carting round multiple actions to be
# 	taken simultaneously
# 	expects a list of actionItems"""
#
# 	def __init__(self, actionList=[]):
# 		self._actions = actionList
#
# 	def executeAll(self):
# 		[i.execute() for i in self._actions]
# 		return
#
# 	def addAction(self, action):
# 		self._actions.append(action)
