
from __future__ import annotations
from typing import List, Dict, Union, TYPE_CHECKING, Set

from weakref import WeakSet, WeakValueDictionary

# container interfacing with the graph - concerned with connections
from edRig.structures import ActionItem
from edRig.core import shortUUID
from edRig import pipeline
# from edRig.tesserae.ops.op import Op

from edRig.tesserae.abstractattr import AbstractAttr
from edRig.tesserae.lib import GeneralExecutionManager
from edRig.lib.python import Signal, AbstractTree, \
	loadObjectClass

if TYPE_CHECKING:
	from edRig.tesserae.abstractgraph import AbstractGraph, AbstractEdge

# temp, find a better order for this
from edRig.tesserae.ops.memory import Memory2


# test
#from edRig.expression import EVALUATOR
#EVALUATOR = None

class AbstractAbstractNode(type):
	"""abstract class for abstract nodes"""
	def __new__(cls, *args, **kwargs):
		return cls

class AbstractNodeExecutionManager(GeneralExecutionManager):
	"""manages abstract execution, updates ui, etc"""
	def __init__(self, node):
		super(AbstractNodeExecutionManager, self).__init__(node)
		self.node = node

	def __enter__(self):
		self.node.reset()
		self.node.beforeExecute()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			self.node.afterExecute(success=False)
			print( "")
			print ("node {} encountered error during execution".format(self.node.nodeName))
			print ("error is {}".format(exc_val))
			#self.node.setState("failed")


			# we want execution to stop in this case
			#raise exc_type(exc_val)
			#self.printTraceback(exc_type, exc_val, exc_tb)
		else:
			self.node.afterExecute(success=True)
			#self.node.setState("complete")

class AbstractNode(AbstractTree):
	"""abstract node managed by abstract graph
	interfaces with direct operations, and with UI"""

	defaultName = "basicAbstract"
	realClass = None
	states = ["neutral", "executing", "complete", "failed", "approved", "guides"]

	#evaluatorClass = EVALUATOR

	@classmethod
	def nodeType(cls):
		"""for use in managing instantiation"""
		return cls.__name__

	@classmethod
	def setRealClass(cls, realClass):
		cls.realClass = realClass

	def __init__(self, graph, name=None, realInstance=None):
		"""this is where the spaghetti begins"""
		self.real = None
		self.nodeName = name or self.defaultName + shortUUID(2)
		
		super(AbstractNode, self).__init__(name=self.nodeName)

		self.uid = shortUUID(8)
		self._graph = graph
		self.state = "neutral"

		"""initialise attribute hierarchy"""
		self.inputRoot = AbstractAttr(node=self, role="input", dataType="null",
		                              hType="root", name="inputRoot")
		self.outputRoot = AbstractAttr(node=self, role="output", dataType="null",
		                              hType="root", name="outputRoot")

		# signals
		self.sync = Signal()
		self.attrsChanged = Signal()
		self.attrValueChanged = Signal() # emit tuple of attrItem, value
		self.stateChanged = Signal()
		self.nodeNameChanged = Signal()
		self.connectionsChanged = Signal()
		self.nodeChanged = Signal()
		self.wireSignals()

		self.extras = {}
		# self.inEdges = set() #type:Set["AbstractEdge"]
		# self.outEdges = set() #type:Set["AbstractEdge"]

		self.index = None # execution order index

		"""right click actions for ui"""
		self.actions = {}
		self.addAction(actionItem=ActionItem(execDict={"func" : self.setApproved},
		                                     name="set approved"))
		self.addAction(actionItem=ActionItem(execDict={"func" : self.recastReal},
		                                     name="recast real"))
		self.dataFileExists = False
		#self.real.setAbstract(self)


		self.initSettings()

		self.makeReal(realInstance)

		# ui stuff
		self.pos = [0,0]
		self.colour = self.real.colour
		# self.redraw = False
		# colour-changing nodes could be done if you make this a property
		self.ui = None # reference to AbstractTile for this node

		pass

	@property
	def graph(self)->"AbstractGraph":
		""" i can't make tensorflow go away
		:returns AbstractGraph"""
		return self._graph
	@graph.setter
	def graph(self, val:"AbstractGraph"):
		self._graph = val

	@property
	def inEdges(self)->Set["AbstractEdge"]:
		"""look up edges in graph"""
		return self.graph.nodeEdges(self, outputs=False)

	@property
	def outEdges(self) -> Set["AbstractEdge"]:
		"""look up edges in graph"""
		return self.graph.nodeEdges(self, outputs=True)

	@property
	def feeding(self)-> Set[AbstractNode]:
		""" all nodes in this node's direct history
		might get a bit pricey but
		not a problem for now """
		return self.graph.adjacentNodes(self, future=True)

	@property
	def fedBy(self) -> Set[AbstractNode]:
		""" all nodes in this node's direct history
		might get a bit pricey but
		not a problem for now """
		return self.graph.adjacentNodes(self, history=True)

	@property
	def data(self):
		""" returns a corresponding graph data slot
		works off uid
		abstractNodes only have access to data - graph may know more
		:rtype AbstractTree """
		data = self.graph.getNodeMemoryCell(self)
		# check that memory class is placed correctly
		# temp
		if not data.get("memory"):
			print("did not find memory cell, creating new")
			memory = Memory2()
			data.addChild(memory)
		return data


	def makeReal(self, realInstance):
		"""creates and or binds real instance to abstract"""
		# real interface
		self.real = None
		if realInstance:
			real = realInstance
		else:
			real = self.instantiateReal(name=self.nodeName)
		self.setRealInstance(real)


	def wireSignals(self):
		"""sets up signal hierarchy"""
		intermediateSignals = [self.attrsChanged, self.stateChanged, self.connectionsChanged,
		          self.nodeNameChanged]

		for i in intermediateSignals:
			# connect sync to everything
			self.sync.connect(i)
			# connect everything to nodeChanged
			i.connect(self.nodeChanged)
		"""need more sophistication in signal system to avoid mashing nodeChanged 5 times
		every time sync is called"""

	# signal-fired methods
	def onNodeChanged(self, *args, **kwargs):
		pass
	def onAttrsChanged(self, *args, **kwargs):
		pass
	def onStateChanged(self, *args, **kwargs):
		pass
	def onConnectionsChanged(self, *args, **kwargs):
		pass

	def initSettings(self):
		"""putting here as temp, this all needs restructuring"""
		# settings
		self.settings = AbstractTree(self.__class__.__name__+"_settings", None)
		#self.evaluator = self.evaluatorClass(graph=self.graph, node=self)

	def setState(self, state):
		if state not in self.states:
			raise RuntimeError("invalid abstractNode state {}".format(state))
		self.state = state
		self.stateChanged()

	@property
	def dataPath(self):
		return self.graph.dataPath + "/" + self.idTag

	@property
	def idTag(self):
		return self.nodeName + "_" + str(self.uid)

	@property
	def edges(self)->Set["AbstractEdge"]:
		return self.inEdges.union(self.outEdges)

	def instantiateReal(self, name=None):
		return self.realClass(name=name)

	def setRealInstance(self, real, inDict=None, outDict=None, define=True):
		"""sets real component"""
		self.real = real
		self.real.setAbstract(self, inDict=inDict, outDict=outDict, define=define)

	def rename(self, name):
		origPath = self.dataPath
		self.nodeName = name
		#name = self._processName(name)
		# if we ever want to add "-op" to the end of real items or something
		self.real.rename(name) # it's just that easy
		pipeline.renameFile(old=origPath, new=self.dataPath)


	def setApproved(self):
		self.log("this will approve the node")
		pass

	def log(self, message):
		"""if we implement proper logging replace everything here"""
		self.graph.log(message)

	# toplogy
	@property
	def history(self):
		return self.graph.getNodesInHistory(self)

	@property
	def future(self):
		return self.graph.getNodesInFuture(self)


	# execution
	def executionStages(self):
		"""returns a list supplied by real component of stages of execution"""
		if not self.real:
			return []
		return self.real.execStageNames()

	def executionFunctions(self):
		"""returns the execution dict of real component"""
		return self.real.execFuncs()

	def getExecFunction(self, index, variant="onExec"):
		"""retrieves specific function"""
		self.log("execIndex is {}".format(index))
		stageName = self.executionStages()[index]
		func = self.executionFunctions()[stageName]
		return func

	def execute(self, index):
		"""builds a single stage of the real component's execution order
		ATOMIC - CALLED BY EXEC TO STAGE"""
		# test
		func = self.getExecFunction(index)
		with self.real.executionManager(): # real-level
			return func(self.real)

	def execToStage(self, index):
		"""builds up until a target stage"""
		maxStage = len(self.executionStages())
		if index == -1:  # build everything
			return self.execToStage(maxStage - 1)
		elif index >= maxStage:
			index = maxStage

		with AbstractNodeExecutionManager(self): #abstract-level
			for i in range(index+1):
				nodeKSuccess = self.execute(i)
			self.evaluateSettings()

	def propagateOutputs(self):
		"""references the value of every output to that of every connected input"""
		for i in self.outEdges:
			i.dest[1].value = i.source[1].value
		if hasattr(self.real, "propagateOutputs"):
			self.real.propagateOutputs()

	"""IN THEORY this system can support multiple stages of execution,
	but it is not recommended, and variants are not supported at all"""

	def beforeExecute(self):
		"""use to update state?"""
		self.setState("executing") # neutral, executing, complete, failed, approved
		pass

	def afterExecute(self, success=True):
		"""used to update state, propagate outputs, etc"""
		if success:
			self.setState("complete")
		else:
			self.setState("failed")
		self.propagateOutputs()
		#self.sync(self) # sure whatever
		#self.sync([self])
		self.sync()
		pass

	"""we need a way to feed back to the graph and ui the state of the node
	do not attempt this specifically here, just trigger sync with the 
	abstract node as argument. errors are raised to graph level and then
	re-directed"""

	def reset(self):
		if self.state != "neutral":
			if self.real:
				self.real.reset()
		self.setState("neutral")

	# SETTINGS
	def evaluateSettings(self):
		"""this never worked anyway"""
		#self.evaluator.evaluateSettings(self.settings)
		return 1

	# ATTRIBUTES
	@property
	def inputs(self):
		#return {i.name : i for i in self.inputRoot.getAllChildren()}
		return self.inputRoot.getAllChildren()

	@property
	def outputs(self):
		#return {i.name : i for i in self.outputRoot.getAllChildren()}
		return self.outputRoot.getAllChildren()

	@staticmethod
	def addAttr(parent=None, name=None, dataType=None,
	            hType=None, desc="", default=None, attrItem=None,
	            *args, **kwargs):
		if attrItem:
			result = parent.addChild(attrItem)

		elif parent.attrFromName(name=name):
			result = parent.attrFromName(name)
		else:
			result = parent.addAttr(name=name, dataType=dataType, hType=hType,
			                        desc=desc, default=default, *args, **kwargs)
		return result

	def removeAttr(self, name, role="output", emit=True):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)
		#attr.parent.removeAttr(name)
		attr.parent.remove(name)
		if emit: # for bulk attribute reordering call signal by hand
			self.attrsChanged()

	def addInput(self, parent=None, name=None, dataType=None,
	             hType="leaf", desc="", default=None, attrItem=None,
	             *args, **kwargs):
		parent = parent or self.inputRoot
		result =  self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)
		self.attrsChanged()
		return result

	def addOutput(self, parent=None, name=None, dataType=None,
	              hType="leaf", desc="", default=None, attrItem=None,
	              *args, **kwargs):
		parent = parent or self.outputRoot
		result = self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)
		self.attrsChanged()
		return result

	def getInput(self, name):
		return self.inputRoot.attrFromName(name)

	def searchInputs(self, match):
		return [i for i in self.inputs if match in i.name]

	def searchOutputs(self, match):
		return [i for i in self.outputs if match in i.name]

	def getOutput(self, name):
		return self.outputRoot.attrFromName(name)

	def connectableInputs(self):
		return self.inputRoot.getAllConnectable()

	def interactibleInputs(self):
		return self.inputRoot.getAllInteractible()

	def connectableOutputs(self):
		return self.outputRoot.getAllConnectable()

	def getConnectedInputs(self):
		inputs = self.inputRoot.getAllChildren()
		return [i for i in inputs if i.getConnections()]

	def getConnectedOutputs(self):
		outputs = self.outputRoot.getAllChildren()
		return [i for i in outputs if i.getConnections()]

	def clearOutputs(self, search=""):
		for i in self.outputs:
			if search in i.name or not search:
				self.removeAttr(i)

	def clearInputs(self, search=""):
		for i in self.inputs:
			if search in i.name or not search:
				self.removeAttr(i, role="input")

	# settings
	def addSetting(self, parent=None, entryName=None, value=None,
	               options=None, min=None, max=None):
		"""add setting entry to abstractTree"""
		parent = parent or self.settings
		branch = parent(entryName)
		if options == bool: options = (True, False)
		extras = {"options" : options,
		          "min" : min,
		          "max" : max}
		branch.extras = {k : v for k, v in extras.items() if v}
		branch.value = value

	# sets
	def addToSet(self, setName):
		self.graph.addNodeToSet(self, setName)

	def removeFromSet(self, setName):
		self.graph.removeNodeFromSet(self, setName)

	def getConnectedSets(self):
		return self.graph.getSetsFromNode(self)

	def getAllActions(self):
		#self.addAction(self.getRealActions())
		actions = {}
		actions.update(self.actions)
		actions.update(self.getRealActions())
		return actions
		#return self.actions

	def getRealActions(self):
		return self.real.getAllActions() # dict

	def addAction(self, actionDict=None, actionItem=None):
		if actionDict:
			self.actions.update(actionDict)
		elif actionItem:
			self.actions.update({actionItem.name : actionItem})

	def getExecActions(self):
		"""this is kind of a mess - allows executing specific nodes to specific
		stages - although we currently only use one"""
		actions = {}
		for i, val in enumerate(self.executionStages()):
			actionDict = {"func" : self.execToStage, "args" : [i]}
			actions.update({val : ActionItem(name=val, execDict=actionDict)})
		return actions

	def recastReal(self):
		"""for use in developing real components live - replaces class of real component
		with current version"""
		newReal = self.real.fromDict(self.real.serialise())
		self.setRealInstance(newReal, define=False)
		self.sync()


	def serialise(self):
		"""converts node and everything it contains to dict"""
		serial = {
			"uid" : self.uid,
			"nodeName" : self.nodeName,
			"inputRoot" : self.inputRoot.serialise(),
			"outputRoot" : self.outputRoot.serialise(),
			"extras" : self.extras,
			"settings" : self.settings.serialise(),
			#"CLASS" : self.__class__.__name__
		}
		if self.real:
			serial["real"] = self.real.serialise()
			#serial["memory"] = self.real.memory.serialise()
		return serial

	@classmethod
	def fromDict(cls, fromDict, graph=None):
		"""classmethod because returned abstract should be the right child class
		so this is carnage"""
		realClass = None
		# try to load real component class from module

		if "real" in list(fromDict.keys()):
			realDict = fromDict["real"]
			realClass = loadObjectClass(realDict["objInfo"])

		if realClass:
			newClass = cls.generateAbstractClass(realClass)
		else:
			newClass = cls

		# abstract reconstruction
		newInst = newClass(graph)
		newInst.uid = fromDict["uid"]
		newInst.rename(fromDict["nodeName"])

		# newInst.outputRoot = AbstractAttr.fromDict(regenDict=fromDict["outputRoot"],
		#                                            node=newInst)
		newInst.outputRoot = AbstractAttr.fromDict(regenDict=fromDict["outputRoot"])
		newInst.outputRoot._node = newInst
		# newInst.inputRoot = AbstractAttr.fromDict(regenDict=fromDict["inputRoot"],
		#                                           node=newInst)
		newInst.inputRoot = AbstractAttr.fromDict(regenDict=fromDict["inputRoot"])
		newInst.inputRoot._node = newInst
		newInst.settings = AbstractTree.fromDict(fromDict["settings"])

		if "real" in list(fromDict.keys()):
			realDict = fromDict["real"]
			realInstance = realClass.fromDict(realDict, abstract=newInst)
			newInst.setRealInstance(realInstance, define=False)
			newInst.real.makeBaseActions()

		return newInst

	@staticmethod
	def generateAbstractClass(realClass):
		"""generates a new abstractNode class bound to target real class"""
		realClassName = realClass.__name__
		abstractClass = type(realClassName, (AbstractNode,),
		                     {"realClass": realClass})
		return abstractClass

	def delete(self):
		"""deletes abstract node and real component
		edges will already have been deleted by graph"""
		self.inputRoot.delete()
		self.outputRoot.delete()
		self.real.delete()










