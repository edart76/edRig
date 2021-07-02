from __future__ import annotations

import copy
from typing import List, Set, Dict, TYPE_CHECKING, Union
if TYPE_CHECKING:
	from edRig.tesserae.abstractnode import AbstractNode
	from edRig.tesserae.abstractgraph import AbstractGraph
	from edRig.tesserae.abstractedge import AbstractEdge

from weakref import WeakSet, WeakKeyDictionary, WeakValueDictionary

from edRig.lib.python import AbstractTree, Signal
from edRig.structures import DataStyle # still around for now, not hurting anything

class AbstractAttr(AbstractTree):
	""" trees to function as attributes for tesserae ops
	"""

	hTypes = ["leaf", "compound", "array", "root", "dummy"]


	accepts = {  # key accepts connections of type value
		"nD" : ["0D", "1D", "2D", "3D"],
		# this should probably be exposed to user per-attribute
	}
	branchesInherit = False

	def __init__(self, name="blankName", node=None, role="input", dataType="0D",
				 hType="leaf", desc="", default=None,
				 *args, **kwargs):
		super(AbstractAttr, self).__init__(name=name, val=default)

		# flags stored in normal dict key
		self.extras["flags"] = {}
		# don't know the best way to do this, leaving this for now

		self._node = node
		self.role = role
		self.default = default
		self.dataType = dataType
		self.hType = hType  # hierarchy type - leaf, compound, array, root, dummy

		self._plug = None

		self.extras["desc"] = desc

		# self.connections = [] # override with whatever the hell you want
		# edges saved separately by graph, not within attr tree

		self.connectionChanged = Signal()


		# default kwargs passed to attributes created through array behaviour
		self.childKwargs = {
			"name" : "newChildAttr",
			"role" : self.role,
			"dataType" : "0D",
			"hType" : "leaf",
			"desc" : "",
			"default" : None,
			"extras" : { "flags" : {}},
			"children" : {} # don't even try
		}

	@property
	def desc(self):
		return self.extras["desc"]

	@property
	def node(self)->"AbstractNode":
		""" points to abstractNode which owns this attr
		:rtype AbstractNode"""
		if self.parent:
			return self.parent.node
		return self._node


	@property
	def abstract(self)->"AbstractNode":
		return self.node

	@property
	def graph(self)->"AbstractGraph":
		return self.node.graph

	@property
	def connections(self)->Set[AbstractEdge]:
		"""edge register is maintained by Graph - this
		only indexes into it """
		return self.graph.attrEdgeMap[self] or set()
		#return self["connections"]
		#return self._connections


	@property
	def dataType(self):
		try:
			return self.extras["flags"]["dataType"]
		except Exception as e:
			print(("error getting datatype for attritem {}".format(self.name)))
			return "nD"
	@dataType.setter
	def dataType(self, val):
		self.extras["flags"]["dataType"] = val

	@property
	def hType(self):
		return self.extras["flags"].get("hType") or "leaf"
	@hType.setter
	def hType(self, val):
		self.extras["flags"]["hType"] = val

	@property
	def role(self):
		return self.extras["role"]
	@role.setter
	def role(self, val):
		self.extras["role"] = val

	# plug properties
	@property
	def plug(self):
		if self._plug is None:
			return None
		return self._plug()
	@plug.setter
	def plug(self, val):
		self._plug = val
		# not robust AT ALL, but enough for what we need

	# misc stuff
	@property
	def colour(self):
		return DataStyle[self.dataType]["colour"]



	# ---- main methods ---
	def addChild(self, newChild, **kwargs):
		newChild = super(AbstractAttr, self).addChild(newChild, **kwargs)
		newChild._node = self.node
		return newChild

	@property
	def children(self):
		return [i for i in self.branches if isinstance(i, AbstractAttr)]

	def isLeaf(self):
		return self.hType == "leaf"

	def isCompound(self):
		return self.hType == "compound"

	def isArray(self):
		return self.hType == "array"

	def isConnectable(self):
		return self.hType == "leaf" or self.hType == "compound"

	def getConnections(self):
		return self.connections

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
		level = self.getAllChildren() + [self]
		levelList = [i for i in level if i.isConnectable()]
		return levelList

	def getAllInteractible(self):
		level = self.getAllChildren() + [self]
		levelList = [i for i in level if i.isInteractible()]
		return levelList

	def addConnection(self, edge):
		"""ensures that input attributes will only ever have one incoming
		connection"""
		if edge in self.connections:
			#self.log("skipping duplicate edge on attr {}".format(self.name))
			print(( "skipping duplicate edge on attr {}".format(self.name) ))
			return
		if self.role == "output":
			self.connections.append(edge)
		else:
			self.connections = [edge]

	def delete(self):
		""" removes this attribute and all children
		from other attrs' connections
		might be better to use signal system"""
		for edge in self.getConnections():
			other = edge.oppositeAttr(self)
			other.connections.remove(edge)
		for i in self.getConnectedChildren():
			i.delete()


	def getConnectedAttrs(self):
		"""returns only connected AbstractAttrs, not abstractEdges -
		this should be the limit of what's called in normal api"""
		if self.role == "input":
			return [i.sourceAttr for i in self.getConnections()]
		elif self.role == "output":
			return [i.destAttr for i in self.getConnections()]

	def attrFromName(self, name):
		#print "attrFromName looking for {}".format(name)
		results = self.search(name)
		if results: return results[0]
		else: return

	### user facing methods
	def addAttr(self, name="", hType="leaf", dataType="0D",
				default=None, desc="", *args, **kwargs):
		#print "AbstractAttr addAttr name is {}".format(name)
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

			print(warn)
			return
		# what if target has children?
		for i in target.getChildren():
			target.removeAttr(i.name)
		for i in target.getConnections():
			conAttr = i["attr"]
			conAttr.connections = [i for i in conAttr.connections if i["attr"] != self]
		# remove attribute
		target.remove()

	# def remove(self, address=None):
	# 	""" also take care of removing """


	def copyAttr(self, name="new"):
		"""used by array attrs - make sure connections are clean
		AND NAMES ARE UNIQUE"""
		newAttr = copy.deepcopy(self)
		newAttr.name = name
		for i in newAttr.getAllChildren():
			i.connections = []
		return newAttr


	# ---- ARRAY BEHAVIOUR ----
	def setChildKwargs(self, name=None, desc="", dataType="0D", default=None,
					   extras=None):
		newKwargs = {}
		# this is disgusting i know
		newKwargs["name"] = name or self.childKwargs["name"]
		# newKwargs["hType"] == hType or self.childKwargs["hType"]
		newKwargs["desc"] = desc or self.childKwargs["desc"]
		newKwargs["dataType"] = dataType or self.childKwargs["dataType"]
		self.childKwargs.update(newKwargs)


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
		#print(( "newNames {}".format(newNames)))

		for i in excessChildren:
			self.remove(i)

		for i in newNames:
			#print(( "newName i {}".format(i)))
			nameSpec = [n for n in spec if n["name"] == i][0]
			kwargs = {}
			# override defaults with only what is defined in spec
			for k, v in self.childKwargs.items():
				kwargs[k] = nameSpec.get(k) or v
				# safer than update

			newAttr = AbstractAttr(**kwargs)
			#self.children.append(newAttr)
			self.addChild(newAttr)



class ArrayAttr(AbstractAttr):
	""" test for better array / compound behaviour """

	def __init__(self, name=None, val=None, node=None):
		super(ArrayAttr, self).__init__(name, val, node=node)

		self.extras["spec"] = []

	@property
	def spec(self):
		return self.extras["spec"]
	@spec.setter
	def spec(self, val):
		self.extras["spec"] = []

	def makeChildBranch(self, name=None, *args, **kwargs):
		return AbstractAttr(name=name, node=self.node,
		                    role=self.role, dataType=self.dataType,
		                    hType="leaf")

	# def matchBranchesToSequence(self, sequence,
	#                             create=True, destroy=True):
	# 	pass

	""" """
