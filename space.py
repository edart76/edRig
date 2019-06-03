""" module for space switches"""

from edRig import AbsoluteNode, ECA, transform, attr, \
	callback, node, naming

from maya import cmds
import maya.api.OpenMaya as om

class SpaceSwitch(object):
	"""base class for space switches affecting transforms"""

	def __init__(self,
	             name="testSpaceSwitch",
	             spaceDrivers=None, spacePlugs=None,
	             blendDegree=2):
		"""depends on mode wanted"""
		self.mainChoice = None
		self.control = None
		self.blend = None
		self.degree = blendDegree
		self.name = name
		self.makeInternals()

	def makeInternals(self):
		"""create the backend node network for a spaceswitch"""

		blend = ECA("wtAddMatrix", n=self.name + "_spaceBlend ")
		for i in range(self.degree):
			choice = ECA("choice", n=self.name + "_choice{}".format(
				naming.string.uppercase[i]))
			attr.con(choice+".output",
			         blend + ".wtMatrix[{}].matrixIn".format(i))







	@property
	def drivenTransforms(self):
		"""return all the spaceGroups which are directly driven
		list by message connections, returning (transform, holdMatrix)"""

	@property
	def stableTransforms(self):
		"""return all transforms which are stabilised during user
		interaction with spaceswitch
		list by message attribute"""


	def stabiliseTransform(self, target):
		"""add target transform to spaceswitch stabilise list
		this necessarily must always be done in world space - for now"""

		hold = ECA("holdMatrix", n=target+"_storeMatrix")
		attr.con(target+".worldMatrix[0]", hold+".inMatrix")


"""
different kernels available 

- straight space snapping. the simplest.

 - n-D space choice using normalised weights. compatible with stabilisation
 more difficult to animate
 
 - 2x n-D space choice feeding into 0-1 blend. theoretically this is just a 
 special case subset of second option, with more clean UI, but i would rather
 treat it separately

every driven transform needs to keep its starting offset as a matrix multiplied
after switch process


"""