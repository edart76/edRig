""" create live networks of connected wheels and cables under tension """
from edRig import cmds, om

from edRig import AbsoluteNode, ECA, attr, plug, transform


class Wheel(object):
	""" individual wheel in pulley system """

	def __init__(self, basePoint=None, name="wheel"):
		""":type basePoint : AbsoluteNode
		:param basePoint : AbsoluteNode
		central point from which main vector will compute
		"""
		self.point = basePoint
		self.name = name
		pass

	def setup(self):
		""" creates base node network """

		# main group for everything
		self.group = ECA("transform", n=self.name + "_main")

		# main pin input
		self.pin = ECA("transform", n=self.name + "pointInput")
		self.pin.parentTo(self.group)

		# base orient node to track cross product between input vectors
		orient = ECA("transform", n="vectorOrient")
		orient.parentTo(self.pin)

		# proxy and temp control, canted rotation not implemented yet
		self.proxy = self.makeProxy()
		self.proxy.parentTo(orient)

		# main vector inputs
		vecAIn = ECA("transform", name="vecA_input")
		vecBIn = ECA("transform", name="vecB_input")
		vecAIn.set("translateX", 1)
		vecBIn.set("translateY", 1)
		for i in vecAIn, vecBIn:
			i.parentTo(self.pin)
			# positions are in pin-space, can use translation directly
			i.addAttr("radius") # radius of each neighbour wheel

		# vector setup
		self.vectorSetup(main=vecAIn, aux=vecBIn)

		# connect everything
		transform.decomposeMatrixPlug(self.point.outWorld, self.pin, r=0, s=0)


	def vectorSetup(self, main=None, aux=None):
		""" creates all the vector homothetic stuff
		main is the axis that all the machinery will align to, our angular
		zero value
		this may not be a good idea, or it may not
		:param main : AbsoluteNode
		:param aux : AbsoluteNode"""
		vectorGrp = ECA("transform", n="vectorAligned")
		transform.aimToVector(vectorGrp, main + ".translate")




	def link(self, before=None, after=None):
		""" :param before : Wheel
		:param after : Wheel
		connects wheel to pulley system
		before and after can be the same wheel
		for now we only support two linked wheels - more can be achieved
		more easily with hacks if necessary
		"""

	def makeProxy(self):
		""" create a polygon cylinder representing
		wheel orientation and size
		move to dedicated proxy/polygon lib sometime maybe """

		proxy = AbsoluteNode( cmds.polyCylinder(
			axis=[0,1,0], ch=0, n=self.name + "_proxy")[0] )
		proxy.addAttr("radius", min=0)
		proxy.con("radius", "scaleX")
		proxy.con("radius", "scaleZ")

		return proxy








"""
wheel dag structure

main group
	vectorOrient # point constrained to main point, oriented to cross product
		offsetOrient # allows rotation around common axis for canted wheels
		proxy # same as above, works as control for now as well
			


"""




