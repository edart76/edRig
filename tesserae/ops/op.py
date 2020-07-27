# base op
# from maya import cmds
# import maya.api.OpenMaya as om
from edRig import cmds, om
from edRig.core import ECN, shortUUID
from edRig.node import AbsoluteNode, ECA, invokeNode
from edRig import scene, attr, transform, pipeline
from edRig.tesserae.abstractnode import AbstractAttr

from edRig.structures import ActionItem
from edRig.pipeline import safeLoadModule
from edRig.tesserae.real import MayaReal, RealAttrInterface
from edRig.tesserae.lib import GeneralExecutionManager
from edRig.lib.python import debug, outerVars, AbstractTree, \
	saveObjectClass, loadObjectClass
from edRig.layers.setups import InvokedNode

class OpExecutionManager(GeneralExecutionManager):
	"""manage execution of ops"""
	excludeList = [
		"tilePile",
	]
	def __init__(self, op):
		super(OpExecutionManager, self).__init__(op)
		self.op = op
		self.beforeSet = None
		self.afterSet = None

	def __enter__(self):
		self.beforeSet = set(scene.listAllNodes())
		self.op.beforeExecution()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""clean up maya scene nodes regardless"""
		self.op.afterExecution()
		self.afterSet = set(scene.listAllNodes())
		new = self.afterSet - self.beforeSet
		newDags = [n for n in [AbsoluteNode(i) for i in new] if n.isDag()
		           and not n.parent]
		newDags = [i for i in newDags if i not in self.excludeList]

		self.op.opGrp
		for i in new:
			#print "i is {}".format(i)
			#print "i isDag {}".format(i.isDag())
			# force unlock nodes
			cmds.lockNode(i, lock=False)
			attr.edTag(i)
			self.op.opTag(i)
		for i in newDags:
			current = scene.listRelatives(self.op.opGrp, ad=True)
			#print "current {}".format(current)
			if not i in current:
				try:
					cmds.parent(i, self.op.opGrp)
				except:
					pass
		#self.op.nodes.update(newDags)

		# halt execution
		if exc_type:
			# print exc_tb
			#raise exc_type(exc_val)
			self.printTraceback(exc_type, exc_val, exc_tb)
			pass

class MayaAttrInterface(RealAttrInterface):
	"""allows access between tesserae attrItems
	and maya io network nodes and plugs"""

	def getRealAttrComponent(self):
		"""look up the network node and plug"""
		plugName = self.attrItem.name
		if self.attrItem.role == "input":
			node = self.mainReal.inputNetwork
		elif self.attrItem.role == "output":
			node = self.mainReal.outputNetwork
		return node + "." + plugName

	# def __add__(self, other):
	# 	return self.__str__().__add__(other)

class Op(MayaReal):

	forceInclude = False

	colour = (100, 100, 150) # rgb

	categories = ["opIo", "main"]
	persistCategories = ["opIo"]

	def tidy(*args, **kwargs):
		"""decorator to tidy dag nodes under this op's group"""
		# print "outer args are {}, {}".format(args, kwargs)
		# direct arguments to decorator
		category = kwargs.get("category", "main")
		def midWrapper(*args, **kwargs):
			# print "mid args are {}, {}".format(args, kwargs)
			func = args[0]
			#@functools.wraps(func)
			def wrapper(*args, **kwargs):
				# print "inner args are {}, {}".format(args, kwargs)
				# default function arguments, including self
				self = args[0]
				before = set(scene.listAllNodes())
				beforeDags = set(scene.listTopDags())

				results = func(*args, **kwargs)

				after = set(scene.listAllNodes()) - before
				afterDags = set(scene.listTopDags()) - beforeDags
				for i in after:
					try:
						self.opTag(i)
						attr.addTag(i, "category", category)
					finally:
						pass

				for i in afterDags:
					try:
						cmds.parent(i, self.opGrp)
					except:
						pass

				# self.nodes.update(after)
				return results
			return wrapper
		return midWrapper

	# execution architecture
	@classmethod
	def execStageNames(cls):
		"""returns names of stages IN ORDER"""
		#execStages = ["plan", "build"]
		execStages = ["execute"]
		return execStages

	@classmethod
	def execFuncs(cls):
		"""all execution stages associated with class"""
		return {"execute" : cls.execute}

	@classmethod
	def classRigGrp(cls):
		"""base group for all tilePile stuff, named by character eventually"""
		return invokeNode(name="tilePile", type="transform")

	def __init__(self, name=None, abstract=None):
		""":type abstract AbstractNode"""
		self.character = None
		print "Op instantiated"
		self._opName = None
		self.opName = name or self.__class__.__name__
		self.abstract = abstract
		self.actions = {}

		self.uuid = self.shortUUID(8)
		if self.abstract:
			self.inputRoot = abstract.inputRoot
			self.outputRoot = abstract.outputRoot
		else:
			print "no abstract passed"
			self.inputRoot = AbstractAttr(role="input", hType="root", name="inputRoot")
			self.outputRoot = AbstractAttr(role="output", hType="root", name="outputRoot")
		self.defineAttrs() # override this specific method with attr construction

		# abstract interface
		# signals and methods directly from abstract
		self.sync = None
		self.attrsChanged = None
		self.attrValueChanged = None
		self.settings = AbstractTree("proxy")
		self.evaluator = None
		self.addSetting = None

		# sets
		self.addToSet = None
		self.removeFromSet = None
		self.getConnectedSets = None

		if self.abstract:
			self.setAbstract(abstract)

		self.makeBaseActions()


		# testing stacks of functions to be called automatically
		# on show / hide guides
		self.showGuidesStack = []
		self.hideGuidesStack = []

	@property
	def internal(self):
		return self.abstract.internal

	@property
	def data(self):
		""" looks up abstract's data """
		return self.abstract.data

	def executionManager(self):
		return OpExecutionManager(self)

	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		"""attach op to abstractNode, and merge input and outputRoots"""
		self.abstract = abstract

		# settings
		self.settings = self.abstract.settings
		self.evaluator = self.abstract.evaluator
		self.addSetting = self.abstract.addSetting

		# sets
		self.addToSet = self.abstract.addToSet
		self.removeFromSet = self.abstract.removeFromSet
		self.getConnectedSets = self.abstract.getConnectedSets

		self.inputRoot = abstract.inputRoot
		self.outputRoot = abstract.outputRoot
		if define:
			self.defineAttrs() # resets attributes, don't call on regeneration
			self.defineSettings()

		# support for redefining attributes from dict
		if inDict:
			self.inputRoot = self.inputRoot.fromDict(inDict, node=abstract)
		if outDict:
			self.outputRoot = self.outputRoot.fromDict(outDict, node=abstract)
		# no luck all skill

		print ""
		self.sync = self.abstract.sync
		self.attrsChanged = self.abstract.attrsChanged
		self.attrValueChanged = self.abstract.attrValueChanged
		self.makeBaseActions()

		self.sync.connect( self.onSync )

		self.sync()

		# i would really like some meta way to supplant all op-level methods
		# with the "correct" abstract-level versions

	def onSync(self):
		""" user-facing method to update plugs, settings, anything """
		pass

	def makeBaseActions(self):
		self.addAction(actionItem=ActionItem(name="clear Maya scene", execDict=
			{"func" : self.clearMayaRig}))
		self.addAction(func=self.showGuidesWrapper, name="showGuides")
		self.addAction(func=self.sync, name="sync")

	@property
	def __name__(self):
		# return str(self.__class__) + "-" + self.opName + "-" + self.uuid
		return str(self.__class__.__name__) + "-" + self.opName

	def rename(self, newName):
		"""called by graph"""
		self.opName = newName

	@property
	def opName(self):
		# because this wasn't confusing enough already
		if self._opName:
			return self._opName
		else:
			return self.__class__.__name__ #+ self.uuid

	@opName.setter
	def opName(self, val):
		# equivalent to renaming an op
		self._opName = val
		# return val

	@staticmethod
	def log(message, **kwargs):
		"""if we implement proper logging replace everything here"""
		#print(message, **kwargs)
		print(message)


	def defineAttrs(self):
		"""override with op specifics"""
		raise NotImplementedError("op class {} DOES NOT override defineAttrs, please fix".format(
			self.__class__.__name__))


	### handy settings methods
	def defineSettings(self):
		"""override with op specifics"""
		pass

	def addSetting(self, parent=None, entryName=None, value=None,
	               options=None, min=None, max=None):
		"""dummy to get args in pycharm :("""
		pass

	def addMemorySpaceSetting(self, parent=None):
		"""specific to give uniform option to method
		of recalling xform from memory"""
		self.addSetting(parent=parent, entryName="memorySpace", value="local",
		                options=("relative", "absolute"))

	def addBoolSetting(self, entryName=None, parent=None, value=True):
		self.addSetting(parent=parent, entryName=entryName, value=value,
		                options=(True, False))

	def exposeNode(self, node, parent=None, entryName="node"):
		"""CRUCIAL aspect of rigging system - allows exposing individual
		nodes AND ATTRIBUTES in the graph, to be driven by expressions or
		later lower-class graph connections"""
		node = AbsoluteNode(node)
		self.addSetting(parent, entryName, value=node)

	# ever look at a node and think
	# wtf are you
	@staticmethod
	def edTag(tagNode):
		# more tactile to have a little top tag
		return attr.edTag(tagNode)


	@staticmethod
	def addTag(tagNode, tagName, tagContent=None):
		return attr.addTag(tagNode, tagName, tagContent)

	@staticmethod
	def getTag(tagNode, tagName=None):
		# retrieves specific tag information, or lists all of it
		if tagName:
			if not tagName in cmds.listAttr(tagNode):
				return None
			gotTag = cmds.getAttr(tagNode + "." + tagName)

		else:
			gotTag = cmds.listAttr(tagNode, string="*tag")
		return gotTag

	def getTaggedNodes(self, searchNodes=None,
	                   searchTag=None, searchContent=None, searchDict=None):
		"""calls main scene tag methods"""
		return scene.listTaggedNodes(searchNodes,
		                             searchTag,
		                             searchContent,
		                             searchDict)

	def opTag(self, tagNode):
		# add tag for the specific op
		attr.addAttr(tagNode, attrName="opTag", attrType="string")
		try:
			attr.setAttr(tagNode + ".opTag", self.opName)
		except:
			pass
		attr.addTag(tagNode, "opUID", self.uuid)
		# connect all created nodes to the input network node
		# said the consummate idiot

	def ECN(self, type, name="blankName", cleanup=False, *args):
		# this is such a good idea
		if name == "blankName":
			name = type
		node = ECN(type, name, *args)
		self.edTag(node)
		self.opTag(node)

		if cleanup:
			node = cmds.parent(node, self.opGrp)[0] # prevent messy scenes
		return node

	def ECAsimple(self, type, name="blankName", cleanup=False, *args, **kwargs):
		# this is such a good idea
		# first check if node already exists, later
		node = self.ECN(type, *args, name=name, cleanup=cleanup, **kwargs)
		return AbsoluteNode(node)

	def ECA(self, type, name="blankName", category=None, *args, **kwargs):
		node = self.ECAsimple(type, name, cleanup=False, *args, **kwargs)
		self.nodes.update(node)
		if category: # add specific tags
			self.addTag(node, "category", category)
		#cmds.parent(node, self.opGrp)
		return node

	# live node attributes from tags
	@property
	def nodes(self):
		"""unsuitable for ordered or specific indexing. if we need that,
		make a new function"""
		return set(self.getTaggedNodes(searchTag="opUID",
		                           searchContent=self.uuid))
	@property
	def inputNetwork(self):
		searchDict = {"opUID" : self.uuid,
		              "category" : "opIo",
		              "role" : "input"}
		node = self.getTaggedNodes(self.nodes, searchDict=searchDict)
		return None if not node else node[0]

	@property
	def outputNetwork(self):
		searchDict = {"opUID" : self.uuid,
		              "category" : "opIo",
		              "role" : "output"}
		node = self.getTaggedNodes(self.nodes, searchDict=searchDict)
		return None if not node else AbsoluteNode(node[0])


	@staticmethod
	def shortUUID(length=4):
		return shortUUID(length=length)

	# execution
	def execute(self):
		raise NotImplementedError()

	def reset(self, exclude=persistCategories):
		"""as this rigging system should be purely additive,
		just delete all associated nodes"""
		for i in self.nodes:
			if cmds.objExists(i):
				#if not attr.getAttr(i+".category") in exclude: # nope
				cmds.delete(i)

	def beforeExecution(self):
		"""create network nodes procedurally from attributes
		called by context immediately before exec"""
		#self.inputNetwork, self.outputNetwork = self.makeOpIoNodes()
		self.makeOpIoNodes()

		for i in self.inputRoot.getAllLeaves():
			self.makeOpIoNodeAttrs(self.inputNetwork, i)

		for i in self.outputRoot.getAllLeaves():
			self.makeOpIoNodeAttrs(self.outputNetwork, i)

		# now connect inputs to previous outputs
		# for i in self.inputRoot.getAllLeaves():
		# 	self.connectInputPlug(i)
		self.connectIoPlugs() # spam this all the time

	def afterExecution(self):
		"""immediately after exec"""
		self.connectIoPlugs()
		pass

	def propagateOutputs(self):
		"""connect attrItem plugs in maya"""
		for i in self.outputs:
			for n in i.getConnections(): # will return abstractEdges
				# this is a car fire but it works for now
				cmds.connectAttr(i.plug, n.destAttr.plug)

	def makeOpIoNodes(self):
		"""create connected bookend network nodes"""
		inputNetwork = self.ECA("network", name=self.opName+"_inputs")
		outputNetwork = self.ECA("network", name=self.opName + "_outputs")

		# add tags
		for i in inputNetwork, outputNetwork:
			attr.addTag(i, "category", "opIo")
		attr.addTag(inputNetwork, "role", "input")
		attr.addTag(outputNetwork, "role", "output")

		attr.makeStringConnection(self.inputNetwork, self.outputNetwork,
								  startName="opStart", endName="opEnd")

		return inputNetwork, outputNetwork


	def makeOpIoNodeAttrs(self, node, attrItem, parentItem=None):
		""" populates opIo network nodes procedurally from op attr hierarchy
		:param node: AbsoluteNode
		:param attrItem : AbstractAttr
		:param parentItem : attrItem"""
		#for i in attrItem.getAllChildren(): # get all leaves maybe?
		i = attrItem
		plug = None
		parentPlug = parentItem.plug if parentItem else ""
		# convert datatype to pass to addattr
		#print "i.dataType is {}".format(i.dataType)

		if i.getChildren(): # need a compound
			plug = attr.addAttr(node, attrName=i.name, attrType="compound",
			                    parent=parentPlug)
			for n in i.getChildren():
				self.makeOpIoNodeAttrs(node, n, parentItem=i)

		if i.dataType == "enum":
			options = ":".join(i.extras.get("items"))
			plug = attr.addAttr(node, attrName=attrItem.name, attrType="enum",
			             parent=parentPlug,
						 enumName=options)
		elif i.dataType == "nD":
			""" acgnostic datatype """

			if i.getConnections():
				dt = i.getConnections()[0].dataType
				newItem = AbstractAttr(name=i.name, dataType=dt, hType="leaf")
				self.makeOpIoNodeAttrs(node, newItem, parentItem)
			else:
				# dt = "matrix"
				# plug = attr.addAttr(node, attrName=i.name, attrType=dt)
				plug = attr.addUntypedAttr(node, attrName=i.name)
		elif i.dataType in attr.INTERFACE_ATTRS:
			dtdict = attr.INTERFACE_ATTRS[i.dataType]
			dtdict = {i.name : dtdict }
			#print("new attr dict is {}".format(dtdict))
			attr.makeAttrsFromDict(node,
	                              attrDict=dtdict,
	                              parent=parentPlug)
			plug = node+ "." + "".join(parentPlug.split(".")[0:]) + i.name
		else:
			dt = i.dataType
			self.log(" attr is {}".format(i.name))
			self.log(" attr dt is {}".format(i.dataType))
			#kwargs = i.extras or {}
			kwargs = {}
			plug = attr.addAttr(node, attrName=attrItem.name, attrType=dt,
			                    parent=parentPlug, **kwargs)

		# add the real-facing component for the attrItem with the plug
		i.plug = MayaAttrInterface(i, self)
		#print "made plug {}".format(i.plug)
		# i.plug = plug

		# set plug value if it's simple
		if i.isSimple():
			attr.setAttr(i.plug(), i.value)

	@staticmethod
	def connectInputPlug(attrItem):
		"""connect previous network output to new network input
		:param attrItem : AbstractAttr"""
		#print "input connections {}".format(attrItem.getConnectedAttrs())
		if attrItem.getConnections():
			prev = attrItem.getConnectedAttrs()[0]
			#if hasattr(prev, name="plug"):
			test = getattr(prev, "plug")
			#print "test {}".format(test)
			if test:
				cmds.connectAttr(prev.plug(), attrItem.plug(), f=True)

	@staticmethod
	def connectOutputPlug(attrItem):
		"""connect previous network output to new network input
		:param attrItem : AbstractAttr"""
		#print "output connections {}".format(attrItem.getConnections())
		for i in attrItem.getConnectedAttrs():
			test = getattr(i, "plug")
			# "test {}".format(test)
			if test:
				cmds.connectAttr(attrItem.plug(), i.plug(), f=True)

	def connectIoPlugs(self):
		"""tries to connect attrItems on both sides of node"""
		for i in self.inputRoot.getAllLeaves():
			self.connectInputPlug(i)

		for i in self.outputRoot.getAllLeaves():
			self.connectOutputPlug(i)


	@staticmethod
	def dataTypeForNodeType( nodeType ):
		""" returns "0D" for transform, "2D" for meshes and surfaces
		etc"""
		if nodeType == "transform" : return "0D"
		elif nodeType == "nurbsCurve" or nodeType == "bezierCurve" :
			return "1D"
		elif nodeType == "mesh" or nodeType == "nurbsSurface" :
			return "2D"
		raise RuntimeError("no dataType for nodeType {}".format(nodeType))


	# actions
	def getAllActions(self):
		return self.actions

	def addAction(self, actionDict=None, actionItem=None, func=None, name=None):
		if actionDict:
			self.actions.update(actionDict)
		elif actionItem:
			#print "adding action {}".format(actionItem)
			self.actions.update({actionItem.name : actionItem})
		elif func:  # just add the function
			name = name or func.__name__
			item = ActionItem(execDict={"func": func}, name=name)
			self.actions.update({item.name : item})

	def addInputWithAction(self, parent=None, name=None, datatype=None, copy=None,
	                       suffix="", desc=""):
		"""allows user to add input whenever - name or datatype undefined here will
		be requested from user as direct input"""
		parent = parent or self.inputRoot
		def _addInputWithAction(op=self, parent=parent, name=name, datatype=datatype,
		                        copy=copy, suffix=suffix, desc=desc):
			if not name:
				name = raw_input(prompt="name of attribute") + suffix
			if not datatype:
				datatype = raw_input(prompt="datatype of attribute (in units of D)")

			op.addInput(parent=parent, name=name, dataType=datatype, desc=desc)

		actionDict = {
			"func" : _addInputWithAction,
			"kwargs" : {"op": self}}
		inputAction = ActionItem(name="add_custom_input", execDict=actionDict)
		self.addAction(actionItem=inputAction)


	# serialisation and regeneration
	def serialise(self):
		objInfo = saveObjectClass(self) # name, class and module
		opDict = {
			"objInfo" : objInfo,
			"opName" : self.opName,
		}

		return opDict

	@staticmethod
	def fromDict(regenDict, abstract=None):
		"""regenerates op from dict"""
		opCls = loadObjectClass(regenDict["objInfo"])
		opInstance = opCls(name=regenDict["opName"])

		if abstract:
			opInstance.inputRoot = abstract.inputRoot
			opInstance.outputRoot = abstract.outputRoot

		opInstance.makeBaseActions()
		return opInstance

	@staticmethod
	def safeLoadModule(mod):
		"""takes string name of module"""
		return safeLoadModule(mod)

	def delete(self):
		"""deletes op instance"""
		self.reset(exclude=[])
		del self

	def showGuides(self):
		"""used to allow user direction over op, as a separate process
		to execution"""
		for i in self.showGuidesStack:
			i()
		return True
		pass

	@tidy(category="test")
	def showGuidesWrapper(self):
		self.showGuides()

	def hideGuides(self):
		for i in self.hideGuidesStack:
			i()


	def setState(self, state):
		"""allows real to set abstract state"""
		self.abstract.setState(state)


	#### maya stuff ####
	# yes i know this should go in a DCC-specific child class, but there's
	# absolutely no point right now
	def invokeNode(self, name="", type="", parent="", func=None):
		parent = parent or self.opGrp
		func = func or self.ECA
		return invokeNode(name=name, type=type, parent=parent,
		                       func=func)

	def clearMayaRig(self):
		"""clears all edRig items from maya scene - this method needs a home"""
		#cmds.file(new=True, f=True)
		for i in scene.listTaggedNodes(searchNodes=scene.ls(),
		                               searchTag="edTag"):
			try:
				cmds.delete(i)
			except:
				pass

	def nodesFromScene(self):
		"""list all nodes created by the op, called on instantiation
		returns set"""
		all = scene.ls()
		new = {i for i in all if self.opName == self.getTag(i, "opTag")}
		return new



	@property
	def rigGrp(self):
		return self.classRigGrp()

	@property
	def opGrp(self):
		return self.invokeNode(name=self.opName+"_opGrp", type="transform",
		                       parent=self.rigGrp, func=self.ECAsimple)
	@property
	def setupGrp(self):
		return self.invokeNode(name=self.opName+"_setup", type="transform",
		                       parent=self.opGrp, func=self.ECAsimple)
	@property
	def controlGrp(self):
		return self.invokeNode(name=self.opName+"_controls", type="transform",
		                       parent=self.opGrp, func=self.ECAsimple)
	@property
	def spaceGrp(self): # moved from datatypes for sanity reasons
		return self.invokeNode(name=self.opName+"_space", type="transform",
		                       parent=self.opGrp, func=self.ECAsimple)

	@staticmethod
	def plugFromAttr(attr):
		"""gets plug from either attrItem or attrInterface"""
		if isinstance(attr, basestring):
			result = attr
		elif getattr(attr, "plug"):
			result = attr.plug()
		else:
			result = attr()
		return result

	#### common maya helper methods
	def constrain0DToInput(self, master, slave, offset=True):
		"""common method to specify constraining a transform
		to another transform, curve or surface"""
		master = self.plugFromAttr(master)
		if attr.plugType(master) in attr.dimTypes["0D"]:
			transform.matrixConstraint(master, slave, offset=offset)





