
from edRig.lib.python import AbstractTree

class AttrItem(AbstractTree):
	""" trees to function as attributes for tesserae ops
	"""

	hTypes = ["leaf", "compound", "array", "root", "dummy"]


	accepts = {  # key accepts connections of type value
		"nD": ["0D", "1D", "2D", "3D"],
		# this should probably be exposed to user per-attribute
	}

	def __init__(self, node=None, role="input", dataType="0D",
				 hType="leaf", name="blankName", desc="", default=None,
				 *args, **kwargs):
		super(AttrItem, self).__init__(name=name, val=default)

		# flags stored in normal dict key
		self["flags"] = {}
		# don't know the best way to do this, leaving this for now

		self.node = node
		self.role = role
		self.default = default
		self.dataType = dataType
		self.hType = hType  # hierarchy type - leaf, compound, array, root, dummy

		self.desc = desc
		# self.extras = SafeDict(kwargs) # can't account for everything
		self.extras = kwargs

		self.connections = [] # override with whatever the hell you want
		self.colour = DataStyle[self.dataType]["colour"]

		self.connectionChanged = Signal()
		self.childrenChanged = Signal()

	# @property
	# def name(self):
	# 	return self._name
	#
	# @name.setter
	# def name(self, val):
	# 	self._name = val

	# @property
	# def children(self):
	# 	return self["children"]
	# @children.setter
	# def children(self, val):
	# 	self["children"] = val

	@property
	def connections(self):
		return self["connections"]
	@connections.setter
	def connections(self, val):
		self["connections"] = val

	@property
	def dataType(self):
		return self["flags"]["dataType"]

	@dataType.setter
	def dataType(self, val):
		self["flags"]["dataType"] = val

	@property
	def hType(self):
		return self["flags"].get("hType", default="leaf")

	@hType.setter
	def hType(self, val):
		self["flags"]["hType"] = val

	def isLeaf(self):
		return self.hType == "leaf"

	def isCompound(self):
		return self.hType == "compound"

	def isArray(self):
		return self.hType == "array"

	def isConnectable(self):
		#print "testing if {} is connectable".format(self.name)
		#print "attr hType is {}".format(self.hType)
		#print "result is {}".format(self.hType == "leaf" or self.hType == "compound")
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

	def addChild(self, newChild):
		if self.hType == "leaf":
			raise RuntimeError("CANNOT ADD CHILD ATTRIBUTES TO LEAF")

		super(AttrItem, self).addChild(newChild)
		if not isinstance(newChild, AttrItem):
			return newChild

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

	def getAllInteractible(self):
		level = self.getAllChildren()
		levelList = [i for i in level if i.isInteractible()]
		if self.isInteractible():
			levelList.append(self)
		return levelList

	# @staticmethod
	# def opHierarchyFromDict(fromDict, attrClass,
	#                         role="input", value=None, name="newAttr",):
	# 	"""used in deserialisation - pass the attr class to be generated"""
	# 	newAttr = attrClass(name=name, dataType=fromDict["dataType"],
	# 	                     hType=fromDict["hType"], value=value, role=role,
	# 	                     desc=fromDict["desc"])
	# 	if "children" in fromDict.keys():
	# 		for i in fromDict["children"]:
	# 			newAttr.addChild(attrClass.opHierarchyFromDict(i,
	# 				role=role, value=i["value"], name=i["name"]))
	# 	return newAttr

	# this is handled by normal deserialisation


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
		target.remove()


	def copyAttr(self, name="new"):
		"""used by array attrs - make sure connections are clean
		AND NAMES ARE UNIQUE"""
		newAttr = copy.deepcopy(self)
		newAttr.name = name
		for i in newAttr.getAllChildren():
			i.connections = []
		return newAttr


	def serialise(self, pretty=False):
		data = super(AttrItem, self).serialise(pretty)

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



class AbstractAttr(AttrItem):
	"""temp, will be rolled into the same object as above"""

	def __init__(self, *args, **kwargs):
		"""add maya-specific support, this inheritance is totally messed up"""
		super(AbstractAttr, self).__init__(*args, **kwargs)
		self._plug = None

		# default kwargs passed to attributes created through array behaviour
		self.childKwargs = {
			"name" : "newAttr",
			"role" : self.role,
			"dataType" : "0D",
			"hType" : "leaf",
			"desc" : "",
			"default" : None,
			"extras" : {},
			"children" : {} # don't even try
		}
		# TECHNICALLY recursion is now possible

	# plug properties
	@property
	def plug(self):
		return self._plug()
	@plug.setter
	def plug(self, val):
		self._plug = val
	# not robust AT ALL, but enough for what we need

	def setChildKwargs(self, name=None, desc="", dataType="0D", default=None,
					   extras=None):
		newKwargs = {}
		# this is disgusting i know
		newKwargs["name"] = name or self.childKwargs["name"]
		# newKwargs["hType"] == hType or self.childKwargs["hType"]
		newKwargs["desc"] = desc or self.childKwargs["desc"]
		newKwargs["dataType"] = dataType or self.childKwargs["dataType"]
		self.childKwargs.update(newKwargs)

	def addConnection(self, edge):
		"""ensures that input attributes will only ever have one incoming
		connection"""
		if edge in self.connections:
			#self.log("skipping duplicate edge on attr {}".format(self.name))
			print( "skipping duplicate edge on attr {}".format(self.name) )
			return
		if self.role == "output":
			self.connections.append(edge)
		else:
			self.connections = [edge]

	def getConnectedAttrs(self):
		"""returns only connected attrItems, not abstractEdges -
		this should be the limit of what's called in normal api"""
		if self.role == "input":
			return [i.sourceAttr for i in self.getConnections()]
		elif self.role == "output":
			return [i.destAttr for i in self.getConnections()]


	def addChild(self, newChild):
		newChild = super(AbstractAttr, self).addChild(newChild)
		newChild.node = self.node
		return newChild
		#self.node.attrsChanged() # call from node

	@property
	def abstract(self):
		return self.node

	def addFreeArrayIndex(self, arrayAttr):
		"""looks at array attr and ensures there is always at least one free index"""

	def matchArrayToSpec(self, spec=None):
		"""supplied with a desired array of names, will add, remove or
		rearrange child attributes
		this is because we can't just delete and regenerate the objects -
		edge references will be lost
		:param spec list of dicts:
		[ { name : "woo", hType : "leaf"}, ]
		etc
			"""

		# set operations first
		nameList = [i["name"] for i in spec]
		nameSet = set(nameList)
		childSet = {i.name for i in self.children}
		excessChildren = childSet - nameSet
		newNames = nameSet - childSet

		print( "newNames {}".format(newNames))

		for i in excessChildren:
			self.removeAttr(i)

		for i in newNames:
			print( "newName i {}".format(i))
			nameSpec = [n for n in spec if n["name"] == i][0]
			kwargs = {}
			# override defaults with only what is defined in spec
			for k, v in self.childKwargs.iteritems():
				kwargs[k] = nameSpec.get(k) or v
				# safer than update

			newAttr = AbstractAttr(**kwargs)
			self.children.append(newAttr)

		# lastly reorder children to match list
		newChildren = []
		for i in nameList:
			child = self.attrFromName(i)
			newChildren.append(child)
		self.children = newChildren
