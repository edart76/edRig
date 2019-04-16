# base op
from maya import cmds
import maya.api.OpenMaya as om
from edRig.core import ECA, ECN, AbsoluteNode, shortUUID, invokeNode
from edRig import Env, attrio, scene, attr
from edRig.tilepile.abstractnode import AbstractAttr
import random, functools, pprint, copy
from edRig.structures import ActionItem
from edRig.pipeline import safeLoadModule
from edRig.tilepile.real import MayaReal, MayaStack, MayaDelta
from edRig.tilepile.lib import GeneralExecutionManager
from edRig.lib.python import debug, outerVars

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
		self.beforeSet = scene.listTopNodes()
		self.op.beforeExecution()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""clean up maya scene nodes regardless"""
		self.op.afterExecution()
		self.afterSet = scene.listTopNodes()
		new = self.afterSet - self.beforeSet
		newDags = [n for n in [AbsoluteNode(i) for i in new] if n.isDag()]
		newDags = [i for i in newDags if i not in self.excludeList]
		cmds.parent(newDags, self.op.setupGrp)

		# halt execution
		if exc_type:
			# print exc_tb
			#raise exc_type(exc_val)
			self.printTraceback(exc_type, exc_val, exc_tb)
			pass


def tidy(name=None, *args, **kwargs):
	def decorator(inst, func, *args, **kwargs):
		#inst = func.im_self
		print "dir inst is {}".format(pprint.pformat(dir(inst)))
		print "dir func is {}".format(pprint.pformat(dir(func)))
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			before = scene.listTopNodes()
			results = func(*args, **kwargs)
			after = scene.listTopNodes() - before
			#inst.nodes.update(after)
			print "tidied nodes"
			return results
		return wrapper
	return decorator

# # FINALLY ACTIONS
def action(name=None, *args, **kwargs):
	print "action args {}".format(args)
	print "action kwargs {}".format(kwargs)
	def decorator(func, *args, **kwargs):
		#@functools.wraps(func)
		print "decorator args {}".format(args)
		print "decorator kwargs {}".format(kwargs)
		newName = name or func.__name__
		#print "dir inst is {}".format(pprint.pformat(dir(inst)))
		print "dir func is {}".format(pprint.pformat(dir(func)))
		def wrapper(*args, **kwargs):
			print "wrapper args {}".format(args)
			print "wrapper kwargs {}".format(kwargs)
			return func(*args, **kwargs)
		# inst.addAction(actionItem=ActionItem(name=newName,
		#                           execDict={"func": func}))
		return wrapper
	return decorator

class Op(MayaReal):
	# base class for "operations" executed by abstractGraph,
	# mainly maya scripting

	# def action(cls=None, name=None, *args, **kwargs):
	# 	print "name is {}".format(name)
	# 	print "cls is {}".format(cls)
	# 	print "action args {}".format(args)
	# 	print "action kwargs {}".format(kwargs)
	#
	# 	def decorator(func, *args, **kwargs):
	# 		# @functools.wraps(func)
	# 		print "decorator args {}".format(args)
	# 		print "decorator kwargs {}".format(kwargs)
	# 		newName = name or func.__name__
	# 		# print "dir inst is {}".format(pprint.pformat(dir(inst)))
	# 		print "dir func is {}".format(pprint.pformat(dir(func)))
	#
	# 		def wrapper(*args, **kwargs):
	# 			print "wrapper args {}".format(args)
	# 			print "wrapper kwargs {}".format(kwargs)
	# 			return func(*args, **kwargs)
	#
	# 		# inst.addAction(actionItem=ActionItem(name=newName,
	# 		#                           execDict={"func": func}))
	# 		return wrapper
	#
	# 	return decorator
	action = action

	#actions = {} # :(

	colour = (100, 100, 150) # rgb

	currentOp = None # set by exec handler?

	# def tidy(self, name=None):
	# 	def decorator(func):
	# 		@functools.wraps(func)
	# 		def wrapper(*args, **kwargs):
	# 			before = scene.listTopNodes()
	# 			results = func(*args, **kwargs)
	# 			after = scene.listTopNodes() - before
	# 			self.nodes.update(after)
	# 			print "tidied nodes"
	# 			return results
	# 		return wrapper
	# 	return decorator
	tidy = tidy

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
		# return {
		# 	"plan" : {"onExec" : cls.plan,
		# 	          "onStop" : cls.onPlanStop},
		# 	"build" : {"onExec" : cls.build,
		# 	           "onStop" : cls.onBuildStop},}
		return {"execute" : cls.execute}

	@classmethod
	def classRigGrp(cls):
		"""base group for all tilePile stuff, named by character eventually"""
		return invokeNode(name="tilePile", type="transform")

	def __init__(self, name=None, abstract=None):
		self.character = None
		print "Op instantiated"
		self._opName = None
		self.opName = name or self.__class__.__name__
		self.abstract = abstract
		self.actions = {}

		self.uuid = self.shortUUID(4)
		if self.abstract:
			self.inputRoot = abstract.inputRoot
			self.outputRoot = abstract.outputRoot
		else:
			print "no abstract passed"
			self.inputRoot = AbstractAttr(role="input", hType="root", name="inputRoot")
			self.outputRoot = AbstractAttr(role="output", hType="root", name="outputRoot")
		self.defineAttrs() # override this specific method with attr construction
		#self.data = copy.deepcopy(self.data)
		self.redraw = False  # single interface with UI

		# abstract interface
		# signals directly from abstract
		self.sync = None
		self.attrsChanged = None
		self.attrValueChanged = None
		self.settings = None
		self.evaluator = None

		if self.abstract:
			self.setAbstract(abstract)

		#self.refreshIo()
		#self.actions = copy.deepcopy(self.actions) # /shrug
		self.makeBaseActions()


		# network nodes holding input and output plugs
		self.inputNetwork = None
		self.outputNetwork = None
		self.nodes = self.nodesFromScene() # set
		debug(self.inputNetwork)

		#experimental
		self.deltaStack = MayaStack()

	def executionManager(self):
		return OpExecutionManager(self)

	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		"""attach op to abstractNode, and merge input and outputRoots"""
		self.abstract = abstract
		print "abstract is {}".format(abstract)
		print "abstract class is {}".format(abstract.__class__)
		print "abstract mclass is {}".format(abstract.__class__.__class__)
		print "new absInstance sync is {}".format(abstract.sync)

		self.inputRoot = abstract.inputRoot
		self.outputRoot = abstract.outputRoot
		if define:
			self.defineAttrs() # resets attributes, don't call on regeneration
		#print "outputs after defineAttrs are {}".format(self.outputs)
		# support for redefining attributes from dict
		if inDict:
			self.inputRoot = self.inputRoot.fromDict(inDict, node=abstract)
		if outDict:
			self.outputRoot = self.outputRoot.fromDict(outDict, node=abstract)
		# no luck all skill
		self.redraw=True

		print ""
		self.sync = self.abstract.sync
		self.attrsChanged = self.abstract.attrsChanged
		self.attrValueChanged = self.abstract.attrValueChanged

		# settings
		self.settings = self.abstract.settings
		self.evaluator = self.abstract.evaluator

		self.makeBaseActions()

		# i would really like some meta way to supplant all op-level methods
		# with the "correct" abstract-level versions

	def makeBaseActions(self):
		self.addAction(actionItem=ActionItem(name="clear Maya scene", execDict=
			{"func" : self.clearMayaRig}))
		self.addAction(func=self.showGuidesWrapper, name="showGuides")

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
		Env.log(message, **kwargs)

	@property
	def inputs(self):
		#return {i.name : i for i in self.inputRoot.getAllChildren()}
		if self.abstract:
			return self.abstract.inputRoot.getAllChildren()
		return self.inputRoot.getAllChildren()

	@property
	def outputs(self):
		#return {i.name : i for i in self.outputRoot.getAllChildren()}
		if self.abstract:
			return self.abstract.outputRoot.getAllChildren()
		return self.outputRoot.getAllChildren()


	@staticmethod
	def addAttr(parent=None, name=None, dataType=None,
	            hType=None, desc="", default=None, attrItem=None,
	            *args, **kwargs):
		if attrItem:
			print "adding attrItem {} directly to {}".format(attrItem.name, parent.name)
			return parent.addChild(attrItem)
		#print "base addAttr name is {}".format(name)
		if parent.attrFromName(name=name):
			print "attr {} already in {} children".format(
				name, parent.name)
			return parent.attrFromName(name)
		return parent.addAttr(name=name, dataType=dataType, hType=hType,
		                      desc=desc, default=default, *args, **kwargs)

	def removeAttr(self, name, role="output"):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)

		attr.parent.removeAttr(name)
		self.redraw = True
		self.sync()


	@staticmethod
	def addAttrsFromDict(parent=None, fromDict=None):
		pass
		# for k, v in fromDict.iteritems():
		# 	newAttr = None

	def addInput(self, parent=None, name=None, dataType=None,
	             hType="leaf", desc="", default=None, attrItem=None,
	             *args, **kwargs):
		parent = parent or self.inputRoot
		self.redraw = True
		return self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)

	def addOutput(self, parent=None, name=None, dataType=None,
	              hType="leaf", desc="", default=None, attrItem=None,
	              *args, **kwargs):
		parent = self.outputRoot if not parent else parent
		self.redraw = True
		return self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)

	def getInput(self, name):
		return self.inputRoot.attrFromName(name)

	def searchInputs(self, match):
		return [i for i in self.inputs if match in i.name]

	def searchOutputs(self, match):
		return [i for i in self.outputs if match in i.name]

	def getOutput(self, name):
		# print "getting output {}".format(name)
		# print "current outputs are {}".format(self.outputs)
		return self.outputRoot.attrFromName(name)

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
		#self.refreshIo()
		# do not automatically refresh, let ops call it individually

	def makeAttrArray(self, archetype=None):
		"""intended to be called as part of refreshIo
		:param archetype: base attribute to copy from
		:archetype is """

	def defineAttrs(self):
		"""override with op specifics"""
		raise NotImplementedError("op class {} DOES NOT override defineAttrs, please fix".format(
			self.__class__.__name__))

	def refreshIo(self):
		"""leftover garbage, now used just to call sync"""
		pass

	def connectableInputs(self):
		self.log("op connectableInputs are {}".format(self.inputRoot.getAllConnectable()))
		return self.inputRoot.getAllConnectable()

	def interactibleInputs(self):
		return self.inputRoot.getAllInteractible()

	def connectableOutputs(self):
		return self.outputRoot.getAllConnectable()

	def substituteRoot(self, role="input", newAttr=None):
		"""used to supplant op root attributes with abstract ones"""
		if role == "input":
			attr = self.inputRoot
			vals = attr.serialise()
			self.inputRoot = newAttr.fromDict(vals)
		else:
			attr = self.outputRoot
			vals = attr.serialise()
			self.outputRoot = newAttr.fromDict(vals)

	# ever look at a node and think
	# wtf are you
	@staticmethod
	def edTag(tagNode):
		# more tactile to have a little top tag
		cmds.addAttr(tagNode, ln="edTag", dt="string", writable=True)
		happyList = [
			":)", ":D", ".o/", "^-^", "i wish you happiness",
			"bein alive is heckin swell!!!", "it's a beautiful day today",
		]
		ey = random.randint(0, len(happyList) - 1)
		cmds.setAttr(tagNode + ".edTag", happyList[ey], type="string")
		cmds.setAttr(tagNode + ".edTag", l=True)

	@staticmethod
	def checkTag(tagNode, op=None, specific=False):
		# checks if a node has a specific edTag
		testList = cmds.listAttr(tagNode, string="edTag")

		if testList:
			return True
		else:
			return False

	@staticmethod
	def addTag(tagNode, tagName, tagContent=None):
		# use string arrays(?) to store op that created tag as well as type
		# better to store content of string as dictionary
		if Op.checkTag(tagNode) == False:
			Op.edTag(tagNode)

		cmds.addAttr(tagNode, ln=tagName, dt="string")
		if tagContent:
			# tag content can be anything, keep track of it yourself
			cmds.setAttr(tagNode + "." + tagName, tagContent, type="string")

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

	# might be useful

	def opTag(self, tagNode):
		# add tag for the specific op
		if self.opName:
			cmds.addAttr(tagNode, ln="opTag", dt="string", writable=True)
			cmds.setAttr(tagNode + ".opTag", self.opName, type="string")

	def ECN(self, type, name="blankName", cleanup=False, *args):
		# this is such a good idea
		if name == "blankName":
			name = type
		node = ECN(type, name, *args)
		self.edTag(node)
		self.opTag(node)
		# print "node is {}".format(node)
		# print "self.opGrp is {}".format(self.opGrp)
		if cleanup:
			node = cmds.parent(node, self.opGrp)[0] # prevent messy scenes
		return node

	def ECAsimple(self, type, name="blankName", cleanup=False, *args):
		# this is such a good idea
		# first check if node already exists, later
		node = self.ECN(type, *args, name=name, cleanup=cleanup)
		return AbsoluteNode(node)

	def ECA(self, type, name="blankName", *args):
		node = self.ECAsimple(type, name, cleanup=False, *args)
		self.nodes.update(node)
		#cmds.parent(node, self.opGrp)
		return node

	@staticmethod
	def shortUUID(length=4):
		return shortUUID(length=length)

	# execution
	def execute(self):
		raise NotImplementedError()

	def reset(self):
		"""as this rigging system should be purely additive,
		just delete all associated nodes"""
		for i in self.nodes:
			if cmds.objExists(i):
				cmds.delete(i)

	def beforeExecution(self):
		"""create network nodes procedurally from attributes
		called by context immediately before exec"""
		self.inputNetwork = self.ECA("network", name=self.opName+"_inputs")
		self.outputNetwork = self.ECA("network", name=self.opName + "_outputs")

		attr.makeStringConnection(self.inputNetwork, self.outputNetwork,
								  startName="opStart", endName="opEnd")

		for i in self.inputRoot.getAllLeaves():
			self.makeOpIoNodes(self.inputNetwork, i)

		for i in self.outputRoot.getAllLeaves():
			self.makeOpIoNodes(self.outputNetwork, i)

		# now connect inputs to previous outputs
		for i in self.inputRoot.getAllLeaves():
			self.connectInputPlug(i)

	def afterExecution(self):
		"""immediately after exec"""
		pass

	def propagateOutputs(self):
		"""connect attrItem plugs in maya"""
		for i in self.outputs:
			for n in i.getConnections(): # will return abstractEdges
				# this is a car fire but it works for now
				cmds.connectAttr(i.plug, n.destAttr.plug)


	# dataMapping = {
	# 	"0D" : "matrix",
	# 	"1D" : "nurbsCurve",
	# 	"2D" : "mesh",
	# 	"string" : "string",
	# 	"int" : "long",
	# }

	def makeOpIoNodes(self, node, attrItem, parentItem=None):
		""":param node: AbsoluteNode
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
				self.makeOpIoNodes(node, n, parentItem=i)

		if i.dataType == "enum":
			options = ":".join(i.extras.get("items"))
			plug = attr.addAttr(node, attrName=attrItem.name, attrType="enum",
			             parent=parentPlug,
						 enumName=options)
		elif i.dataType == "nD":
			"""this is a bit involved. in theory if nd attribute has no input it shouldn't
			exist at all - however, for purpose of my sanity, with no input it will
			default to matrix.
			with input connection, it will copy that datatype, with conversion (presume
			to matrix) taking place internally to op"""
			if i.getConnections():
				dt = i.getConnections()[0].dataType
				newItem = AbstractAttr(name=i.name, dataType=dt, hType="leaf")
				self.makeOpIoNodes(node, newItem, parentItem)
			else:
				dt = "matrix"
				plug = attr.addAttr(node, attrName=i.name, attrType=dt)
		elif i.dataType in attr.INTERFACE_ATTRS:
			dtdict = attr.INTERFACE_ATTRS[i.dataType]
			attr.makeAttrsFromDict(node,
	                              attrDict={i.name : dtdict},
	                              parent=parentPlug)
			plug = node+ "." + "".join(parentPlug.split(".")[0:]) + i.name
		else:
			dt = i.dataType
			kwargs = i.extras or {}
			plug = attr.addAttr(node, attrName=attrItem.name, attrType=dt,
			                    parent=parentPlug, **kwargs)
		# attr plug now points to network node
		i.plug = plug

		# set plug value if it's simple
		if i.isSimple():
			attr.setAttr(i.plug, i.value)

	@staticmethod
	def connectInputPlug(attrItem):
		"""connect previous network output to new network input
		:param attrItem : AbstractAttr"""
		if attrItem.getConnections():
			prev = attrItem.getConnections()[0]
			if hasattr(prev, name="plug"):
				cmds.connectAttr(prev.plug, attrItem.plug, f=True)

	# io
	def searchData(self, infoName):
		return attrio.getData(infoName, self.dataFilePath)
		pass

	def saveOutData(self, infoName="info", data={}):
		# golly gee willakers
		print "op saving data"
		self.checkDataFileExists()
		attrio.updateData(infoName, data, path=self.dataFilePath)

	# actions
	def getAllActions(self):
		return self.actions

	def addAction(self, actionDict=None, actionItem=None, func=None, name=None):
		if actionDict:
			self.actions.update(actionDict)
		elif actionItem:
			print "adding action {}".format(actionItem)
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
		opDict = {}
		opDict["NAME"] = self.__name__
		opDict["CLASS"] = self.__class__.__name__
		opDict["MODULE"] = self.__class__.__module__
		opDict["opName"] = self.opName
		#copyData = copy.copy(self.data)
		#opDict["data"] = copyData
		opDict["inputRoot"] = self.inputRoot.serialise()
		opDict["outputRoot"] = self.outputRoot.serialise()
		return opDict

	@staticmethod
	def fromDict(regenDict, abstract=None):
		"""regenerates op from dict"""
		module = regenDict["MODULE"]
		loadedModule = Op.safeLoadModule(module)
		try:
			opClass = getattr(loadedModule, regenDict["CLASS"])
			opInstance = opClass(name=regenDict["opName"])
		except Exception as e:
			print "ERROR in reconstructing op {}".format(regenDict["NAME"])
			print "error is {}".format(str(e))
			return None

		#opInstance.opName = regenDict["opName"]

		# print "default inputs are {}".format(opInstance.inputs)
		if abstract:
			opInstance.inputRoot = abstract.inputRoot
			opInstance.outputRoot = abstract.outputRoot
		else:
			opInstance.inputRoot = AbstractAttr.fromDict(regenDict["inputRoot"])
			opInstance.outputRoot = AbstractAttr.fromDict(regenDict["outputRoot"])


		# print "new inputs are {}".format(opInstance.inputs)
		# print "new outputs are {}".format(opInstance.outputs)
		opInstance.data = regenDict.get("data")
		#opInstance.addAction(func=opInstance.showGuides)
		opInstance.makeBaseActions()
		return opInstance

	@staticmethod
	def safeLoadModule(mod):
		"""takes string name of module"""
		return safeLoadModule(mod)

	def delete(self):
		"""deletes op instance"""
		self.reset()
		del self

	def showGuides(self):
		"""used to allow user direction over op, as a separate process
		to execution"""
		return True
		pass

	def showGuidesWrapper(self):
		self.showGuides()


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
		cmds.file(new=True, f=True)

	def nodesFromScene(self):
		"""list all nodes created by the op, called on instantiation
		returns set"""
		all = cmds.ls()
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