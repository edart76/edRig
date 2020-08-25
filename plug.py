"""operations working on plugs as live operation components"""
import math


from edRig import core, attr, ECA, debug, cmds, om, oma



def conOrSet(driver, driven):
	"""if EITHER is a static value, the opposite will be set as a plug"""
	attr.conOrSet(driver, driven)

def vecFromTo(startPlug, endPlug, name=None):
	"""get vector between two plugs"""
	name = name or "vecFrom_{}_{}".format(startPlug, endPlug)
	vec = ECA("plusMinusAverage", name=name)
	vec.set("operation", "subtract") #smart enum setting bois :D
	vec.con(endPlug, vec+".input3D[0]")
	vec.con(startPlug, vec+".input3D[1]")
	return vec+".output3D"

def dividePlug(numerator, divisor):
	mdv = ECA("multiplyDivide", n="divide_{}_by_{}_".format(numerator, divisor))
	mdv.conOrSet(numerator, mdv + ".input1")
	mdv.conOrSet(divisor, mdv + ".input2")
	mdv.set("operation", 2)
	return mdv + ".output"

def multPlugs(*plugs):
	"""multiplies all plugs - optimise to multDoubleLinear here if possible
	sequential pairs of nodes are created for each plug"""
	a = plugs[0]
	# use mdv if compound, mdl if not
	if any( [attr.plugHType(plug) == "compound" for plug in plugs]):
		nodeType = "multiplyDivide"
	else: nodeType = "multDoubleLinear"

	for i in plugs[1:]:
		#mult = ECA("multiplyDivide")
		mult = ECA(nodeType, n="multPlugs")
		mult.conOrSet(a, mult + ".input1")
		mult.conOrSet(i, mult + ".input2")
		a = mult + ".output"
	return a

def multLinearPlugs(*plugs):
	""" optimise the above using combinationShape node """
	debug(plugs)
	if len(plugs) == 2: # special, common case
		node = ECA("multDoubleLinear")
		node.conOrSet(plugs[0], node + ".input1")
		node.conOrSet(plugs[1], node + ".input2")
		return node + ".output"
	node = ECA("combinationShape")
	for i, val in enumerate(plugs):
		node.conOrSet(val, node + ".inputWeight[{}]".format(i))
	return node + ".outputWeight"

def addLinearPlugs(*plugs):
	""" specify individual linear values """
	add = ECA("plusMinusAverage", n="addLinearPlugs")
	for i, val in enumerate(plugs):
		add.conOrSet(val, add + ".input1D[{}]".format(i))
	return add + ".output1D"

def addCompoundPlugs(*plugs):
	""" easier to use plusMinusAverage node here than the above"""
	add = ECA("plusMinusAverage", n="addCompoundPlugs")
	for i, val in enumerate(plugs):
		add.conOrSet(val, add + ".input3D[{}]".format(i))
	return add + ".output3D"

def plugCondition(val1, val2, operation="greaterThan",
                  ifFalse=None, ifTrue=None):
	"""compares conditions, returns either supplied options or
	0 1 if none given"""
	tokens = [u'equal', u'not Equal', u'greater Than', # please kill me
	          u'greater or Equal', u'less Than', u'less or Equal']
	operators = ["equal", "notEqual", "greaterThan", "greaterOrEqual",
	             "lessThan", "lessOrEqual"]
	ops = ["==", "!=", ">", ">=", "<", "<="]
	node = ECA("condition")
	index = ops.index(operation) if operation in ops else operators.index(operation)
	node.set("operation", index )
	node.conOrSet(val1, "firstTerm")
	node.conOrSet(val2, "secondTerm")
	if any((ifFalse, ifTrue)):
		node.conOrSet(ifFalse or (0, 0, 0), "colorIfFalse")
		node.conOrSet(ifTrue or (1, 1, 1), "colorIfTrue")
		return node + ".outColorR"
	node.set("colorIfFalseR", 0)
	node.set("colorIfTrueR", 1)
	return node + ".outColorR"

def plugZeroSafety( val, safetyValue=0.0001):
	""" to prevent maya freaking out about division by zero """
	return plugCondition(val, 0.0, operation="equal",
	                     ifFalse=val, ifTrue=safetyValue)


def plugMin(*args):
	"""gets minimum of a set of plugs"""

def plugAdd(*args):
	"""adds set of plugs"""

def plugAverage(*args):
	"""gets average of plugs"""

def plugDistance(a, b=None):
	"""return euclidean distance between positions"""
	distance = ECA("distanceBetween")
	distance.conOrSet(a, distance+".point1")
	if b:
		distance.conOrSet(b, distance+".point2")
	return distance+".distance"

def setPlugLimits(plug, min=None, max=None):
	""" still not sure on triple plugs """
	node = ECA("clamp")
	for i in [min, max]:
		tag = "max"
		if i == min: tag = "min"
		if i != None:
			node.conOrSet(i, tag)
		else:
			node.conOrSet(plug, tag)
	node.conOrSet(plug, "input")
	if attr.plugHType(plug) == "leaf":
		return node + ".outputR"
	return node + ".output"
	#
	# return plug


def setPlugRange(plug, min=0, max=1,
                 oldMin=0, oldMax=1, name=None):
	name = name or "remap"
	remap = ECA("setRange", n=name)
	remap.conOrSet(min, remap + "min", )
	remap.conOrSet(max, remap + "max",)
	remap.conOrSet(oldMin, remap + "oldMin", )
	remap.conOrSet(oldMax, remap + "oldMax", )
	remap.con(plug, "value")
	return remap + ".outValue"

	pass



def reversePlug(plug):
	"""returns 1 - plug"""
	rev = ECA("reverse", n=plug+"_reverse")
	attr.con(plug, rev+".input")
	return rev+".output"

def periodicSignalFromPlug(plug, period=1.0, amplitude=1.0,
                           profile="linear"):
	"""creates a repeating 0-1 signal from float plug using
	animCurve node
	used for modulo operations"""
	profiles = ("linear", "sine", "cosine", "tan")
	curve = ECA("animCurveUU")
	curve.con(plug, "input")
	fn = oma.MFnAnimCurve(curve.MObject)
	fn.addKey(0.0, 0.0)
	fn.addKey(period, amplitude)
	fn.setTangentTypes([0, 1],
	                   tangentInType=2, tangentOutType=2) # linear, linear
	fn.setPostInfinityType(3) # cycle
	fn.setPreInfinityType(3) # cycle
	return curve + ".output"

def invertMatrixPlug(plug):
	"""returns an inverse matrix plug"""
	node = ECA("inverseMatrix")
	node.con(plug, "inputMatrix")
	return node + ".outputMatrix"

def blendFloatPlugs(plugList=None, blender=None, name="blendPlugs"):
	"""blends float plugs together"""
	blend = ECA("blendTwoAttr", n=name)
	#print "plugList {}".format(plugList)
	for i, val in enumerate(plugList):
		conOrSet(val, blend + ".input[{}]".format(i) )
	conOrSet(blender, blend + ".attributesBlender")
	return blend + ".output"

def blendMatrixPlugs(matrixList=None, driverList=None, name="blendMatrices"):
	""" blends matrix plugs with drivers"""
	node = ECA("wtAddMatrix", n=name)
	for i in range(len(matrixList)):
		plug = node + ".wtMatrix[{}]".format(i)
		conOrSet(matrixList[i], plug + ".matrixIn")
		conOrSet(driverList[i], plug + ".weightIn")
	return node + ".matrixSum"


def blendRotationPlugs(a, b=(0,0,0), name="angleBlend"):
	""" creates an animBlendNodeAdditiveRotation to avoid unit conversions """
	abnar = ECA("animBlendNodeAdditiveRotation", n=name)
	conOrSet(a, abnar + ".inputA")
	conOrSet(b, abnar + ".inputB")
	# i honestly don't know what the best way is anymore
	return {"blender" : abnar + ".weightA",
	        "output" : abnar + ".output"}


def vectorMatrixMultiply(vector=None, matrix=None, normalise=False,
                         name="vectorMatrixMult"):
	node = ECA("vectorProduct", n=name)
	conOrSet(vector, node + ".input1", )
	conOrSet( matrix, node + ".matrix",)
	conOrSet( normalise, node + ".normalizeOutput",)
	attr.setAttr( node + ".operation", "point Matrix Product")
	return node + ".output"
	# BE WARNED
	# vectors from sheared matrices are not normalised properly
	# why would they be

def multMatrixPlugs(plugs, name="matMult"):
	"""multiplies matrix plugs in given sequence"""
	node = ECA("multMatrix", n=name)
	for i, val in enumerate(plugs):
		cmds.connectAttr(val, node+".matrixIn[{}]".format(i))
	return node + ".matrixSum"

def crossProduct(vecA, vecB, normalise=False, name="crossProduct"):
	node = ECA("vectorProduct", n=name)
	conOrSet(vecA, node + ".input1")
	conOrSet(vecB, node + ".input2")
	conOrSet(normalise, node + ".normalizeOutput")
	attr.setAttr(node + ".operation", "cross Product")
	return node + ".output"

def dotProduct(vecA, vecB, normalise=True, name="dotProduct"):
	node = ECA("vectorProduct", n=name)
	conOrSet(vecA, node + ".input1")
	conOrSet(vecB, node + ".input2")
	conOrSet(normalise, node + ".normalizeOutput")
	attr.setAttr(node + ".operation", "dot Product")
	return node + ".outputX"

def normalisePlug(vector, name="normalisePlug"):
	node = ECA("vectorProduct", n=name)
	conOrSet(vector, node + ".input1")
	node.set("operation", 0)
	node.set("normalizeOutput", 1)
	return node + ".output"

trigModes = {"sine" : math.sin,
         "cosine" : math.cos,
         "tangent" : math.tan,
         "arcsine" : math.asin,
         "arccosine" : math.acos,
         "arctangent" : math.atan}

def trigPlug(plug=None, mode="sine", res=16, inputDegrees=True):
	"""remap a plug through a trigonometric function
	no adaptive sampling here yet, very inefficient
	but it's enough for now """

	crv = ECA("animCurveUU", n=mode)
	func = trigModes[mode]
	fn = oma.MFnAnimCurve(crv.MObject)
	if mode in ("sine", "cosine", "tangent"):
		domain = 180.0
		convertToRadians = 1
	else:
		domain = 1.0
		convertToRadians = 0

	step = domain / float(res)
	for i in range(res + 1):
		lookup = step * 2 * i - domain
		if convertToRadians: lookup = math.radians(lookup)
		value = func( lookup )
		fn.addKey(lookup, value)
	fn.setTangentTypes([i for i in range(res + 1)],
	                   tangentInType=4, tangentOutType=4) # spline, spline
	crv.set("preInfinity", 3)
	crv.set("postInfinity", 3)
	if not plug:
		return crv
	crv.con(plug, crv+".input")
	return crv + ".output"

def plugToDegrees(plug):
	node = ECA("multDoubleLinear", name="toDegrees")
	node.set("input2", 180.0 / 3.14159265)
	node.conOrSet(plug, "input1")
	return node + ".output"

def plugToRadians(plug):
	node = ECA("multDoubleLinear", name="toRadians")
	node.set("input2", 3.14159265 / 180.0)
	node.conOrSet(plug, "input1")
	return node + ".output"


# logic stuff
# expects bool signals as input
def orPlugs(a, b):
	add = addLinearPlugs(a, b)
	capped = setPlugLimits(add, max=1)
	return capped

def xorPlugs(*plugs):
	""" probably more elegant way of doing this, just need something now """
	values = ECA("addDoubleLinear", n="XORplugs_negativePositiveOne")
	values.set("input1", 1)
	values.set("input2", -1)
	choices = []
	for i, plug in enumerate(plugs):
		choice = ECA("choice", n="XORplugs{}_choice".format(i))
		choice.con(plug, "selector")
		choice.con(values + ".input2", "input[0]")
		choice.con(values + ".input1", "input[1]")
		choices.append( choice + ".output")
	total = multLinearPlugs(*choices)
	total = setPlugLimits(total, min=0, max=1)
	return reversePlug(total) + "X"

def normaliseBoolPlug(plug):
	""" converts 0 1 signal to -1 1"""
	values = ECA("addDoubleLinear", n="normalise_negativePositiveOne")
	values.set("input1", -1)
	values.set("input2", 1)
	choice = ECA("choice")
	choice.con(values + ".input1", "input[0]")
	choice.con(values + ".input2", "input[1]")
	choice.con(plug, "selector")
	return choice + ".output"

def boolFromNormalisedPlug(plug):
	"""converts -1 1 signal to 0 1"""
	return plugCondition(plug, 0, operation="greaterThan")



class RampPlug(object):
	"""don't you love underscores and capital letters?
	called thus:
	ramp = RampPlug(myAnnoyingString)
	setAttr(ramp.point(0).value, 5.0)
	to be fair, if these are special-cased in maya, why not here"""

	class _Point(object):
		def __init__(self, root, index):
			self.root = root
			self.index = index

		@property
		def _base(self):
			return "{}[{}].{}_".format(
				self.root, self.index, self.root	)

		@property
		def value(self):
			return self._base + "FloatValue"
		@property
		def position(self):
			return self._base + "Position"
		@property
		def interpolation(self):
			return self._base + "Interp"

	def __init__(self, rootPlug):
		"""root is remapValue"""
		self.root = rootPlug
		self.points = {}

	def point(self, id):
		""":rtype : RampPlug._Point"""
		return self._Point(self.root, id)









