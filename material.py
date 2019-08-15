from maya import cmds
import maya.api.OpenMaya as om

from edRig import scene, core, log, beauty
from edRig.node import AbsoluteNode, ECA

class Material(AbsoluteNode):
	"""base class for materials idk"""

	outColourPlug = "outColor"
	transparencyPlug = "outTransparency"

	@property
	def shadingGroup(self):
		"""returns connected shading group"""
		return AbsoluteNode(getSGfromShader(self()))

	def applyTo(self, target):
		applyMaterialNode(self(), target)

	@property
	def outColour(self):
		return self() + "." + self.outColourPlug

	@property
	def transparency(self):
		return self() + "." + self.transparencyPlug

	def setColour(self, colour):
		colour = beauty.getColour(colour, normalise=True)
		print "colour {}".format(colour)
		self.set(self.outColour, colour)

	def setTransparency(self, colour):
		colour = beauty.getColour(colour, normalise=True)
		self.set(self.transparency, colour)


class SurfaceShader(Material):
	pass

def getUiShader(colour=(0,0,80)):
	"""returns a transparency shader for use on surface controls"""
	shader = SurfaceShader.create(name="rigShader")
	colour = beauty.getColour(colour)
	shader.setColour(colour)
	"""all very temp for now"""
	return shader


class LayeredShader(Material):
	"""AAAAAAAAAAAAAAAAAA"""

# i have yet to go anywhere arnold
# i anticipate a fun time

class AiStandardSurface(Material):
	"""bring it"""



def applyMaterialNode(matNode, target):
	"""applies material represented by node to target dag"""
	sg = getSGfromShader(matNode)
	if not sg:
		log("sg not found for {}".format(matNode))
	cmds.sets([target], e=True, forceElement=sg)
	

def getSGfromShader(shader):
	if cmds.objExists(shader):
		sgq = cmds.listConnections(shader, d=True, et=True, t='shadingEngine')
		if sgq:
			return sgq[0]

	return None


