"""low-level library for parsing colour tuples"""
from maya import cmds
from edRig import attr

colourPresets = {
	"red" : (256, 0, 0),
	"blue" : (0, 256, 0),
}

def getColour(colour=(), normalise=False):
	"""if i see a default colour control i'm gonna flip"""
	if isinstance(colour, basestring):
		colour = colourPresets.get(colour) or (60,60, 256)
	if normalise:
		for i, val in enumerate(colour):
			colour[i] = val / 256.0
	return colour

def setColour(target, colour):
	attr.setAttr(target + ".overrideEnabled", 1)
	attr.setAttr(target + ".overrideRGBColors", 1)
	attr.setAttr(target + ".overrideColorRGB", colour)

class Colour(object):
	"""people laugh at this but it's so important
	to work with beautiful tools"""

	def getBinaryComplement(self):
		pass
	def getTertiaryComplement(self, a=True, b=False):
		pass


