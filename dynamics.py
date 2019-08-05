"""lib for manipulating nDynamics nodes"""
from maya import cmds

from edRig.node import AbsoluteNode, ECA
from edRig import attr, naming, plug, scene, callback, core

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
	cmds.setAttr( source + ".prevFrameValue",
	              cmds.getAttr( sink + ".currentFrameValue"))



class NDynamicsElement(AbsoluteNode):
	"""what do all physics things need"""

	# def __init__(self, *args, **kwargs):
	# 	super(NDynamicsElement, self).__init__(*args, **kwargs)
	# 	self.nucleus = None

	def connectTime(self, timeSource):
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
		newIndex = cmds.getAttr(nucleus+".inputActive", size=True)
		self.con(nucleus+".startFrame", self+".startFrame")
		self.con(nucleus+".outputObjects[{}]".format(newIndex),
		         self+".nextState")

		self.con(self+".startState",
		         nucleus+".inputActiveStart[{}]".format(newIndex))
		self.con(self + ".startState",
		         nucleus + ".inputActiveStart[{}]".format(newIndex))

		attr.makeMutualConnection(nucleus, self, attrType="message",
		                          startName="elements", endName="nucleus")

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



class NHair(NDynamicsElement):
	"""wiggly willy
	points to hairSystem, not follicle"""

	nodeType = "hairSystem"
	follicle = None

	def __init__(self, *args, **kwargs):
		super(NHair, self).__init__(*args, **kwargs)
		self.hairSystem = None

	
	def connectToNucleus(self, nucleus):
		"""nHair unfortunately needs a separate follicle node
		to actually compute. sucks man."""
		super(NHair, self).connectToNucleus(nucleus)

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

	"""currently one follicle/hair system per dynamic curve - 
	later if this is too slow investigate multiple follicles per hair system"""

	@property
	def inputShapePlug(self):
		return self.follicle+".startPosition"
	@property
	def restShapePlug(self):
		return self.follicle+".restPosition"
	@property
	def outLocal(self):
		return self.follicle+".outCurve"

	@property
	def follicle(self):
		"""look up connected follicle node"""
		return AbsoluteNode(attr.getImmediateFuture(self+".outputHair[0]")[0])

	@property
	def follicles(self):
		"""maybe later"""

"""with all the extra complexity and overhead from follicle, it might actually be better to
set up a chain of connected nParticles"""

class NCollider(NDynamicsElement):
	"""collision meshes"""

	def connectToNucleus(self, nucleus):
		self.con(nucleus+".startFrame", self+".startFrame")

		index = cmds.getAttr(nucleus+".inputPassive", size=True)
		self.con(self+".currentState",
		         nucleus+".inputPassive[{}]".format(index))
		self.con(self + ".startState",
		         nucleus + ".inputPassiveStart[{}]".format(index))

class NParticle(NDynamicsElement):
	"""far more simple than others"""


class Nucleus(AbsoluteNode):
	"""specific capacities for working with nucleus nodes"""

	@classmethod
	def create(cls, name="newNucleus", timeInput="time1.outTime"):
		# make new nucleus, disable it by default when scrubbing
		node = super(Nucleus, cls).create(name)
		node.con(timeInput, node+".currentTime")
		# node.con(plug.reversePlug("CodeNode.isScrubbing"),
		#          node+".enable")
		# scene.SceneGlobals.addNucleus(node)
		return node

	@staticmethod
	def getNucleus(search=""):
		"""when you just need to make stuff jiggle"""
		result = cmds.ls(search) or cmds.ls(type="nucleus")
		return result

	def addElement(self, elementNode):
		"""adds target nDynamics node to solver
		not really much point in trying to hack this apart, it's pretty closed"""

def attachDynamicCurves():
	pass

def weldCVs(shapeA):
	pass

def makeCurveDynamic(targetCurve,
                     live=True, timeInput="time1.outTime",
                     nucleus=None, tidyGrp=None,
                     name=""):
	"""the better version"""
	nucleus = nucleus or Nucleus.create(timeInput=timeInput)
	tidyGrp = tidyGrp or ECA("transform", n="dynamicsGrp")

	targetCurve = AbsoluteNode(targetCurve).shape
	if not live:
		targetCurve = targetCurve.copy(name=name+"_static")

	system = NHair.create(n=name+"_system")
	system.connectToNucleus(nucleus)
	return system






