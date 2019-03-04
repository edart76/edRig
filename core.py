# core functions and useful things
import maya.cmds as cmds
import maya.api.OpenMaya as om
import math, random, sys, uuid, copy, functools
from nodule import nodule

sys.dont_write_bytecode = True


def isThisMaya():
	"""returns true if code is run from within maya, else false"""
	# use the frames
	return True  # for now


# basic parenting
def EdPar(children, parent, rel=False):
	for i, item in enumerate(children):
		cmds.parent(item, parent, relative=rel)

def isNode(target):
	return cmds.objExists(target)

def isPlug(target):
	"""returns true for format pCube1.translateX"""
	node = target.split(".")[0]
	if not isNode(target):
		return False
	plug = "".join(target.split(".")[0:])
	if plug in cmds.listAttr(node):
		return True
	return False

def makeList(test):
	if not isinstance(test, list):
		return [test]
	return test

def shortUUID(length=4):
	uid = ""
	for i in range(length):
		o = str(random.randint(0, 9))
		uid += o
	return uid


def nameDeco(name):
	if name:
		n = name + "_"
	else:
		n = ""
	return n


def nodeFromAttr(attr):
	node = (attr.split(".")).pop(0)
	return node


def shapeListFromTf(tf):
	return cmds.listRelatives(tf, shapes=True)

def tfFromShape(shape):
	return cmds.listRelatives(shape, parent=True)

def invokeNode(name="", type="", parent="", func=None):
	# print "core invokeNode looking for {}".format(name)
	if cmds.objExists(name):
		#print "found {}".format(name)
		return AbsoluteNode(name)
	if not func:
		func = ECA
	node = func(type=type, name=name)
	if parent and cmds.objExists(parent):
		#print "parenting invoked"
		cmds.parent(node, parent)
	return node


def con(start, end, *args):
	# cmds.connectAttr is so fun to type every single time
	# no apologies
	# this will literally save my hands

	# or so i thought
	# i was very young and very stupid

	startBool = isAttr(start)
	endBool = isAttr(end)
	if "nf" or "noForce" in args:
		force = False
	else:
		force = True
	next = False
	startChilds = []
	endChilds = []
	if startBool and endBool:
		startChilds = isAttr(start, "multi")
		endChilds = isAttr(end, "multi")
		#
		# print startChilds
		# print endChilds

		if not (startChilds or endChilds):
			cmds.connectAttr(start, end, f=force, na=next)
			# simples

		elif startChilds or endChilds:
			if not startChilds:
				startChilds.append(start)
			if not endChilds:
				endChilds.append(end)

			if len(startChilds) > 1 and len(endChilds) > 1:
				if len(startChilds) == len(endChilds):
					cmds.connectAttr(start, end, f=force, na=next)
					# visually i prefer every individual connection to be shown,
					# but this evaluates faster (i think)
				else:
					x = 0
					if len(startChilds) < len(endChilds):
						x = len(startChilds)
					else:
						x = len(endChilds)
					for i in range(x):
						cmds.connectAttr(startChilds[i], endChilds[i],
						                 f=force, na=next)

			elif len(endChilds) > 1 and not len(startChilds) > 1:
				# print "start is {}, startChilds is {}".format(start, startChilds)
				# print "end is {}, endChilds is {}".format(end, endChilds)
				for i in endChilds:
					print i
					cmds.connectAttr(start, i, f=force, na=next)

			elif len(startChilds) > 1 and not len(endChilds) > 1 and "1D" in endChilds[0]:
				# aaaaaa
				print "it's a 1D pma"
				for i in startChilds:
					cmds.connectAttr(i, "{}[{}]".format(end, nextIndex(end)))

	else:
		print "failed - one of {}, {} doesn't exist".format(start, end)


def nextIndex(attr, startIndex=0):
	# testList = attr.split(".")
	# testNode = testList.pop(0)
	# testAttr = ("".join(testList))
	while startIndex < 1000:
		if len(cmds.connectionInfo("{}[{}]".format(attr, startIndex), sfd=True) or []) == 0:
			return startIndex
		startIndex += 1
	return 0


def edSet(attr, val):
	if not isinstance(val, list):
		val = [val]
	mult = isAttr(attr, "multi")
	# print "attr is {}, val is {}".format(attr, val)
	if mult:
		# print "mult is {}".format(mult)
		for i, multAttr in enumerate(mult):
			# print i, multAttr
			cmds.setAttr(multAttr, val[i % len(val)])
	else:
		cmds.setAttr(attr, val[0])
	# just don't feed this stuff that doesn't exist?


# free code and messy code are the same thing
def argLink(arg, target, *args):
	# connects argument if it's an attribute,
	# sets it if not
	if isAttr(arg):
		con(arg, target)
	elif cmds.objExists(arg):
		if args:
			# so structure is (transform, attr, ".rotateY")
			try:
				con(arg, target)
			except:
				con(arg + args[0], target)
	else:
		edSet(target, arg)
		# is it a node, do we need to get the translate?
		# only set once sure it's not any kind of live information


def isType(node, kind):
	if not cmds.objExists(node):
		return False
	return True if cmds.nodeType(node) == kind else False


def attrFromNode(node, attr):
	x = "{}.{}".format(node, attr)
	# make this cleverer if needs be
	return x


def breakConnections(attr):
	# whoever the fuck wrote the original needs to be kicked in the mouth
	connected = cmds.listConnections(attr, plugs=True, source=True,
	                                 skipConversionNodes=True, destination=False)
	if connected:
		#print "connected is {}, breaking".format(connected)
		cmds.disconnectAttr(connected[0], attr)
		# why the fuck is this not default


def isAttr(test, *args):
	# OH BOY ATTRIBUTEQUERY SUCKS BIG THROBBING DONG
	if not isinstance(test, basestring):
		return False
	# elif cmds.objExists(test):
	# return False
	# print "test is " + test
	testList = test.split(".")
	testNode = testList.pop(0)
	testAttr = ("".join(testList))
	# get rid of brackets because maya is awesome

	bracketIndex = testAttr.find("[")
	if bracketIndex > -1:
		testAttr = testAttr[:bracketIndex]  # python too weak to do this inline
	# print "testList is {}".format(testList)
	# print "testNode is {}".format(testNode)
	# print "testAttr is {}".format(testAttr)

	ex = cmds.attributeQuery(testAttr, node=testNode, exists=True)
	# print "ex is {}".format(ex)
	if not ex or not args:
		return ex
	elif "multi" in args:
		multiList = cmds.attributeQuery(testAttr, node=testNode, listChildren=True)
		multiBool = cmds.attributeQuery(testAttr, node=testNode, multi=True)
		# print "multiBool is {}".format(multiBool)

		multiOut = []
		# print "{} multiList is {}".format(test, multiList)

		if multiList:
			# print "{} multiList is {}".format(test, multiList)
			for i in multiList:
				multiOut.append("{}.{}".format(testNode, i))
				# this is so dumb
		if multiBool and not multiList:
			# aka it's a pma node
			# print "test is " + test
			testIndex = 0
			# print "conInfo is {}.{}[{}]".format(test, testAttr, testIndex)
			# print cmds.connectionInfo(
			# "{}.{}[{}]".format(test, testAttr, testIndex),
			# bracketIndex = test.find("[")
			# print "bracketIndex is {}".format(bracketIndex)
			# bracketString = test[:bracketIndex]
			# print "bracketString is {}".format(bracketString)
			while cmds.connectionInfo(
					test + "[{}]".format(testIndex),
					isExactDestination=True):
				# print test + "[{}]".format(testIndex)
				testIndex = testIndex + 1
				# print "testIndex is {}".format(testIndex)
			multiOut = [test + "[{}]".format(testIndex)]
			# print "multiOut is {}".format(multiOut)
			# print ""

		# print "multiOut is {}".format(multiOut)
		return multiOut

		# else:
		#     return []
	# elif "child" or "children" or "childs" in args:

	# this assumes feeding test values as "node.attribute" - you know,
	# the sane way that data is handled through all maya coding


def debug(var):
	# print repr(eval(var)) + "is" + var
	#print [i for i in globals().iteritems()]
	xName = [k for k, v in globals().iteritems() if v is var]
	print "{} is {}".format(xName, var)


def loc(name):
	# bread + butter
	locTransform = nodule(cmds.spaceLocator(n=name)[0])
	return locTransform
	# maya for once correctly assumes that if you need access to a locator shape,
	# you're a scrub


def ECN(kind, name, *args):
	# node creation without carpal conflagration
	# short for EdCreateNode

	if kind == "pma":
		node = cmds.createNode("plusMinusAverage", n=name)
		if "-" in args:
			cmds.setAttr(node + ".operation", 2)

	elif kind == "md":
		node = cmds.createNode("multiplyDivide", n=name)
		if "div" in args:
			cmds.setAttr(node + ".operation", 2)

	elif kind == "npc":
		node = cmds.createNode("nearestPointOnCurve", n=name)

	elif kind == "pci":
		##### DEPRECATED #####
		# use curve.pciAtU instead for improved efficiency
		node = cmds.createNode("pointOnCurveInfo", n=name)
		cmds.setAttr(node + ".turnOnPercentage", 1)
		# seriously if you use this raw you mess up everything
		# and your frames pay for it

	elif kind == "db":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "vp":
		node = cmds.createNode("vectorProduct", n=name)
		cmds.setAttr(node + ".normalizeOutput", 1)
		# 0=none, 1=dot, 2=cross, 3=vecMatProd, 4=pointMatProd
		a = 0
		if "dot" in args:
			a = 1
		elif "cross" in args:
			a = 2
		elif "vmp" in args:
			a = 3
		elif "pmp" in args:
			a = 4  # tragically, the pimp setting is useless
		cmds.setAttr(node + ".operation", a)

	elif kind == "abnar":
		# the true medicinal power of ECN becomes clear
		node = cmds.createNode("animBlendNodeAdditiveRotation", n=name)

	elif kind == "rev":
		node = cmds.createNode("reverse", n=name)

	# quat block
	elif kind == "etq":
		node = cmds.createNode("eulerToQuat", n=name)
	elif kind == "qte":
		node = cmds.createNode("quatToEuler", n=name)
	elif kind == "qtp":
		node = cmds.createNode("quatProd", n=name)
	elif kind == "qtc":
		node = cmds.createNode("quatConjugate", n=name)
	elif kind == "qtn":
		node = cmds.createNode("quatNormalize", n=name)

	elif kind == "ab":
		node = cmds.createNode("angleBetween", n=name)

	elif kind == "multMatrix":
		node = cmds.createNode("multMatrix", n=name)

	elif kind == "matDecomp":
		node = cmds.createNode("decomposeMatrix", n=name)

	elif kind == "adl":
		node = cmds.createNode("addDoubleLinear", n=name)

	elif kind == "mdl":
		node = cmds.createNode("multDoubleLinear", n=name)

	elif kind == "aim":
		node = cmds.createNode("aimConstraint", n=name)

	elif kind == "pmm":
		node = cmds.createNode("pointMatrixMult", n=name)
		cmds.setAttr(node + ".vectorMultiply", 1)
		cmds.setAttr(node + ".inPointX", 1)
		if "vmOff" in args:
			cmds.setAttr(node + ".vectorMultiply", 0)


	elif kind == "rebuildCrv":
		node = cmds.createNode("rebuildCurve", n=name)

	elif kind == "rmv":
		node = cmds.createNode("remapValue", n=name)
		# args to set min and max values

	elif kind == "pb":
		node = cmds.createNode("pairBlend", n=name)

	elif kind == "cnd":
		node = cmds.createNode("condition", n=name)

	elif kind == "clamp":
		node = cmds.createNode("clamp", n=name)

	elif kind == "choice":
		node = cmds.createNode("choice", n=name)

	elif kind == "joint":
		node = cmds.createNode("joint", n=name)

	elif kind == "4x4":
		node = cmds.createNode("fourByFourMatrix", n=name)

	elif kind == "aim":
		node = cmds.createNode("aimConstraint", n=name)

	elif kind == "fitB":
		node = cmds.createNode("fitBspline", n=name)

	elif kind == "composeMat":
		node = cmds.createNode("composeMatrix", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	else:
		# raise RuntimeError("Kind {} is not recognised - please choose an ECN-supported node".format(kind))
		node = cmds.createNode(kind, n=name)

	if isinstance(node, list):
		node = node[0]
	if node:
		# cmds.select(clear=True)
		return node


def ECn(kind, name, *args):
	return nodule(ECN(kind, name, *args))


def mag(x):
	return math.sqrt(sum(i ** 2 for i in x))


def isEqual(x, y, tolerance=0.0001):
	# are x and y equal to within tolerance?
	return abs(x - y) < tolerance


def MObjectFrom(node):
	# get the MObject from anything
	# print "getting MObject"
	sel = om.MSelectionList()
	# print "sel is {}".format(sel)
	# print "object node is {}".format(node)
	sel.add(node)
	ref = sel.getDependNode(0)
	#print "ref is {}".format(ref)
	# ref is now MObject referring to node,
	# regardless if dag
	return ref


def MFnTransformFrom(dag):
	# is this a transform or already an MObject?
	#print "dag is {}".format(dag)
	if cmds.objExists(dag):
		object = MObjectFrom(dag)
	else:
		object = dag
	fn = om.MFnTransform(object)
	return fn


def MMatrixFrom(dag):
	tfn = MFnTransformFrom(dag)
	transMat = tfn.transformation()
	return transMat.asMatrix()


def setColour(dag, colour):
	cmds.setAttr(dag + ".overrideEnabled", 1)
	for i, val in enumerate(["R", "G", "B"]):
		cmds.setAttr(dag + ".overrideColour" + val, colour[i])


def rotOrder(order, toInt=False, toString=False):
	stringList = ["xyz", "zyx", "zxy", "xzy", "yxz", "zyx"]
	if toInt:
		int = stringList.find(order)
		return int
	elif toString:
		string = stringList[order]
		return string


def duplicateShape(shape, search="", replace=""):
	oldTf = cmds.listRelatives(shape, parent=True)[0]
	oldShapeType = cmds.nodeType(shape)
	newName = shape.replace(search, replace)
	newTf = cmds.duplicate(shape, name="temp", rc=True)[0]
	newShapeList = cmds.listRelatives(newTf, shapes=True)
	#print "newShapeList is {}".format(newShapeList)
	# uuuuugh
	newShape = [i for i in newShapeList if shape[:-1] in i][0]
	# NO DUPLICATE SHAPE NAMES KIDDOS
	#print "newShape is {}".format(newShape)
	newShape = cmds.rename(newShape, newName)
	# newTf = cmds.listRelatives(newShape, parent=True)[0]
	newShape = cmds.parent(newShape, oldTf, r=True, s=True)[0]
	# ugly but whatevs
	# con(shape+".local", newShape+".create")
	# breakConnections(newShape+".create")
	#print "newTf is {}".format(newTf)
	cmds.delete(newTf)
	return newShape

def shapeFrom(target):
	"""sometimes you just say gimme the shape
	ask and ye shall receive"""
	if "shape" in cmds.nodeType(target, inherited=True):
		return target
	else:
		return cmds.listRelatives(target, shapes=True)[0]

def tfFrom(target):
	if "transform" == cmds.nodeType(target):
		return target
	else:
		return cmds.listRelatives(target, parent=True)[0]


def getRoughSceneScale():
	# highest highs and lowest lows
	# qol function to avoid plan elements appearing at totally useless scales
	# returns bounding box of everything in scene
	return cmds.exactWorldBoundingBox(cmds.ls(allDag=True), ignoreInvisible=True)
	pass

def isoViewPoint():
	"""returns point at which to place camera in order to give a consistent
	viewpoint
	totally distinct from the one at framestore because this actually works"""
	v = getRoughSceneScale()
	mag = math.sqrt(v[3]*2 + v[4]*2 + v[5]*2)
	return (1, 1, 1) * (mag + mag/2.0)

# argument functions, allowing functions to take either transforms or

class AbsoluteNode(str):
	# DON'T LOSE YOUR WAAAAY
	def __new__(cls, node):
		# this is the stripped down fast version of pymel
		if isinstance(node, AbsoluteNode):
			return node
		if isinstance(node, list):
			return AbsoluteNode(node[0])
		absolute = str.__new__(cls, node)
		absolute.node = node
		if not cmds.objExists(node):
			print "{} DOES NOT EXIST - YER OFF THE MAP".format(node)
			absolute.refreshPath = absolute.returnBasicNode
			return absolute
		# print "node is {}".format(node)
		# print "node type is {}".format(type(node))
		# if not "|" in node:
		# 	node = "|" + node
		absolute.MObject = MObjectFrom(node)
		absolute.MFnDependency = om.MFnDependencyNode(absolute.MObject)
		absolute._shapeFn = None
		absolute.MDagPath = None
		# check if it's dag or just dependency
		if absolute.MObject.hasFn(107): # MFn.kDagNode
			absolute.MDagPath = om.MDagPath.getAPathTo(absolute.MObject)
			absolute.MFnDagNode = om.MFnDagNode(absolute.MObject)
			absolute.refreshPath = absolute.refreshDagPath
			if absolute.MObject.hasFn(110): # MFnTransform
				absolute.MFnTransform = om.MFnTransform(absolute.MObject)

		elif absolute.MObject.hasFn(4): # dependency
			absolute.refreshPath = absolute.returnDepNode

		# metaprogramming for fun and profit
		# cmds.select(clear=True)
		return absolute

	def __init__(self, *args, **kwargs):
		super(AbsoluteNode, self).__init__(*args, **kwargs)

		pass

	def __str__(self):
		self.refreshPath()
		if isinstance(self.node, list):
			self.node = self.node[0]
		return self.node

	def __repr__(self):
		self.refreshPath()
		if isinstance(self.node, list):
			self.node = self.node[0]
		return self.node

	def refreshDagPath(self):
		self.MDagPath = om.MDagPath.getAPathTo(self.MObject)
		#self.node = self.MDagPath.fullPathName()
		self.node = self.MFnDagNode.fullPathName()

	def returnDepNode(self):
		self.node = self.MFnDependency.name()

	def returnBasicNode(self):
		return self.node

	@property
	def name(self):
		return self.node.split("|")[-1]

	@name.setter
	def name(self, value):
		# is this a bad idea
		#cmds.rename(self.node, value)
		self.MFnDependency.setName(value)
	# i've got no strings, so i have fn

	@property
	def shapeFnType(self):
		# lightweight way to know how to treat the shapeFn
		if self.MObject.hasFn(296): # kMesh
			return "kMesh"
		elif self.MObject.hasFn(267): # kNurbsCurve
			return "kNurbsCurve"
		elif self.MObject.hasFn(294): # kNurbsSurface
			return "kNurbsSurface"
		else:
			return None

	@property
	def shapeFn(self):
		# initialise costly shape mfns only when needed, then never again
		if not self._shapeFn:
			if self.shapeFnType:
				self._shapeFn = eval("om.MFn"+self.shapeFnType[1:]+"(self.MObject)")
			else:
				return self.shape.shapeFn
		return self._shapeFn

	@property
	def isCurve(self):
		return self.shapeFnType == "kNurbsCurve"
	@property
	def isMesh(self):
		return self.shapeFnType == "kMesh"
	@property
	def isSurface(self):
		return self.shapeFnType == "kNurbsSurface"


	@property
	def shape(self):
		"""this feels like a bad idea"""
		if self.isShape():
			return self
		else:
			return AbsoluteNode(shapeFrom(self.node))

	@property
	def transform(self):
		if self.isTransform():
			return self
		else:
			return AbsoluteNode(tfFrom(self))


	def isTransform(self):
		if self.shapeFnType:
			return False
		if self.MDagPath:
			return True
		else:
			return False

	def isShape(self):
		if self.shapeFnType:
			return True

	def delete(self, full=True):
		"""deletes maya node, and by default deletes entire openmaya framework around it
		tilepile is very unstable, and i think this might be why"""
		name = self.node
		self.MObject = None

		cmds.delete(name)

	@property
	def nodeType(self):
		"""returns string name of node type - "joint", "transform", etc"""
		return cmds.nodeType(self.node)


def ECA(type, name, *args):
	# node = cmds.createNode(type, n=name)
	node = ECN(type, name, *args)
	return AbsoluteNode(node)

class NodeFunction(object):
	"""decorator class that encapsulates maya node functions with network nodes"""
	def __init__(self, fn):
		functools.update_wrapper(self, fn)
		self.fn = fn

	def __call__(self, *args, **kwargs):
		""""""





#
# class Op(object):
# 	# base class for "operations" in Maya scripting
# 	opName = None
# 	controller = None
#
# 	def __init__(self, name=None):
# 		self.character = None
# 		print "Op instantiated"
# 		self._opName = None
# 		if not name:
# 			self.opName = self.__class__.__name__
# 		else:
# 			self.opName = name
#
# 		self.uuid = self.shortUUID(4)
# 		#self.uuid =
# 		# self.inputs = {}
# 		# self.outputs = {}
# 		# ops have inputs and outputs, but you need to define them yourself
#
# 	@property
# 	def __name__(self):
# 		# return str(self.__class__) + "-" + self.opName + "-" + self.uuid
# 		return str(self.__class__.__name__) + "-" + self.opName
#
# 	@property
# 	def opName(self):
# 		# because this wasn't confusing enough already
# 		if self._opName:
# 			return self._opName
# 		else:
# 			return self.__class__.__name__ #+ self.uuid
#
# 	@opName.setter
# 	def opName(self, val):
# 		# equivalent to renaming an op
# 		if self.controller:
# 			self.controller.renameOp(op=self, newName=val)
# 		else:
# 			self._opName = val
# 			# return val
#
# 	def rename(self, name):
# 		self.opName = name
#
#
# 	# ever look at a node and think
# 	# wtf are you
# 	@staticmethod
# 	def edTag(tagNode):
# 		# more tactile to have a little top tag
# 		cmds.addAttr(tagNode, ln="edTag", dt="string", writable=True)
# 		happyList = [
# 			":)", ":D", ".o/", "^-^", "i wish you happiness",
# 			"bein alive is heckin swell!!!", "it's a beautiful day today",
# 		]
# 		ey = random.randint(0, len(happyList) - 1)
# 		cmds.setAttr(tagNode + ".edTag", happyList[ey], type="string")
# 		cmds.setAttr(tagNode + ".edTag", l=True)
#
# 	@staticmethod
# 	def checkTag(tagNode, op=None, specific=False):
# 		# checks if a node has a specific edTag
# 		testList = cmds.listAttr(tagNode, string="edTag")
#
# 		if testList:
# 			return True
# 		else:
# 			return False
#
# 	@staticmethod
# 	def addTag(tagNode, tagName, tagContent=None):
# 		# use string arrays(?) to store op that created tag as well as type
# 		# better to store content of string as dictionary
# 		if Op.checkTag(tagNode) == False:
# 			Op.edTag(tagNode)
#
# 		cmds.addAttr(tagNode, ln=tagName, dt="string")
# 		if tagContent:
# 			# tag content can be anything, keep track of it yourself
# 			cmds.setAttr(tagNode + "." + tagName, tagContent, type="string")
#
# 	@staticmethod
# 	def getTag(tagNode, tagName=None):
# 		# retrieves specific tag information, or lists all of it
# 		if tagName:
# 			gotTag = cmds.getAttr(tagNode + "." + tagName)
# 		else:
# 			gotTag = cmds.listAttr(tagNode, string="*tag")
# 		return gotTag
#
# 	# might be useful
#
# 	def opTag(self, tagNode):
# 		# add tag for the specific op
# 		if self.opName:
# 			cmds.addAttr(tagNode, ln="opTag", dt="string", writable=True)
# 			cmds.setAttr(tagNode + ".opTag", self.opName, type="string")
#
# 	def ECN(self, type, name="blankName", *args):
# 		# this is such a good idea
# 		if name == "blankName":
# 			name = type
# 		node = ECN(type, name, *args)
# 		self.edTag(node)
# 		self.opTag(node)
# 		return node
#
# 	def ECA(self, type, name="blankName", *args):
# 		# this is such a good idea
# 		# first check if node already exists, later
# 		node = self.ECN(type, *args, name=name)
# 		return AbsoluteNode(node)
#
# 	def ECn(self, type, name="blankName", *args):
# 		if name == "blankName":
# 			name = type
# 		node = self.ECN(type, name, *args)
# 		return nodule(node)
#
# 	@staticmethod
# 	def shortUUID(self, length=4):
# 		return shortUUID(length=length)
#
# 	def serialise(self):
#
# 		opDict = {}
# 		opDict["NAME"] = self.__name__
# 		opDict["CLASS"] = self.__class__.__name__
# 		opDict["MODULE"] = self.__class__.__module__
# 		opDict["opName"] = self.opName
#
# 		copyData = copy.copy(self.data)
# 		opDict["data"] = copyData
#
# 		return opDict


def isInstanceUserDefined(instance):
	cls = instance.__class__
	if hasattr(cls, "__class__"):
		return ("__dict__" in dir(cls) or hasattr(cls, "__slots__"))

def ruggedSerialise(object):
	# have a better crack at serialising datatypes and absoluteNodes
	# for now though
	return None

#
# class NodeOp(Op):
# 	# class referring to operations with nodes
# 	def __init__(self):
# 		Op.__init__(self)
# 		self.nodes = []
#
#
# class VecFromTo(NodeOp):
# 	# persistent vectors
# 	# def __init__(self, from=None, to=None):
# 	#     self.vec = self.ECN("pma", "-")
# 	pass
#
#
# def crossProduct(name, start, mid, end):
# 	# vectors are from midpoint to start and end
# 	# if you can say it better i'd love to hear it
# 	vecA = vecFrom("vec{}to{}".format(mid, start), mid, start)
# 	vecB = vecFrom("vec{}to{}".format(mid, end), mid, end)
#
# 	cross = ECN("vp", name)
# 	cmds.setAttr(cross + ".operation", 2)
#
# 	mag = ECN("md", name)
# 	ctrl = ECN("mdl", name + "_ctrl")
#
# 	for ax in "XYZ":
# 		con(ctrl + ".output", mag + ".input1" + ax)
#
# 	con(vecA, cross + ".input1")
# 	con(vecB, cross + ".input2")
# 	out = mag + ".output"
# 	# add system to flip vector with condition and mdiv
#
# 	return out
#
#
# class BlendRot(NodeOp):
# 	# blend rotations without using blendColours
# 	# (eg without using unitConversions, and bringing SHAME on family)
# 	def __init__(self, rot1, rot2):
# 		super(BlendRot, self).__init__()
# 		self.rot1 = start
# 		self.rot2 = end
#
# 		rot1 = self.rot1 + ".rotate"
# 		rot2 = self.rot2 + ".rotate"
#
# 		rev = ECN("rev", "rotRev")
# 		rotBlend = ECN("abnar", "rotBlend")
#
# 		in1 = rotBlend + ".inputA"
# 		in2 = rotBlend + ".inputB"
# 		blend = rev + "inputX"
# 		out = rotBlend + ".output"
#
# 		self.inputs.append(in1, in2, blend)
# 		self.outputs.append(out)
# 		self.nodes.append(rev, rotBlend)
#
# 		cmds.connectAttr(rev + ".outputX", rotBlend + ".weightA")
# 		cmds.connectAttr(rev + ".inputX", rotBlend + ".weightB")
# 		cmds.connectAttr(rot1, in1)
# 		cmds.connectAttr(rot2, in2)
#
#
# class Normalise(NodeOp):
# 	# normalise any three values
# 	def __init__(self, values):
# 		super(Normalise, self).__init__()
# 		self.values = values
# 		norm = ECN("vp", "normalise")
#
# 		in1 = norm + ".input1"
# 		out1 = norm + ".output"
#
# 		self.inputs.append(in1)
# 		self.outputs.append(out1)
# 		self.nodes.append(norm)
#
# 		for i, axis in "XYZ":
# 			cmds.connectAttr(values[i], in1 + axis)
#
#
# class Trig(NodeOp):
# 	# get sin, cos and tan of any value
# 	def __init__(self, value):
# 		super(Trig, self).__init__()
# 		self.value = value
#
# 		trigNode = ECN("etq", "trigNode")
# 		tanDiv = ECN("md", "tanDiv")
# 		in1 = trigNode + ".inputRotateX"
# 		outSin = trigNode + ".outputQuatW"
# 		outCos = trigNode + ".outputQuatX"
# 		outTan = tanDiv + ".outputX"
#
# 		con(self.value, in1)
# 		con(outSin, tanDiv + ".input1X")
# 		con(outCos, tanDiv + ".input2X")
# 		cmds.setAttr(tanDiv + ".operation", 2)
#
# 		self.inputs.append(in1)
# 		self.outputs.append(outSin, outCos, outTan)
# 		self.nodes.append(trigNode, tanDiv)
#
#
# class MatConst(NodeOp):
# 	# create matrix constraint and bask in frames
# 	def __init__(self, parents, child, offset):
# 		super(MatConst, self).__init__()
#
# 		matMult = ECN("multMatrix")
# 		matDecomp = ECN("matDecomp")
#
# 		in1 = matMult + ".matrixIn[0]"
# 		in2 = matMult + ".matrixIn[1]"
# 		cmds.connectAttr(parents + ".worldMatrix[0]", in1)
# 		cmds.connectAttr(child + ".parentInverseMatrix[0]", in2)
#
# 		cmds.connectAttr(matMult + ".matrixSum", matDecomp + ".inputMatrix")
# 		outQuat = matDecomp + ".outputQuat"
# 		outRot = matDecomp + ".outputRotate"
# 		outScale = matDecomp + ".outputScale"
# 		outTrans = matDecomp + ".outputTranslate"
#
# 		con(outTrans, child + ".translate")
# 		con(outRot, child + ".rotate")
# 		con(outScale, child + ".scale")
#
# 		self.nodes.append(matMult, matDecomp)
# 		self.outputs.append(outTrans, outRot, outScale, outQuat)
#
# 	"""
# 	i suck at python
# 	if len(parents)>1:
# 		#not implemented yet
# 	else:
# 		if offset==False:
# 			in1 = matMult + ".matrixIn[0]"
# 			in2 = matMult
#
# 	"""

randomWords = [
	"this", "is", "a", "test", "how", "shall", "I", "sing", "that", "majesty"
]
def randomWord():
	bound = len(randomWords) - 1
	return randomWords[random.randint(0, bound)]