"""operations working on plugs as live operation components"""
import math
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from edRig import core, attr, ECA
#from edRig.node import ECA,PlugObject



def conOrSet(driver, driven):
	"""if EITHER is a static value, the opposite will be set as a plug"""
	attr.conOrSet(driver, driven)

def vecFromTo(startPlug, endPlug):
	"""get vector between two plugs"""
	vec = ECA("plusMinusAverage", name="vecFrom_{}_{}".format(
		startPlug, endPlug))
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
	"""multiplies all plugs - optimise to multDoubleLinear here if possible"""
	a = plugs[0]
	for i in plugs[1:]:
		#mult = ECA("multiplyDivide")
		mult = ECA("mdl")
		mult.conOrSet(a, mult + ".input1")
		mult.conOrSet(i, mult + ".input2")
		a = mult + ".output"
	return a

def plugCondition(val1, val2, operation="greaterThan"):
	"""compares conditions"""

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
	for i in [n for n in (min, max)if n]:
		cnd = ECA("condition")
		if i == min:
			cnd.set("operation", 2)
		conOrSet(plug, cnd + ".firstTerm")
		conOrSet(plug, cnd + ".colorIfFalse")
		conOrSet(i, cnd + ".colorIfTrue")
		conOrSet(i, cnd + ".secondTerm")
		plug = cnd + "outColor"
	return plug




def reversePlug(plug):
	"""returns 1 - plug"""
	rev = ECA("reverse", n=plug+"_reverse")
	attr.con(plug, rev+".inputX")
	return rev+".outputX"

def periodicSignalFromPlug(plug, period=1.0, amplitude=1.0,
                           profile="linear"):
	"""creates a repeating 0-1 signal from float plug using
	animCurve node"""
	profiles = ("linear", "sine", "cosine", "tan")
	curve = ECA("animCurveUU")

def invertMatrixPlug(plug):
	"""returns an inverse matrix plug"""

def blendFloatPlugs(plugList=None, blender=None, name="blendPlugs"):
	"""blends float plugs together"""
	blend = ECA("blendTwoAttr", n=name)
	#print "plugList {}".format(plugList)
	for i, val in enumerate(plugList):
		conOrSet(val, blend + ".input[{}]".format(i) )
	conOrSet(blender, blend + ".attributesBlender")
	return blend + ".output"

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


def trigPlug(plug, mode="sine", res=30, inputDegrees=True):
	"""remap a plug through a trigonometric function"""
	modes = {"sine" : math.sin,
	         "cosine" : math.cos,
	         "tangent" : math.tan,
	         "arcsine" : math.asin,
	         "arccosine" : math.acos,
	         "arctangent" : math.atan}

	crv = ECA("animCurveUU")
	func = modes[mode]
	fn = oma.MFnAnimCurve(crv.MObject)
	if mode in ("sine", "cosine", "tangent"):
		domain = 180.0
	else:		domain = 1.0

	step = domain / float(res)
	for i in range(res + 1):
		lookup = step * i
		value = func( math.radians(lookup) )
		fn.addKey(lookup, value)
	crv.set("preInfinity", 3)
	crv.set("postInfinity", 3)
	crv.con(plug, crv+".input")
	return plug + ".output"



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









