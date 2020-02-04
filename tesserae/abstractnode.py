
from collections import OrderedDict

# container interfacing with the graph - concerned with connections
import edRig.pipeline
from edRig.structures import AttrItem, ActionItem, ActionList
from edRig.core import shortUUID
from edRig import pipeline, attrio
# from edRig.tesserae.ops.op import Op
import functools
from edRig.tesserae.lib import GeneralExecutionManager
from edRig.lib.python import Signal, AbstractTree

# test
from edRig.tesserae.expression import EVALUATOR

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
			print ""
			print "node {} encountered error during execution".format(self.node.nodeName)
			print "error is {}".format(exc_val)
			#self.node.setState("failed")


			# we want execution to stop in this case
			#raise exc_type(exc_val)
			#self.printTraceback(exc_type, exc_val, exc_tb)
		else:
			self.node.afterExecute(success=True)
			#self.node.setState("complete")

class AbstractNode(object):
	"""abstract node managed by abstract graph
	interfaces with direct operations, and with UI"""

	defaultName = "basicAbstract"
	realClass = None
	states = ["neutral", "executing", "complete", "failed", "approved", "guides"]

	evaluatorClass = EVALUATOR

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

		self.extras = None
		self.inEdges = set()
		self.outEdges = set()

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

		pass

	@property
	def graph(self):
		""" i can't make tensorflow go away
		:returns AbstractGraph"""
		return self._graph
	@graph.setter
	def graph(self, val):
		self._graph = val


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
		self.evaluator = self.evaluatorClass(graph=self.graph, node=self)

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
	def edges(self):
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
		print "RENAMED NODE TO {}".format(name)
		self.real.rename(name) # it's just that easy
		pipeline.renameFile(old=origPath, new=self.dataPath)


	def setApproved(self):
		self.log("this will approve the node")
		pass

	def log(self, message):
		"""if we implement proper logging replace everything here"""
		print message

	# toplogy
	@property
	def history(self):
		return self.graph.getNodesInHistory(self)

	@property
	def future(self):
		return self.graph.getNodesInFuture(self)

	@property
	def fedBy(self):
		return self.graph.getNode(self, entry=True)["fedBy"]

	@property
	def feeding(self):
		return self.graph.getNode(self, entry=True)["feeding"]

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
		"""ye sure ok whatever
		real parses settings to find what needs evaluating"""
		self.evaluator.evaluateSettings(self.settings)
		# should this be called from real?

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
		attr.parent.removeAttr(name)
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
		#self.log("op connectableInputs are {}".format(self.inputRoot.getAllConnectable()))
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
		branch.extras = {k : v for k, v in extras.iteritems() if v}
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
		self.setRealInstance(newReal)
		self.sync()

	# graph io
	def checkDataFileExists(self):
		if edRig.pipeline.checkFileExists(self.dataPath):
			print "data file for {} exists".format(self.nodeName)
			self.dataFileExists = True
		else:
			print "data file for {} does not exist, making new one".format(self.nodeName)
			edRig.pipeline.makeBlankFile(path=self.dataPath)
			self.dataFileExists = True

	def searchData(self, infoName, internal=True):
		if internal:
			memoryCell = self.graph.getNodeMemoryCell(self)
			return memoryCell["data"].get(infoName)

		print "abstract getting data" + infoName
		self.checkDataFileExists()
		return attrio.getData(infoName, self.dataPath)
		pass

	def saveOutData(self, infoName="info", data=None, internal=True):
		""" NEW INTERNAL MODE
		in the interest of not drowning in files, a mechanism for storing all
		data in one single .tes file
		"""
		if internal:
			memoryCell = self.graph.getNodeMemoryCell(self)
			memoryCell["data"][infoName] = data
			return

		# golly gee willakers
		print "abstract saving data " + infoName
		self.checkDataFileExists()
		attrio.updateData(infoName, data, path=self.dataPath)


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
		return serial

	@classmethod
	def fromDict(cls, fromDict, graph=None):
		"""classmethod because returned abstract should be the right child class
		so this is carnage"""
		realClass = None
		# try to load real component class from module

		if "real" in fromDict.keys():
			realDict = fromDict["real"]
			module = realDict["MODULE"]
			loadedModule = pipeline.safeLoadModule(module)
			try:
				realClass = getattr(loadedModule, realDict["CLASS"])
			except Exception as e:
				print "ERROR in reconstructing op {}".format(realDict["NAME"])
				raise e

		if realClass:
			newClass = cls.generateAbstractClass(realClass)
		else:
			newClass = cls

		# abstract reconstruction
		newInst = newClass(graph)
		newInst.uid = fromDict["uid"]
		newInst.rename(fromDict["nodeName"])

		newInst.outputRoot = AbstractAttr.fromDict(fromDict=fromDict["outputRoot"],
		                                           node=newInst)
		newInst.inputRoot = AbstractAttr.fromDict(fromDict=fromDict["inputRoot"],
		                                          node=newInst)
		newInst.settings = AbstractTree.fromDict(fromDict["settings"])
		# print ""
		# print "ABSTRACT FROMDICT KEYS ARE {}".format(fromDict.keys())

		if "real" in fromDict.keys():
			realDict = fromDict["real"]
			realInstance = realClass.fromDict(realDict, abstract=newInst)
			#print "realInstance is {}".format(realInstance)
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


class AbstractAttr(AttrItem):
	"""simple object marking separate inputs and outputs to AbstractNodes
	also incorporating hierarchy"""

	accepts = { # key accepts connections of type value
		"nD" : ["0D", "1D", "2D", "3D"],
		# this should probably be exposed to user per-attribute
	}

	def __init__(self, *args, **kwargs):
		"""add maya-specific support, this inheritance is totally messed up"""
		super(AbstractAttr, self).__init__(*args, **kwargs)
		self.plug = None

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

	def setChildKwargs(self, name=None, desc="", dataType="0D", default=None,
	                   extras=None):
		newKwargs = {}
		# this is disgusting i know
		newKwargs["name"] = name or self.childKwargs["name"]
		# newKwargs["hType"] == hType or self.childKwargs["hType"]
		newKwargs["desc"] = desc or self.childKwargs["desc"]
		newKwargs["dataType"] = desc or self.childKwargs["dataType"]
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









