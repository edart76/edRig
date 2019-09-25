# core functions and useful things
import maya.cmds as cmds
import maya.api.OpenMaya as om
import math, random, sys, functools

sys.dont_write_bytecode = True


def isThisMaya():
	"""returns true if code is run from within maya, else false"""
	# use the frames
	return True  # for now

def isNode(target):
	return cmds.objExists(target)

def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)


def isPlug(target):
	"""returns true for format pCube1.translateX"""
	node = target.split(".")[0]
	if not isNode(target):
		return False
	plug = ".".join(target.split(".")[1:])
	return plug in cmds.listAttr(node)

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

def nodeFromAttr(attr):
	node = (attr.split(".")).pop(0)
	return node


def shapeListFromTf(tf):
	return cmds.listRelatives(tf, shapes=True)

def tfFromShape(shape):
	return cmds.listRelatives(shape, parent=True)


def duplicateShape(shape, search="", replace=""):
	oldTf = cmds.listRelatives(shape, parent=True)[0]
	oldShapeType = cmds.nodeType(shape)
	newName = shape.replace(search, replace)
	newTf = cmds.duplicate(shape, name="temp", rc=True)[0]
	newShapeList = cmds.listRelatives(newTf, shapes=True)
	newShape = [i for i in newShapeList if shape[:-1] in i][0]
	newShape = cmds.rename(newShape, newName)
	newShape = cmds.parent(newShape, oldTf, r=True, s=True)[0]
	cmds.delete(newTf)
	return newShape

def setColour(dag, colour):
	cmds.setAttr(dag + ".overrideEnabled", 1)
	for i, val in enumerate(["R", "G", "B"]):
		cmds.setAttr(dag + ".overrideColour" + val, colour[i])


def rotOrder(order, toInt=False, toString=False):
	stringList = ["xyz", "zyx", "zxy", "xzy", "yxz", "zyx"]
	if toInt:
		int = stringList.index(order)
		return int
	elif toString:
		string = stringList[order]
		return string

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



def ECN(kind, name="", parent=None, *args, **kwargs):
	# node creation without carpal conflagration
	# short for EdCreateNode

	if not name: name = kind

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

	elif kind == "locator":
		node = cmds.spaceLocator(name=name)[0]

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	elif kind == "":
		node = cmds.createNode("distanceBetween", n=name)

	else:
		# raise RuntimeError("Kind {} is not recognised - please choose an ECN-supported node".format(kind))
		node = cmds.createNode(kind, n=name, ss=True)

	if isinstance(node, list):
		node = node[0]

	if node:
		if parent:
			try:
				cmds.parent(node, parent)
			except:
				pass
		#cmds.select(clear=True)
		return node


def mag(x):
	return math.sqrt(sum(i ** 2 for i in x))


def isEqual(x, y, tolerance=0.0001):
	# are x and y equal to within tolerance?
	return abs(x - y) < tolerance


def MObjectFrom(node):
	# get the MObject from anything
	sel = om.MSelectionList()
	sel.add(node)
	ref = sel.getDependNode(0)
	return ref

def stringFromMObject(obj):
	"""opposite, retrieves string name"""
	return om.MFnDagNode(obj).fullPathName()

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


def shapeFrom(target):
	"""sometimes you just say gimme the shape
	ask and ye shall receive"""
	if "shape" in cmds.nodeType(target, inherited=True):
		return target
	else:
		return cmds.listRelatives(target, shapes=True)[0]

def makeShape(name, nodeType):
	"""creates a new shape node and transform,
	names them correctly, and returns the shape"""
	shape = cmds.createNode(nodeType, n=name+"Shape")
	parent = cmds.listRelatives(shape, parent=True)[0]
	cmds.rename(parent, name)
	return shape

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


class NodeFunction(object):
	"""decorator class that encapsulates maya node functions with network nodes"""
	def __init__(self, fn):
		functools.update_wrapper(self, fn)
		self.fn = fn

	def __call__(self, *args, **kwargs):
		""""""





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