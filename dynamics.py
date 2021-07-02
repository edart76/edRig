"""lib for manipulating nDynamics nodes"""
from maya import cmds
from edRig.maya import core

from edRig.maya.core.node import EdNode, ECA
from edRig import attr


def makeSolverCell(name):
	""" create a pair of nodes to recycle values from previous frame
	currently only float value and only cmds
	this can be so much more beautiful """
	sink = cmds.createNode("network", n=name+"Solver_frameEnd")
	sinkObj = core.getMObject(sink)
	cmds.addAttr(sink, ln="currentFrameValue")
	cmds.addAttr(sink, dt="string", ln="frameSource")

	source = cmds.createNode("network", n=name+"Solver_frameStart")
	cmds.addAttr(source, ln="prevFrameValue")
	cmds.addAttr(source, dt="string", ln="frameSink")
	cmds.addAttr(source, ln="dt")
	cmds.connectAttr(source+".frameSink", sink+".frameSource")

	# used to update solvers live
	cmds.addAttr(source, dt="message", ln="updateSource")

	try:
		cmds.connectAttr("CodeNode.dt", source+".dt")
		cmds.connectAttr("CodeNode.solvers", source+".updateSource")
	except:
		pass

	return source, sink

def updateCell(source, sink):
	""" refit with openmaya to avoid direct graph updates """
	cmds.setAttr( source + ".prevFrameValue",
	              cmds.getAttr( sink + ".currentFrameValue"))



class NDynamicsElement(EdNode):
	"""what do all physics things need"""

	# def __init__(self, *args, **kwargs):
	# 	super(NDynamicsElement, self).__init__(*args, **kwargs)
	# 	self.nucleus = None

	def connectTime(self, timeSource=None):
		timeSource = timeSource or self.defaultTime
		self.con(timeSource, self+".currentTime")

	def connectInputShape(self, shapePlug, spacePlug=None):
		"""connect the target plug to shape input of element"""
		self.con(shapePlug, self.inputShapePlug)

	def connectRefShape(self, refPlug):
		self.con(refPlug, self.restShapePlug)

	def connectOutputShape(self, targetPlug, local=True):
		"""connects up baseShape as a start point, adds another
		shape as output
		does NOT set intermediate object :) """
		plug = self.outLocal if local else self.outWorld
		self.con(plug, targetPlug)
		pass

	def connectToNucleus(self, nucleus):
		"""connect up all the fiddly mel stuff"""
		# how many things are already connected?
		nucleus = Nucleus(nucleus)
		newIndex = cmds.getAttr(nucleus+".inputActive", size=True)
		# self.con(nucleus+".startFrame", self+".startFrame")
		self.con(nucleus+".outputObjects[{}]".format(newIndex),
		         self+".nextState")

		# self.con(self+".startState",
		#          nucleus+".inputActiveStart[{}]".format(newIndex))
		# self.con(self + ".currentState",
		#          nucleus + ".inputActive[{}]".format(newIndex))
		# only for active elements, not colliders

		attr.makeMutualConnection(nucleus, self, attrType="message",
		                          startName="elements", endName="nucleus")
		# no reason for a component to diverge from nucleus time
		# nucleus.con(nucleus + ".currentTime", self + ".currentTime")
		# DO NOT DO THIS passing time through a nucleus crashes without fail
		self.con(attr.getImmediatePast( nucleus + ".currentTime", wantPlug=True)[0],
		         self + ".currentTime" )
		# self.con( "time1.outTime", self + ".currentTime" )
		nucleus.kick()


	@property
	def nucleus(self):
		"""look up message connection"""
		return attr.getImmediatePast(self()+".nucleus")

	### specific polymorph plugs
	@property
	def inputShapePlug(self):
		pass
	@property
	def restShapePlug(self):
		pass
	@property
	def outLocal(self):
		pass

	@property
	def outputLocalShape(self):
		test = attr.getImmediateFuture(self.outLocal)
		if test: return EdNode(test[0])

	@property
	def nComponents(self):
		"""return dict of all connected nComponents, indexed by index """
		components = {}
		for i in attr.getImmediateFuture(self + ".nucleusId"):
			if cmds.nodeType(i) == "nComponent":
				index = attr.getAttr(i + ".componentIndices[0]")
				components[index] = i
				# vulnerable to multiple uninitialised nComponents
				# don't do that
		return components

	def connectNComponent(self, index=1, name=None):
		"""creates new nComponent and sets its index correctly
		reusing nComponents would be AMAZING in future """
		name = name or self.name + "_{}component".format(index)
		comp = NComponent.create(n=name)
		self.con(self + ".nucleusId", comp + ".objectId")
		comp.set("componentType", 2) # point, enum indices are weird
		comp.set("componentIndices[0]", index)
		return comp

	def getComponent(self, index=1):
		return self.nComponents.get(index) or \
		       self.connectNComponent(index)


class NHair(NDynamicsElement):
	"""wiggly willy
	points to hairSystem, not follicle"""

	defaultAttrs = { # by default clump taper actually affects collision
		"clumpWidthScale[0].clumpWidthScale_FloatValue" : 1,
		"clumpWidthScale[1].clumpWidthScale_FloatValue" : 1,
		"hairWidthScale[0].hairWidthScale_FloatValue" : 1,
		"hairWidthScale[1].hairWidthScale_FloatValue" : 1,

		"clumpWidth" : 0.0,
		"hairWidth" : 0.1, # ideally we shouldn't tangle with clumpWidth

	}

	_nodeType = "hairSystem"
	# follicle = None

	def __init__(self, *args, **kwargs):
		super(NHair, self).__init__(*args, **kwargs)
		self.hairSystem = None
		# self._follicle = None

	
	def connectToNucleus(self, nucleus):
		"""nHair unfortunately needs a separate follicle node
		to actually compute. sucks man."""
		super(NHair, self).connectToNucleus(nucleus)
		newIndex = cmds.getAttr(nucleus+".inputActive", size=True)
		self.con(nucleus + ".startFrame", self + ".startFrame")

		self.con(self+".startState",
		         nucleus+".inputActiveStart[{}]".format(newIndex))
		self.con(self + ".currentState",
		         nucleus + ".inputActive[{}]".format(newIndex))

		self.set( "active", 1)

	def connectInputShape(self, shapePlug, spacePlug=None):
		"""follicles are the worst"""
		if not self.follicle:
			self.makeFollicle()
			
		super(NHair, self).connectInputShape(shapePlug, spacePlug)

		if spacePlug:
			self.con(spacePlug, self.follicle+".startPositionMatrix")

	def connectRestShape(self, restPlug):
		super(NHair, self).connectRefShape(restPlug)
		self.follicle.set("restPose", 3)
		
	def makeFollicle(self):
		follicle = ECA("follicle", n="testFollicle")
		self.con(self+".outputHair[0]", follicle+".currentPosition")
		self.con(follicle+".outHair", self+".inputHair[0]")
		return follicle

	def setLockedPoints(self, mode):
		""" sets start, end, both or none to be locked in place """
		options = ["none", "start", "end", "both"]
		self.follicle.set("pointLock", options.index(mode))


	"""currently one follicle/hair system per dynamic curve - 
	later if this is too slow investigate multiple follicles per hair system"""

	@property
	def inputShapePlug(self):
		return self.follicle+".startPosition"
	@property
	def inputShape(self):
		return EdNode(attr.getImmediatePast(self.inputShapePlug)[0])
	@property
	def restShapePlug(self):
		return self.follicle+".restPosition"
	@property
	def outLocal(self):
		return self.follicle+".outCurve"

	@property
	def follicle(self):
		"""look up connected follicle node"""
		test = attr.getImmediateFuture(self+".outputHair[0]")
		if test: return EdNode(test[0])

	@property
	def follicles(self):
		"""maybe later"""

	@staticmethod
	def fromDynamicCurve(crv):
		"""returns an NHair object from a dynamic curve"""
		system = attr.getImmediatePast(crv + ".create")
		if system:
			return NHair(system[0])


class NComponent(NDynamicsElement):
	"""our handling of nComponents and nConstraints is actually very sparse
	at present - one nComponent will represent one point's interaction
	with one nConstraint
	once this works, investigate using extra indices of
	nComponent.componentIndices"""

	""" direct interaction with this class should actually be minimal """

class NConstraint(NDynamicsElement):
	"""for constraining dynamic elements together"""
	_nodeType = "dynamicConstraint"
	methods = ("weld", "spring", "rubberBand")
	connect = {"nearestPairs" : "nearest Pairs",
	           "withinMaxDistance" : "within Max Distance",
	           "componentOrder" : "component Order"} # not joking


	def constrainElements(self, elementA=None, indexA=0,
	                      elementB=None, indexB=0, elements=None,
	                      nucleus=None, timeSource=None,
	                      method="weld", connect="componentOrder",
	                      ):
		"""main method for constraining elements,
		through any number of methods
		should itself be a class method
		this currently incurs heavy node duplication
		:param elementA : NDynamicsElement,
		:param elements : list of tuples [ (NDynamicsElement, index), ]
		"""
		compA = elementA.getComponent(index=indexA)
		compB = elementB.getComponent(index=indexB)
		# getComponent sets indices properly

		self.set("constraintMethod", method)
		self.set("connectionMethod", self.connect[connect])

		self.con(compA + ".outComponent", self + ".componentIds[0]")
		self.con(compB + ".outComponent", self + ".componentIds[1]")

		self.set("enable", 1)
		self.set("maxIterations", 1) # has appreciable impact on performance
		# increment if necessary

		# 3.52ms


		if nucleus : self.connectToNucleus(nucleus)
		self.connectTime(timeSource=timeSource)

	def connectToNucleus(self, nucleus):
		""" special cased cos constraints are weird """
		nucleus = Nucleus(nucleus)

		attr.makeMutualConnection(nucleus, self, attrType="message",
		                          startName="elements", endName="nucleus")

		self.con(attr.getImmediatePast( nucleus + ".currentTime", wantPlug=True)[0],
		         self + ".currentTime" )

		vacant = attr.getNextAvailableIndex(nucleus + ".inputCurrent")
		print(("vacant {}".format(vacant)))
		self.con("evalCurrent[0]", "{}.inputCurrent[{}]".format(
			nucleus, vacant))
		self.con("evalStart[0]", "{}.inputStart[{}]".format(
			nucleus, vacant	))

		nucleus.kick()



class NCollider(NDynamicsElement):
	"""collision meshes"""
	_nodeType = "nRigid"

	@property
	def inputShapePlug(self):
		""" collider shape input """
		return self() + ".inputMesh"

	def connectToNucleus(self, nucleus):
		super(NCollider, self).connectToNucleus(nucleus)
		self.con(nucleus + ".startFrame", self + ".startFrame")

		index = cmds.getAttr(nucleus+".inputPassive", size=True)
		self.con(self+".currentState",
		         nucleus+".inputPassive[{}]".format(index))
		self.con(self + ".startState",
		         nucleus + ".inputPassiveStart[{}]".format(index))

class NParticle(NDynamicsElement):
	"""far more simple than others"""

	def connectToNucleus(self, nucleus):
		"""nHair unfortunately needs a separate follicle node
		to actually compute. sucks man."""
		#super(NParticle, self).connectToNucleus(nucleus)
		newIndex = cmds.getAttr(nucleus+".inputActive", size=True)

		self.con(self+".startState",
		         nucleus+".inputActiveStart[{}]".format(newIndex))
		self.con(self + ".currentState",
		         nucleus + ".inputActive[{}]".format(newIndex))
		self.set( "active", 1)

class Nucleus(EdNode):
	"""specific capacities for working with nucleus nodes"""

	@classmethod
	def create(cls, name="newNucleus", timeInput="time1.outTime"):
		# make new nucleus, disable it by default when scrubbing
		node = super(Nucleus, cls).create(name)
		#node.con(timeInput, node+".currentTime")
		# node.con(plug.reversePlug("CodeNode.isScrubbing"),
		#          node+".enable")
		# scene.SceneGlobals.addNucleus(node)

		# add clear interface for time input to nucleus
		# all dynamics elements will then draw from this
		timeInterface = ECA("choice", n=name+"_timeInterface")
		timeInterface.con(timeInput, timeInterface + ".input[0]")
		timeInterface.con("output", node+".currentTime")

		return cls(node)

	@staticmethod
	def getNucleus(search=""):
		"""when you just need to make stuff jiggle"""
		result = cmds.ls(search) or cmds.ls(type="nucleus")
		return result

	@property
	def timeInput(self):
		"""return driving plug of T I M E """
		return attr.getImmediatePast(self() + ".currentTime", wantPlug=True)

	def addElement(self, elementNode):
		"""adds target nDynamics node to solver
		not really much point in trying to hack this apart, it's pretty closed"""

	def addCollider(self, mesh, name):
		""" adds a new collider to nucleus from shape node """
		shape = EdNode(mesh).shape
		collider = NCollider.create(name=name+"_rigid")
		collider.connectInputShape(shape.outLocal)
		collider.connectToNucleus( self() )
		collider.transform.name = name + "_transform"

		# update collider
		self.kick()
		collider.set("thickness", 0.1)
		self.kick()
		return collider

	def kick(self):
		"""disconnects time and jitters current time a bit -
		latest attempt to avoid rabid crashing"""
		source = attr.getImmediatePast( self + ".currentTime", wantPlug=True )[0]
		# print "source {}".format(source)
		#attr.breakConnections(self + ".currentTime")
		current = cmds.currentTime(q=True)
		start = self.get("startFrame")
		cmds.currentTime(start)

		#self.con(source, self +
		#cmds.dgdirty(a=True)
		cmds.currentTime( start + 1 )
		cmds.currentTime( start + 2 )

		cmds.play(state=True, forward=True)
		# cmds.pause(sec=5)
		# time.sleep(5)
		cmds.play(state=False)
		# cmds.pause(sec=5)
		# time.sleep(2)
		cmds.currentTime( start )


def attachDynamicCurves():
	pass

def weldCVs(shapeA):
	pass

def makeCurveDynamic(targetCurve,
                     live=True, timeInput="time1.outTime",
                     nucleus=None, tidyGrp=None,
                     name="", staticRest=True):
	"""the better version"""
	nucleus = nucleus or Nucleus.create(timeInput=timeInput)
	tidyGrp = tidyGrp or ECA("transform", n="dynamicsGrp")

	targetCurve = EdNode(targetCurve).shape
	if not live:
		targetCurve = targetCurve.copy(name=name+"_static", children=True)

	system = NHair.create(n=name+"_system")
	system.connectToNucleus(nucleus)

	outCrv = targetCurve.copy(name+"_output", children=True)
	system.connectInputShape( shapePlug=targetCurve.shape.outLocal)
	system.con( system.outLocal, outCrv.shape.inShape)
	return system

def constrainClosestPoints(systemA, systemB):
	"""creates weld constraint between nearest CVs"""
	print("constraining")



def dampPlug(plug, nucleus=None, goalPlug=None):
	""" pass a plug's value through a dynamic particle,
	allowing inline insertion of delay, damping etc """
	""" use in conjunction with plug limits to eliminate overshoot"""


