"""low-level library for parsing colour tuples
and generally improving user experience in a maya scene"""
from maya import cmds
from edRig import attr
import math

colourPresets = {
	"red" : (256, 0, 0),
	"blue" : (0, 0, 256),
	"guides" : (256, 256, 0), # neon unpleasant warning yellow

}

def getColour(colour=None, normalise=False):
	"""if i see a default colour control i'm gonna flip"""
	if isinstance(colour, basestring):
		colour = colourPresets.get(colour) or (60,60, 256)
	elif isinstance(colour, tuple):
		colour = list(colour)

	if normalise:
		for i, val in enumerate(colour):
			colour[i] = val / 256.0
	return colour

def setColour(target, colour=(40, 200, 40)):
	colour = getColour(colour)
	attr.setAttr(target + ".overrideEnabled", 1)
	attr.setAttr(target + ".overrideRGBColors", 1)
	attr.setAttr(target + ".overrideColorRGB", colour)

def removeColour(target):
	attr.setAttr(target + ".overrideEnabled", 0)

class Colour(object):
	"""people laugh at this but it's so important
	to work with beautiful tools"""

	def getBinaryComplement(self):
		pass
	def getTertiaryComplement(self, a=True, b=False):
		pass

def getUsableScale(boundingObject, factor=1.0):
	"""scales joint to be usable based on a certain bounding box"""
	bounds = cmds.exactWorldBoundingBox(boundingObject)
	size = math.sqrt( pow( bounds[3] - bounds[0], 2) +
	                  pow(bounds[4] - bounds[1], 2) +
	                  pow(bounds[5] - bounds[2], 2) )
	return size * factor