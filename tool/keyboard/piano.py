
from maya import cmds
import maya.api.OpenMaya as om

from edRig import ECA, AbsoluteNode, plug, attr
from edRig.node import RemapValue


""" basic autorig for setting up the main key press system,
and providing hooks for whatever mechanism goes on the back of it

all locators placed at key midpoints

baseGrp = common coordinate space, placed at first A
startLoc = locked at x=0
endLoc = placed at midpoint of final key
octaveEndLoc

for limits, and actual pivot mechanism, use glorified driven key

depression - 0-10 range, with 10 specifying maximum attributes
no remapping yet, keep everything linear to interpretation by system

fake the restituting weight with a simple spring particle,
we don't need to simulate full mass and collision

pivotLoc - output of roll system, drives key geometry

similarly fake the roll with a remap value for the translation,
it doesn't have to be much to sell it


we assume a keyboard with keys arrayed in X, with key tips facing to Z

"""

def makeOctave(pos, width):
	""" makes guides for a single octave of keys
	"""

	"""given a set of int key spacings, for white keys,
	find spacings for black keys"""

	tripleOffset = 0.5
	doubleOffset = 0.5

	tripleExpansion = 0.1
	doubleExpansion = 0.05

	""" positions could start from whatever, but spacings 
	will start from C"""

	Db = pos[2] + (width / 2.0 + width * doubleExpansion) * -1
	Eb = pos[2] + (width / 2.0 + width * doubleExpansion)

	Ab = pos[5] + width * 0.5 # Ab always central
	Gb = Ab - width - width * tripleExpansion
	Bb = Ab + width + width * tripleExpansion





def makeKey(endLoc, index=None,
            numberKeys=None, keyWidth=None,
            ):
	""" set up pivot mechanism for individual key
	midLoc to be placed in the lateral midpoint of each key
	"""
	# first position key on keyboard
	midLoc = ECA("locator", name="key{}_mid".format(index))
	xPlug = plug.multPlugs(index, keyWidth)
	midLoc.con(xPlug, midLoc + ".translateX")

	data = {
		"midLoc",
	}
	pass

def makeRoll(
		depressPlug=None,
		template=False,
        pose=None, remap=None, origin=None,
		topSurfaceTemplate=None, keyEndTemplate=None,
        index=None):
	"""
	depressTransform : shows depress position for key relative to pivot,
	including translation for roll
	depressPlug : key's depression value

	if template, will set up main pose and remap
	if not, will inherit from those supplied

	pose : master pose locator
	origin : specific key origin locator

	"""
	""" we should only declare this twice for a full piano,
	for black and white keys """


	# just put this here for now
	topSurface = ECA("locator", n="topSurface")
	# to be placed on top suface of key, where finger would touch
	keyEnd = ECA("locator", n="keyEnd")
	# to be placed at end of key, where hammer interacts

	if template:
		remap = RemapValue.create(n="depressTranslate")
		origin = ECA("locator", name="rollOrigin").transform
		pose = ECA("locator", name="depressPose").transform
		pose.parentTo(origin)
		remap.con(pose + ".translateZ", remap.ramp.point(1).value)


	else:
		remap = remap.getRampInstance(name="instance{}".format(index))

		for i in "ZY":
			keyEnd.con( keyEndTemplate + ".translate" + i,
			            keyEnd + ".translate" + i)
			topSurface.con(topSurfaceTemplate + ".translate" + i,
			            topSurface + ".translate" + i)
			pass

	topSurface.parentTo(origin)
	keyEnd.parentTo(origin)

	output = ECA("locator", name="rollOutput").transform
	output.parentTo(origin)

	# blend rotation - we only care about one axis
	rotX = plug.blendFloatPlugs([(0, 0, 0), pose + ".rotateX"],
	                            depressPlug)
	remap.con(depressPlug, remap + ".inputValue")

	output.con(remap + ".outValue", output + ".translateZ")
	output.con(rotX, output + ".rotateX")
	return {
		"remap" : remap,
		"output" : output,
		"pose" : pose,
		"topSurface" : topSurface,
		"keyEnd" : keyEnd,
	}


def makeDepressionAttrs(name="piano", nKeys=88):
	"""create network nodes with external inputs, control inputs,
	final output values between 0-1
	and and addition nodes to blend them together
	no multiplication, we assume that to be within purview of controls"""

	output = ECA("network", n=name+"_activations")


	return { "outputNode" : output,
	         "attrs" : [ output + ".activation[{}]".format(i)
	                     for i in range(nKeys) ] }


def makeKeyboard():
	""" tragically this does not support non-linear keyboards
	just don't affront the natural order and you'll be fine """

	base = ECA("transform", n="base")
	mainEnd = ECA("locator", n="keyboardEnd").transform
	mainEnd.parentTo(base)
	mainEnd.set("translateX", 10)

	nKeys = 88
	keys = []
	depressionData = makeDepressionAttrs(nKeys=nKeys)

	# make templates first for black and white, then instance out
	# smaller rigs to them
	blackTemplateLoc = ECA("locator", n="blackTemplateRoot").transform
	active = blackTemplateLoc.addAttr(
		attrName="templateActivation", min=0, max=1)
	blackKeyData = makeRoll(depressPlug=active, template=True)

	whiteTemplateLoc = ECA("locator", n="whiteTemplateRoot").transform
	active = whiteTemplateLoc.addAttr(
		attrName="templateActivation", min=0, max=1)
	whiteKeyData = makeRoll(depressPlug=active, template=True)

	#divide tx by nkeys
	dx = plug.dividePlug(mainEnd + ".translateX", nKeys)

	for i in range(nKeys):
		data = makeKey(mainEnd, index=i, numberKeys=nKeys, keyWidth=dx)
