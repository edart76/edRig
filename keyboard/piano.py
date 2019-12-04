
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


"""

def makeOctave():
	""" makes guides for a single octave of keys """

def makeKey(endLoc, index=None,
            numberKeys=None, keyWidth=None):
	""" set up pivot mechanism for individual key"""
	# first position key on keyboard
	midLoc = ECA("locator", name="key{}_mid".format(index))
	xPlug = plug.multPlugs(index, keyWidth)
	midLoc.con(xPlug, midLoc + ".translateX")



	pass

def makeRollTemplate( depressTransform ):
	"""
	depressTransform : shows depress position for key relative to pivot,
	including translation for roll"""
	""" we should only declare this twice for a full piano,
	for black and white keys """

	remap = RemapValue.create(n="depressTranslate")
	






base = ECA("transform", n="base")
mainEnd = ECA("locator", n="keyboardEnd").transform
mainEnd.set("translateX", 10)

nKeys = 88
keys = []

#divide tx by nkeys
dx = plug.dividePlug(mainEnd + ".translateX", nKeys)

for i in range(nKeys):
	makeKey(mainEnd, index=i, numberKeys=nKeys, keyWidth=dx)
