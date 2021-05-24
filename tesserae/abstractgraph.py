# manages connectivity and execution order of a dag graph


import pprint
from weakref import WeakSet, WeakValueDictionary
from collections import defaultdict
from typing import List, Callable, Dict, Union, Set, TYPE_CHECKING
from functools import partial
from enum import Enum
from importlib import reload
from tree import Tree, Signal

from edRig import ROOT_PATH, pipeline, naming
#from edRig.lib.python import Signal
from edRig.lib.python import AbstractTree
from edRig.pipeline import TempAsset
from edRig.tesserae.abstractnode import AbstractNode, AbstractAttr
from edRig.tesserae.abstractedge import AbstractEdge
from edRig.tesserae.lib import GeneralExecutionManager
from edRig.structures import ActionItem


class ExecutionPath(object):
	"""class describing a sequential path through the graph"""
	def __init__(self, graph=None):
		self.sequence = []
		self.graph = graph
		self.seedNodes = set() # nodes with no history
		self.passedNodes = set() # nodes passed by query
		self.boundaryNodes = set()
		self.allNodes = set() # safety

		self.currentIndex = 1 # never less than 1

	"""this could also store execution indices, but only if we need
	things like 'build all plan stages, then all run stages' etc"""


	@property
	def nodeSet(self):
		"""returns set of nodes in sequence"""
		return set(self.sequence)

	def getSeedNodes(self, starters):
		"""returns the seed nodes for a set of nodes"""
		allHistory = self.graph.getCombinedHistory(starters)
		for i in [n for n in starters if not n.history]:
			allHistory = allHistory.union({i}) # add nodes
		seedNodes = self.graph.getSeedNodes()
		ourSeeds = seedNodes.intersection(allHistory)
		return ourSeeds

	def resetIndices(self):
		for i in self.allNodes:
			i.index = None

	def setNodes(self, targets):
		"""initialise path with various known values"""
		self.passedNodes = set(targets)
		self.seedNodes = self.getSeedNodes(targets)

		# safety
		self.boundaryNodes = self.passedNodes.union(self.seedNodes)
		self.allNodes = self.boundaryNodes.union(self.graph.getNodesBetween(
			nodes=self.boundaryNodes))

	def buildToNodes(self):
		"""get order only containing targets' critical paths"""
		self.resetIndices()

		self.currentIndex = 1
		for i in self.seedNodes:
			self.setIndex(i)
			testSet = self.passedNodes.union({i})
			between = self.graph.getNodesBetween(testSet, include=True)
			for n in between:
				self.setIndexBranchSafe(n)
		# donezo????????????

	def setIndexBranchSafe(self, node):
		"""sets index of target, or looks back til it finds a node with an index"""
		if node.index:
			return
		for i in node.fedBy:
			if not i.index:
				self.setIndexBranchSafe(i)
		self.setIndex(node)

	def setIndex(self, node):
		"""sets node index to current index and increments"""
		if node.index: # super duper sketched out about this
			return
		node.index = self.currentIndex
		self.currentIndex += 1
		self.sequence.append(node) # sure why not

	@staticmethod
	def getExecPathToNodes(graph=None, targets=None):
		"""gets execution path to nodes"""
		path = ExecutionPath(graph)
		path.setNodes(targets)
		path.resetIndices()

		path.buildToNodes()
		return path

	@staticmethod
	def getExecPathToAll(graph=None):
		"""execute everything"""
		path = ExecutionPath(graph)
		path.setNodes(graph.nodes)
		path.resetIndices()
		path.buildToNodes() #?
		return path

class AbstractGraphExecutionManager(GeneralExecutionManager):
	"""manages context for entire execution process"""
	def __init__(self, graph):
		super(AbstractGraphExecutionManager, self).__init__(graph)
		self.graph = graph

	def __enter__(self):
		"""set graph state"""
		self.graph.setState("executing")
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""reset graph state"""
		if exc_type:
			self.graph.setState("neutral")
			# anything other than neutral freezes forever
			#raise exc_type(exc_val)
			#self.printTraceback(exc_type, exc_val, exc_tb)
		self.graph.setState("neutral")


class AbstractGraph2(AbstractTree):
	"""setting out the inheritance from AbstractTree
	abstractNodes and child graphs are BRANCHES.

	node groups might be value of branch 'groups'

	scripting tesserae should be as simple as
	>>>import tesserae
	>>>tesserae.graph.addNode("JointCurveOp")
	# node is added, ui updated automatically

	>>>tesserae.view.arrange()
	"""

	# register of all active graphs to async lookup and interaction
	graphRegister = AbstractTree(name="graphs")

	branchesInherit = False

	class State(Enum): # graph states
		neutral = "neutral"
		executing = "executing",
		complete = "complete",
		failed = "failed",
		approved = "approved"

	class EdgeEvents(Enum):
		added = "added"
		removed = "removed"

	states = State._member_names_[:]

	# reserved names for graph components,
	# not to be used for node names
	reservedKeys = ["nodeGroups", "nodeMemory", "edges"]



	def __init__(self, #parent=None,
	             name="main"):
		super(AbstractGraph2, self).__init__(name=name)

		self.graphName = name
		self.parent = None
		# add to register
		# we ignore parent on initialisation
		self.graphRegister[self.graphName] = self

		self.nodeGraph = {} # node catalogue indexed by UID
		"""{1040 : {
				"node" : AbstractNode,
				"feeding" : set() # list of nodes fed by outputs
				"fedBy" : set(), # same but backwards
				}
			}

		this is intended for very quick and easy traversal of the graph
		tuples of nodes and attrs stored by edges
				"""

		"""
		# reorganise edges to more literal system
		# single map of edges, everything else indexes into it if needed
		
		
		"""

		self.edges = set() # single source of truth on edges

		def _edgeItemFactory():
			return WeakSet()

		# self.attrEdgeMap = WeakValueDictionary() #type: Dict[AbstractAttr, AbstractEdge]
		# self.nodeEdgeMap = WeakValueDictionary() #type: Dict[AbstractNode, AbstractEdge]
		self.attrEdgeMap = defaultdict(_edgeItemFactory) #type: Dict[AbstractAttr, Set[AbstractEdge]]
		# self.nodeEdgeMap = defaultdict(_edgeItemFactory)

		#self.edges = []
		self.selectedNodes = []
		self.nodeSets = {}

		self.registeredNodes = {} # dict of className : class

		self.initGraph()

		self.state = "neutral"
		"""used to check if execution is in progress; prevents any change to topology
		if it is. states are neutral, executing, (routing, for massive graphs?)"""


		# signals
		self.sync = Signal()
		# edgesChanged signature : edge object, event type
		self.edgesChanged = Signal()
		self.stateChanged = Signal()
		self.nodeChanged = Signal()
		# nodeSetsChanged signature : node set, event type
		self.nodeSetsChanged = Signal()
		self.wireSignals()

	# serialised special graph attributes
	@property
	def nodeMemory(self):
		return self("nodeMemory")

	@property
	def edges(self)->Set[AbstractEdge]:
		return self["edges"]
	@edges.setter
	def edges(self, val:Set[AbstractEdge]):
		self["edges"] = val

	@property
	def nodeSets(self):
		return self["nodeSets"]
	@nodeSets.setter
	def nodeSets(self, val):
		self["nodeSets"] = val

	@property
	def nodes(self)->List[AbstractNode]:
		#return set(i["node"] for i in list(self.nodeGraph.values()))
		return [i for i in self.branches if not i.name in self.reservedKeys]

	def log(self, message):
		print(message)

	def setAsset(self, assetItem):
		self._asset = assetItem

	def clearSession(self):
		self.nodeGraph.clear()
		self.edges = []

	# signals
	def onNodeAttrsChanged(self, node):
		"""checks if any connections to node are now invalid"""
		legal = self.checkNodeConnections(node)
		if not legal:
			self.edgesChanged()
		self.nodeChanged(node)

	def wireSignals(self):
		"""as usual, sync drives everything"""
		self.sync.connect(self.edgesChanged)
		self.sync.connect(self.stateChanged)
		# self.sync.connect(self.nodeChanged) # not yet, no specific node

	@property
	def asset(self):
		if self.parent:
			return self.parent.asset
		else:
			return self._asset

	@property
	def dataPath(self):
		# self.log("graph datapath, asset is {}, path is {}".format(
		# 	self.asset, self.asset.dataPath) )
		if self.asset:
			return self.asset.dataPath

		return ROOT_PATH+"/temp/tempData"

	def registerNodeClasses(self):
		"""generates abstract class for each known real class"""
		for i in self.realClasses:
			abstractClass = AbstractNode.generateAbstractClass(i)
			self.registeredNodes[i.__name__] = abstractClass

	@property
	def registeredClassNames(self):
		return [i for i in list(self.registeredNodes.keys())]

	@property
	def knownUIDs(self):
		return list(self.nodeGraph.keys())

	@property
	def knownNames(self):
		return [i["node"].nodeName for i in list(self.nodeGraph.values())]

	### region node creation and deletion

	def createNode(self, nodeType="", real=None)->AbstractNode:
		"""accepts string of node class name to create
		does not directly add node to graph
		:param real : optional existing real class"""

		if not nodeType in self.registeredClassNames:
			raise RuntimeError("nodeType "+nodeType+" not registered in graph")
		newAbsClass = self.registeredNodes[nodeType]
		newAbsInstance = newAbsClass(
			self, name=newAbsClass.__name__, realInstance=real)
		return newAbsInstance


	def addNode(self, node:Union[str, AbstractNode])->AbstractNode:
		"""adds a node to the active graph"""
		if self.state != "neutral":
			self.log ("cannot add node during execution")
			return

		if isinstance(node, str):
			node = self.createNode(nodeType=node)

		if node.uid in self.knownUIDs:
			print("uid {} already exists, retrying".format(node.uid))
			node.uid += 1
			return self.addNode(node)
		elif node.nodeName in self.knownNames:
			newName = naming.incrementName(node.nodeName, currentNames=self.knownNames)
			node.rename(newName)
		# self.nodeGraph[node.uid] = {
		# 	"node" : node,
		# 	"feeding" : set(), # lists of AbstractNodes, use methods to process
		# 	"fedBy" : set(), # only single level
		# }

		# add node as branch
		self.addChild(node)

		return node

	def deleteNode(self, node):
		if self.state != "neutral":
			return False
		# entry = self.getNode(node, entry=True)
		#
		# node = entry["node"]
		for i in node.edges:
			self.deleteEdge(i)

		node.delete()
		# self.nodeGraph.pop(node.uid)
		# goodnight sweet prince
		del node

	#endregion

	### region node querying
	def nodesFromName(self, name):
		"""may by its nature return multiple nodes"""
		return [i for i in self.nodes if i.nodeName == name]

	def nodeFromUID(self, uid):
		# return self.nodeGraph[uid]["node"]
		return [i for i in self.nodes ]

	def getNode(self, node, entry=False)->Union[AbstractNode, Dict]:
		"""returns an AbstractNode object from
		an AbstractNode, node name, node UID, or AbstractAttr(?)
		:returns AbstractNode"""
		if isinstance(node, AbstractNode):
			node = node
		elif isinstance(node, str):
			node = self.nodesFromName(node)[0] # don't do this
		elif isinstance(node, int):
			node = self.nodeFromUID(node)
		elif isinstance(node, AbstractAttr):
			node = node.node
		elif isinstance(node, dict) and "node" in list(node.keys()): # node entry
			node = node["node"]
		# node is now absolutely definitely a node
		if not entry:
			return node
		return [i for i in list(self.nodeGraph.values()) if i["node"]==node][0]

	#endregion

	### region adding edges
	def addEdge(self, sourceAttr:AbstractAttr, destAttr:AbstractAttr, newEdge=None):
		"""adds edge between two attributes
		DOES NOT CHECK LEGALITY
		edges in future should not use bidirectional references -
		only inputs know their own drivers - outputs know nothing

		"""
		if self.state != "neutral":
			print("graph state is ", self.state, "skipping")

			return False

		self.log( "")
		self.log( " ADDING EDGE")
		newEdge = newEdge or AbstractEdge(
			source=sourceAttr, dest=destAttr, graph=self)

		# add edge to master edge set
		self.edges.add(newEdge)
		self.attrEdgeMap[sourceAttr].add(newEdge)

		# remove existing dest connections
		self.attrEdgeMap[destAttr].clear()
		self.attrEdgeMap[destAttr].add(newEdge)
		self.edgesChanged(newEdge, self.EdgeEvents.added)
		return newEdge


		# # in regeneration the edge object is already created
		# # remove existing connections to destAttr for now
		# # for edge in destAttr.connections:
		# # 	self.edges.remove(edge)
		# # destAttr.connections.clear()
		# # sourceAttr.addConnection(newEdge)
		# # destAttr.addConnection(newEdge)
		# # self.edges.append(newEdge)
		#
		# sourceAttr.node.outEdges.add(newEdge)
		# destAttr.node.inEdges.add(newEdge)
		# sourceEntry = self.getNode(sourceAttr.node, entry=True)
		# destEntry = self.getNode(destAttr.node, entry=True)
		#
		# sourceEntry["feeding"] = sourceEntry["feeding"].union({destAttr.node})
		# destEntry["fedBy"] = destEntry["fedBy"].union({sourceAttr.node})
		# self.log("source feeding is {}".format(sourceEntry["feeding"]))
		#
		# return newEdge

	def deleteEdge(self, edge):
		if self.state != self.State.neutral:
			return False
		# in theory this should be it
		self.edges.remove(edge)

		return

		# sourceNode = edge.source[0]
		# sourceEntry = self.getNode(sourceNode, True)
		# self.log("feeding before delete is {}".format(sourceEntry["feeding"]) )
		# if edge in self.edges:
		# 	self.edges.remove(edge)
		#
		# sourceNode = edge.source[0]
		# destNode = edge.dest[0]
		# sourceNode.outEdges.remove(edge)
		# destNode.inEdges.remove(edge)
		# # update entries how?
		# # WITH TOPOLOGY OF COURSE
		# # two nodes are disconnected if the whole sets of their edges are disjoint
		# if sourceNode.edges.isdisjoint(destNode.edges):
		# 	self.log("sets are disjoint")
		# 	sourceEntry = self.getNode(sourceNode, True)
		# 	destEntry = self.getNode(destNode, True)
		# 	#print "feeding is {}".format(sourceEntry["feeding"])
		# 	sourceEntry["feeding"].difference({destNode})
		# 	destEntry["fedBy"].difference({sourceNode})


	def nodeEdges(self, node:AbstractNode, outputs=False)->Set[AbstractEdge]:
		"""return either edges for either inputs or outputs
		could have done this directly on node object
		but seems easier to follow this way """
		edges = WeakSet()
		tree = node.outputRoot if outputs else node.inputRoot
		for i in tree.allBranches():
			edges.update(self.attrEdgeMap[i])
		return edges

	def adjacentNodes(self, node, future=True, history=True)->Set[AbstractNode]:
		"""return direct neighbours of node"""
		nodes = WeakSet()
		if future:
			for i in self.nodeEdges(node, outputs=True):
				nodes.add(i.destAttr.node)
		if history:
			for i in self.nodeEdges(node, outputs=False):
				nodes.add(i.sourceAttr.node)
		return nodes

	# endregion



	### region CONNECTIVITY AND TOPOLOGY ###
	def getNodesInHistory(self, node, entries=True):
		"""returns all preceding nodes"""
		return self.getInlineNodes(node, history=True,
		                           future=False, entries=entries)

	def getNodesInFuture(self, node, entries=True):
		"""returns all proceeding nodes"""
		return self.getInlineNodes(node, history=False,
		                           future=True, entries=entries)

	def getCombinedHistory(self, nodes):
		"""returns common history between a set of nodes"""
		history = set()
		for i in nodes:
			# history = history.union(i.history)
			history.update(self.getNodesInHistory(i))
		return history

	def getCombinedFuture(self, nodes, entries=False):
		"""returns common future between a set of nodes"""
		future = set()
		for i in nodes:
			future.update(self.getNodesInFuture(i))
		if not entries:
			return future

	def getInlineNodes(self, node, history=True, future=True)->Set[AbstractNode]:
		"""gets all nodes directly in the path of selected node
		forwards and backwards is handy way of working out islands"""
		inline = set()
		for n in self.adjacentNodes(node, history=history, future=future):
			inline.add(n)
			inline.update(self.getInlineNodes(node, history=history, future=future))
		return inline

	def getContainedEdges(self, nodes=None):
		"""get edges entirely contained in a set of nodes"""
		nodes = self.getNodesBetween(nodes, include=False)
		edges = set()
		for i in nodes:
			nodeEdges = self.nodeEdges(i, outputs=True).union(
				self.nodeEdges(i, outputs=False))
			edges = edges.union(nodeEdges)
			# imperfect - contained nodes may have escaping connections
		return edges

	def getSeedNodes(self):
		"""get nodes with no history
		do not trust them"""
		seeds = set()
		for i in self.nodes:
			# if not i.history:
			if not self.nodeEdges(i, outputs=False):
				seeds.add(i)
		return seeds

	def getEndNodes(self):
		"""get nodes with no future
		pity them"""
		lost = set()
		for i in self.nodes:
			if not i.future: # i know the feeling
				lost.add(i) # don't cry, it doesn't help
		return lost # things might not get better
		# but they can't get worse


	def checkLegalConnection(self, source, dest):
		"""checks that a connection wouldn't undermine DAG-ness"""
		if self.state != "neutral": # graph is executing
			return False
		if source.node.uid == dest.node.uid: # same node
			self.log("put some effort into it for god's sake")
			return False
		elif source in source.node.inputs or dest in dest.node.outputs:
			self.log("attempted connection in wrong order")
			return False
		elif source.node in dest.node.future:
			self.log("source node in destination's future")
			return False
		elif dest.node in source.node.history:
			self.log("dest node in source's past")
			return False
		return True

	def checkNodeConnections(self, node):
		"""called whenever attributes change, to check there aren't any
		dangling edges"""
		removeList = []
		for i in node.edges:
			if not any([n in node.outputs + node.inputs for
						n in [i.sourceAttr, i.destAttr]]):
				removeList.append(i)

		if removeList:
			for i in removeList:
				self.deleteEdge(i)
				self.edgesChanged()
			return False # going for semantics here
		return True



	def getNodesBetween(self, nodes=[], entry=False, include=True):
		"""get nodes only entirely contained by selection
		include sets whether to return passed nodes or not
		return node items"""
		starters = set(self.getNode(i, entry=False) for i in nodes)
		for i in starters:
			#""" do fancy topology shit """
			"""get all inline nodes for all search nodes
			if any node appears only in search history or only in search
			future,	cannot be contained. """

		allHistory = self.getCombinedHistory(starters)
		allFuture = self.getCombinedFuture(starters)

		betweenSet = allHistory.intersection(allFuture) # gg easy ????

		if include:
			betweenSet = betweenSet.union(nodes)
		else:
			betweenSet = betweenSet.difference(nodes)

		return betweenSet

	#endregion

	### region node execution ###
	def getExecPath(self, nodes):
		"""creates execution path from unordered nodes"""
		if nodes:
			newPath = ExecutionPath.getExecPathToNodes(self, nodes)
		else:
			newPath = ExecutionPath.getExecPathToAll(self)
		self.log("exec path is {}".format(i.nodeName for i in newPath.sequence))
		return newPath

	def executeNodes(self, nodes=None, index=-1):
		"""executes nodes in given sequence to given index"""

		execPath = self.getExecPath(nodes=nodes)
		#self.setState("executing")
		# enter graph-level execution state here
		with AbstractGraphExecutionManager(self):
			for i in execPath.sequence:
				nodeIndex = index
				if index == -1: # all steps
					nodeIndex = len(i.executionStages()) # returns ["plan", "build"] etc
				# for n in range(nodeIndex):
				# 	kSuccess = i.execute(index=n)
				"""currently no support for executing all nodes to stage n before
				all to n+1"""
				try:
					kSuccess = i.execToStage(index)
					# enter and exit node-level execution state
					self.log("all according to kSuccess")
				except RuntimeError("NOT ACCORDING TO KSUCCESS"):
					pass

		# exit graph-level execution
		#self.setState("neutral")
		self.log("execution complete")

	def resetNodes(self, nodes=None):
		"""resets nodes to pre-executed state"""
		if not nodes:
			nodes = self.nodes
		for i in nodes:
			i.reset()
		"""currently no support for specific order during reset, as in maya there
		is no need. however, it could be done"""
		self.sync()

	def reset(self):
		self.resetNodes(self.nodes)
		self.setState("neutral")
		self.stateChanged()

	def getExecActions(self, nodes=None):
		"""returns available execution actions for target nodes, or all"""
		return {"execute nodes" : ActionItem(execDict={
			"func" : self.executeNodes, "kwargs" : {"nodes" : nodes}},
			name="execute nodes"),
			"reset nodes": ActionItem(execDict={  # everything
				"func": self.resetNodes, "kwargs" : {"nodes" : nodes}},
				name="reset nodes"),
			"rig it like you dig it" : ActionItem(execDict={ # everything
				"func" : self.executeNodes}, name="rig it like you dig it"),
			"reset all": ActionItem(execDict={  # everything
				"func": self.reset}, name="reset all")
		}

	def setState(self, state):
		"""didn't know this was also a magic method but whatevs"""
		if not state in self.states:
			raise RuntimeError("tried to set invalid state {}".format(state))
		self.state = state
		self.stateChanged()

	#endregion


	### region node sets
	@property
	def nodeSetNames(self):
		return list(self.nodeSets.keys())

	def addNodeToSet(self, node, setName):
		"""adds node to set - creates set if it doesn't exist
		:param node : AbstractNode
		:param setName : str"""
		origSet = self.nodeSets.get(setName)
		if not origSet:
			self.nodeSets[setName] = set()
		self.nodeSets[setName].add(node)

	def removeNodeFromSet(self, node, setName):
		""":param node : AbstractNode
		:param setName : str"""
		targetSet = self.nodeSets.get(setName)
		if not targetSet:
			# i aint even mad
			self.log("target set {} not found".format(setName))
			return
		if not node in targetSet:
			# you aint even mad
			self.log("target node {} not in set {}".format(node.nodeName, setName))
			return
		targetSet.remove(node)

		if not targetSet:
			# we aint even mad?
			self.nodeSets.pop(setName)

	def getNodesInSet(self, setName):
		nodes = set()
		targetSet = self.nodeSets.get(setName)
		if targetSet:
			nodes = {i for i in targetSet}
		return nodes

	def getSetsFromNode(self, node):
		node = self.getNode(node)
		sets = set()
		for i in self.nodeSets.items():
			if node in i[1]:
				sets.add(i)
	# endregion

	### region node memory
	def getNodeMemoryCell(self, node):
		""" retrieves or creates key in memory dict of
		uid : {
			name : node name,
			data : node memory """

		uid = self.getNode(node).uid
		return self.nodeMemory.get(uid) or self.makeMemoryCell(node)

	def makeMemoryCell(self, node):
		node = self.getNode(node)
		cell = self.nodeMemory(node.uid)
		cell["nodeName"] = node.nodeName
		cell("data")

		return cell


	def initGraph(self):
		"""override for specific implementations"""
		from edRig.tesserae.oplist import ValidList

		# register real classes that nodes can represent
		self.realClasses = ValidList.ops
		self.registerNodeClasses()
		self._asset = TempAsset # maybe?

	# endregion

	# region serialisation and regeneration
	def serialise(self):
		"""oof ouchie"""
		graph = {"nodes" : {},
		         "edges" : [],
		         "name" : self.graphName,
		         "asset" : self.asset.name,
		         "memory" : self.nodeMemory.serialise(),
		         }
		for uid, entry in self.nodeGraph.items():
			graph["nodes"][uid] = entry["node"].serialise()
			# don't worry about fedBy and feeding - these will be reconstructed
			# from edges
		graph["edges"] = [i.serialise() for i in self.edges]
		graph["nodeSets"] = {k : [i.nodeName for i in v] for k, v in self.nodeSets.items()}
		# add another section for groupings when necessary

		return graph

	@staticmethod
	def fromDict(regen):
		"""my bones"""

		newGraph = AbstractGraph(name=regen["name"]) # parent will be tricky
		# regen memory
		memory = AbstractTree.fromDict(regen["memory"])
		newGraph.addChild(memory, force=True)

		if "asset" in list(regen.keys()):
			newGraph.setAsset(pipeline.assetFromName(regen["asset"]))
		for uid, nodeInfo in regen["nodes"].items():
			newNode = AbstractNode.fromDict(nodeInfo, newGraph)
			newNode.uid = uid
			newGraph.addNode(newNode)
		for i in regen["edges"]:
			newEdge = AbstractEdge.fromDict(i, newGraph)
			newGraph.addEdge(sourceAttr=newEdge.sourceAttr,
			                 destAttr=newEdge.destAttr, newEdge=newEdge)
		for k, v in regen["nodeSets"]:
			newGraph.nodeSets[k] = set([newGraph.getNode(n) for n in v])
		return newGraph

	# endregion

	### initial startup when tesserae is run for the first time
	#@staticmethod
	@classmethod
	def startup(cls, name="main"):
		"""returns a fresh graph object"""
		# do other stuff if necessary
		return cls(name=name)

AbstractGraph = AbstractGraph2