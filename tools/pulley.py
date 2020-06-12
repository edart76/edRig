""" create live networks of connected wheels and cables under tension """
from edRig import cmds, om

from edRig import AbsoluteNode, ECA, attr, plug, transform, curve


class PulleySystem(object):
	""" trash name
	class for connected systems of lines under tension,
	threaded around wheels
	"""
	def __init__(self, name="pulleySystem"):
		self.wheels = []

	def addWheel(self, name="newWheel"):
		""" assumed to be added in order """
		wheel = Wheel(name=name)
		self.wheels.append(wheel)

	def orderWheels(self):
		nWheels = len(self.wheels)
		for i, val in enumerate(self.wheels):
			nextIndex = (i + 1) % nWheels
			prevIndex = i - 1
			print("index {} next {} prev {}".format(i, nextIndex, prevIndex))
			val.next = self.wheels[ nextIndex ]
			val.prev = self.wheels[ prevIndex ]

	def build(self):
		self.orderWheels()
		for i in self.wheels:
			i.build()

	def link(self):
		for i in self.wheels:
			i.link()


class Wheel(object):
	""" individual wheel in pulley system
	search "homothetic circles" and it should point
	the right way"""

	def __init__(self, basePoint=None, name="wheel"):
		""":type basePoint : AbsoluteNode
		:param basePoint : AbsoluteNode
		central point from which main vector will compute

		each wheel deals with itself and the relationship to its next

		"""
		self.point = basePoint
		self.name = name
		self.next = None # next wheel
		self.prev = None # previous wheel

		self.outputNext = None
		self.outputPrev = None

		self.group = None
		self.pin = None

		self.curves = []

		# interface parametres
		self.pos = None
		self.radius = None

		pass

	def build(self):

		""" creates base node network """

		# main group for everything
		self.group = ECA("transform", n=self.name + "_main")

		# main pin input
		self.pin = ECA("locator", n=self.name + "pointInput")
		self.pin.addAttr(attrName="radius", min=0, dv=0.3)
		self.pin.con( self.pin + ".scaleX", self.pin + ".radius") # for now
		self.pin.parentTo(self.group)



		# radius flipping setup
		self.pin.addAttr(attrName="flip", attrType="bool")
		choice = ECA("choice", n=self.name + "radiusSwitch")
		flipMdl = ECA("multDoubleLinear", n=self.name + "radiusFlip")
		flipMdl.set("input1", 1)
		flipMdl.set("input2", -1)
		choice.con(flipMdl + ".input1", "input[0]")
		choice.con(flipMdl + ".input2", "input[1]")
		choice.con(self.pin + ".flip", "selector")
		# 1 / -1 used in other places in setup
		self.radius = plug.multPlugs(self.pin + ".radius", choice + ".output")


		# base orient node to track cross product between input vectors
		orient = ECA("transform", n=self.name + "vectorOrient")
		orient.parentTo(self.pin)
		self.orient = orient

		# arc midpoint
		self.midpoint = ECA("locator", n=self.name + "arcMidpoint")
		self.midpoint.con(self.radius, "translateX")
		self.midpoint.parentTo(self.orient)

		# proxy and temp control, canted rotation not implemented yet
		self.proxy = self.makeProxy()
		self.proxy.parentTo(orient)

		# curve setup
		self.arc = ECA("makeThreePointCircularArc", n=self.name + "Arc")

		self.pos = self.pin + ".translate"


	def link(self):
		"""
		connects wheel to pulley system
		before and after can be the same wheel
		for now we only support two linked wheels - more can be achieved
		more easily with hacks if necessary
		there are probably inefficiencies in here among the linear stuff,
		but at least it's all pretty parallel
		"""

		# main vector inputs
		# to centres of adjacent wheels
		vecToPrev = plug.vecFromTo(self.pin + ".translate",
		                           self.prev.pin + ".translate")
		vecToNext = plug.vecFromTo(self.pin + ".translate",
		                           self.next.pin + ".translate")
		vecWithout = plug.vecFromTo(self.prev.pin + ".translate",
		                            self.next.pin + ".translate")

		# normal between points
		inNormal = plug.crossProduct(vecToPrev, vecToNext, normalise=True)
		vecToPrevN = plug.normalisePlug(vecToPrev)
		vecToNextN = plug.normalisePlug(vecToNext)

		prevOrientMat = transform.buildTangentMatrix(
			(0, 0, 0), vecToPrevN, inNormal)
		nextOrientMat = transform.buildTangentMatrix(
			(0, 0, 0), vecToNextN, inNormal)

		transform.decomposeMatrixPlug(prevOrientMat, target=self.orient )

		# draw lines to track which wheels are connected
		nextLine = curve.curveFromCvPlugs([self.next.pos,
		                                  self.pin + ".translate"], useApi=0,
		                                  name=self.name + ".prevLine")

		# find homothetic centres
		""" equation goes like this
		centre = (r2 / (r1 + r2) ) * pos1 + (r1 / (r1 + r2) ) * pos2
		angles of tangents are common to both discs
		"""

		totalRadii = plug.addLinearPlugs(self.radius, self.next.radius)
		r2OverTotal = plug.dividePlug(self.next.radius, totalRadii)
		lhs = plug.multPlugs(r2OverTotal, self.pos)
		r1OverTotal = plug.dividePlug(self.radius, totalRadii)
		rhs = plug.multPlugs(r1OverTotal, self.next.pos)
		centre = plug.addPlugs(lhs, rhs)

		# marker for now
		marker = ECA("locator", n=self.name + "hCentreMarker")
		marker.con(centre, "translate")





	def makeProxy(self):
		""" create a polygon cylinder representing
		wheel orientation and size
		move to dedicated proxy/polygon lib sometime maybe """

		proxy = AbsoluteNode( cmds.polyCylinder(
			axis=[0,1,0], ch=0, n=self.name + "_proxy",
		height=0.1, radius=0.4)[0] )

		return proxy








"""
wheel dag structure

main group
	vectorOrient # point constrained to main point, oriented to cross product
		offsetOrient # allows rotation around common axis for canted wheels
		proxy # same as above, works as control for now as well
			


"""




