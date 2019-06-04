"""lib for manipulating nDynamics nodes"""
from maya import cmds

from edRig.node import AbsoluteNode, ECA
from edRig import attr, naming, plug, scene

class NDynamicsComponent(AbsoluteNode):
	"""what do all physics things need"""

	def connectTime(self, timeSource):
		self.con(timeSource, self+".currentTime")

	def connectToShape(self, baseShape, local=True):
		"""connects up baseShape as a start point, adds another
		shape as output
		does NOT set intermediate object :) """
		outputShape = AbsoluteNode(baseShape).getShapeLayer(local)


	def connectToNucleus(self, nucleus):
		"""connect up all the fiddly mel stuff"""
		# how many things are already connected?
		newIndex = cmds.getAttr(nucleus+".inputActive", size=True)
		self.con(nucleus+".startFrame", self+".startFrame")
		self.con(nucleus+".outputObjects[{}]".format(newIndex),
		         self+".nextState")

		self.con(self+".startState",
		         nucleus+".inputActiveStart[{}]".format(newIndex))
		self.con(self + ".startState",
		         nucleus + ".inputActiveStart[{}]".format(newIndex))




class Nucleus(AbsoluteNode):
	"""specific capacities for working with nucleus nodes"""

	@staticmethod
	def create(name="newNucleus", timeInput="time1.outTime"):
		# make new nucleus, disable it by default when scrubbing
		node = Nucleus(ECA("nucleus", n=name).node)
		node.con("time1.outTime", node+".currentTime")
		node.con(plug.reversePlug("CodeNode.isScrubbing"),
		         node+".enable")

		scene.SceneGlobals.addNucleus(node)

		return node

	def addElement(self, elementNode):
		"""adds target nDynamics node to solver
		not really much point in trying to hack this apart, it's pretty closed"""


