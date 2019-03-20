from edRig import core, control, attrio
import edRig.curve as libcurve
import edRig.transform as libtf
from edRig.layers import base
from maya import cmds
import maya.api.OpenMaya as om
from collections import OrderedDict
from edRig.core import AbsoluteNode, invokeNode, shortUUID, randomWord
from edRig.tilepile.ops.op import Op
from edRig.layers import Env


class Datatype(object):
	"""base class for datatypes to be passed through layers"""
	D = "nD"
	defaultNode = "default basic node for transmitting data"
	defaultPlug = "matrix, maybe?"
	name = "defaultName"
	# sick of passing this through inits, find a way to gather
	# variables from scope at time of instantiation
	defaultOutPlugs = {
		"0D" : ".matrix",
		"1D" : ".local",
		"2D" : ".outMesh"
	}
	defaultInPlugs = {

	}


	def __init__(self, node=None, ):
		#print "datatype instantiated"
		self.MObject = None
		self._name = None
		self.stageName = "base"
		# self.offsetGrp = AbsoluteNode(offsetGrp) or self.ECA("transform", name=self.D+"_offset")
		self.active = AbsoluteNode(node) if node else None
		insert = cmds.listRelatives(node, parent=True)
		self.spaceGrp = self.ECA("transform", "data"+self.__class__.__name__+self.name)
		#cmds.parent(self.active, self.spaceGrp)

		if insert:
			print "insert is {}".format(insert)
			#cmds.parent(self.spaceGrp, AbsoluteNode(insert[0]))
		self.activePlug = None

	@property
	def name(self):
		return self._name or "blank"

	@name.setter
	def name(self, val):
		self._name = val

	# @property
	# def spaceGrp(self):
	# 	return invokeNode("data"+self.__class__.__name__, "transform")


	def __repr__(self):
		return self.active

	def __str__(self):
		return self.active

	def ECN(self, type, name, *args):
		node = core.ECN(type, name, *args)
		Op.addTag(node, "datatype", self.__class__.__name__)
		return node

	def ECA(self, type, name, *args):
		node = core.ECA(type, name, *args)
		Op.addTag(node, "datatype", self.__class__.__name__)
		return node

	def updateData(self, data=None, joints=True, curves=True):
		"""explicitly define the data to be updated - could be inputs,
		outputs etc. example would be (from the parent op):
			self.saveData["jointcurve"] = {}
		and then populate that with the information from the datatype object
		NOPE only save out data from ops.
		saving this object as data is cool though.
		"""
		pass


	# transfer ownership: copy class, then change parentOp

	def newStage(self, stageName):
		"""way for ops to define the end of a function concerning datatypes,
		returning a new datatype object and creating an explicit stage node
		in the graph
		newStage RESETS REPRESENTATION - a fresh command is required to create
		a new active node"""

		newNode = self.addPartition(name="{}_end-{}_begin-{}".format(
			self.D, self.stageName, stageName))
		# newData = self.__class__(node=newNode)
		# self.stageName = stageName
		# self.active = newNode
		return newNode

	def addPartition(self, name=None):
		"""please please please help me"""
		return True

	def setActive(self, node):
		self.active = AbsoluteNode(node)

	def getPoint(self, *args, **kwargs):
		"""common to all datatypes"""
		pass


class Simple(Datatype):
	"""for passing simple items - strings, floats, vectors etc"""

	def asPlug(self):
		"""returns the live plug value of the datatype, or none"""
		if self.activePlug:
			return self.activePlug
		else:
			return None

	def asValue(self):
		"""returns the flat value"""

	def connectValue(self, targetAttr):
		"""connects active plug if it exists, sets targetAttr if not"""
		if self.asPlug():
			cmds.connectAttr(self.asPlug(), targetAttr, f=True)
		else:
			cmds.setAttr(targetAttr, self.asValue())

	def setValue(self, targetAttr):
		cmds.setAttr(targetAttr, self.asValue())

class Point(Datatype):
	"""class combining transform, locator, joint etc"""
	defaultNode = "transform"
	D = "0D"

	#spaceList = ["world", "local", "parent", "custom"]
	def __init__(self, node=None):
		super(Point, self).__init__(node=node)
		#self.spaceName=space
		self.tf = None
		self.tfn = None
		self.worldMat = None
		self.localMat = None
		self.u = None
		self.v = None
		if node:
			self.setActive(node)
		pass

	#def setPoint(self, transform=None):
	def setActive(self, transform):
		super(Point, self).setActive(transform)
		self.tf = core.AbsoluteNode(transform)
		self.MObject = self.tf.MObject
		self.tfn = self.tf.MFnTransform
		self.activePlug = self.tf+".matrix"
		self.localMat = self.tf+".matrix"
		self.worldMat = self.tf+".worldMatrix[0]"


	def asMVector(self):
		return self.tfn.translation(1)

	def asMMatrix(self):
		return libtf.WorldMMatrixFrom(self.tf)

	def asJoint(self):
		"""converts to a joint in local space"""
		if self.active.nodeType == "joint":
			return self.active
		joint = self.ECA("joint", name=self.stageName+"_point_asJoint")
		cmds.parent(joint, self.spaceGrp)
		self.connectTransformAttrs(self.active, joint)
		self.setActive(joint)

	def connectTransformAttrs(self, driver, driven):
		libtf.connectTransformAttrs(driver, driven)

	def getPoint(self):
		return self

	@property
	def worldTranslate(self):
		return cmds.xform(self.active, q=True, ws=True, t=True)


class Curve(Datatype):
	"""my life, my love and my lady"""
	D = "1D"

	def __init__(self, node=None, ):
		super(Curve, self).__init__(node)
		self.upCurve = None
		self.points = {} # optional DICT of 0D Point datatypes, indexed by u value on curve
		# not carried over to new stages
		self.res = []
		self.v = None # for use in surfaces
		self.curveInput = None
		self.localCurve = None
		self.worldCurve = None

	def setActive(self, node):
		test = AbsoluteNode(node)
		if not test.isShape():
			test = test.shape
		super(Curve, self).setActive(test)
		self.activePlug = self.active+".local"
		self.curveInput = self.active + ".create"
		self.localCurve = self.active + ".local"
		self.worldCurve = self.active + ".worldSpace[0]"

	def setUpCurve(self, upCurve):
		self.upCurve = AbsoluteNode(upCurve)
		#cmds.parent(upCurve, self.spaceGrp)

	def getPoint(self, live=True, u=0.5, constantU=True, purpose="getPoint"):
		"""returns riveted point on curve"""
		return self.getRivetPoint(u, constantU=constantU, purpose=purpose)

	def addPoint(self, u, point):
		self.points[u] = point

	def setRivetPoint(self, point):
		u = self.getClosestU(point.worldTranslate)
		libcurve.curveRivet(point.active, self.active.shape, u, upCrv=self.upCurve.shape)
		return u

	def getRivetPoint(self, u, constantU=True, purpose="anyPurpose"):
		"""returns a point anchored on the main curve"""
		dag = self.ECA("transform", self.name+"_pointAt{}U".format(u))
		point = Point(dag)
		libcurve.curveRivet(point.active, self.active.shape, u, upCrv=self.upCurve.shape,
		                    constantU=constantU, purpose=purpose)
		return point

	def getClosestU(self, pos=None, target=None, percent=True):
		"""returns u value of main curve closest to pos"""
		if target:
			pos = cmds.xform(target, ws=True, t=True, q=True)
		point = om.MPoint(*pos)
		baseU = self.active.shapeFn.closestPoint(point)[1]
		if not percent:
			return baseU
		return self.active.shapeFn.findLengthFromParam(baseU) / self.active.shapeFn.length()


	def skinToPoints(self, points=None):
		points = core.makeList(points)
		null = self.ECA("joint", name=self.name+"SkinNull")
		cmds.parent(null, self.spaceGrp)
		# mainSkin = cmds.skinCluster([null], crvSpine, name='spine_skinCluster', toSelectedBones=True, bindMethod=0, skinMethod=0,
		#                normalizeWeights=1)[0]
		mainSkin = cmds.skinCluster(null.node, self.active, name=self.name+"mainSkin",
		                            toSelectedBones=True, skinMethod=1)
		upSkin = cmds.skinCluster(null.node, self.upCurve, name=self.name+"upSkin",
		                          toSelectedBones=True, skinMethod=1)
		# mainSkin = cmds.skinCluster(self.active, name=self.name + "mainSkin")
		# upSkin = cmds.skinCluster(self.upCurve, name=self.name + "upSkin")
		for i in points:
			cmds.skinCluster(mainSkin, edit=True, ai=i.asJoint())
			cmds.skinCluster(upSkin, edit=True, ai=i.asJoint())

	def getPointAtU(self, u):
		return self.active.shapeFn.getPointAtParam(u)

	def getUValues(self):
		return self.points.keys()




#
# class JointCurve(Datatype):
# 	#"""my life my love and my lady"""
#
# 	def __init__(self):
# 		# the idea here is only to create joints or curve when needed
# 		# do that later - for now both are created
# 		super(JointCurve, self).__init__()
# 		self._curveTf = None
# 		self.curveFn = None
# 		self.curveShape = None
# 		self._upCurveTf = None
# 		self.upCurveFn = None
# 		self.upCurveShape = None
# 		self._joints = []  # list of point datatypes
# 		self.drivenBy = "curve"
# 		self.chainedJoints = False
#
# 	@property
# 	def __name__(self):
# 		return "JointCurve1D"
#
# 	@property
# 	def curveTf(self):
# 		return self._curveTf
#
# 	@curveTf.setter
# 	def curveTf(self, value):
# 		if libcurve.isCurve(value):
# 			self.curveShape = core.AbsoluteNode(value)
# 			self._curveTf = core.AbsoluteNode(core.tfFromShape(value))
# 		elif core.isType(value, "transform"):
# 			self._curveTf = core.AbsoluteNode(value)
# 			self.curveShape = core.AbsoluteNode(core.shapeListFromTf(value)[0])
# 		self.curveFn = libcurve.curveFnFrom(self.curveShape)
#
# 	@property
# 	def upCurveTf(self):
# 		return self._upCurveTf
#
# 	@upCurveTf.setter
# 	def upCurveTf(self, value):
# 		if libcurve.isCurve(value):
# 			self.upCurveShape = value
# 			self._upCurveTf = core.tfFromShape(value)
# 		elif core.isType(value, "transform"):
# 			self._upCurveTf = value
# 			self.upCurveShape = core.shapeListFromTf(value)[0]
# 		self.upCurveFn = libcurve.curveFnFrom(self.upCurveShape)
#
# 	@property
# 	def joints(self):
# 		return self._joints
#
# 	@joints.setter
# 	def joints(self, value):
# 		print "setting joints"
# 		self._joints = []
# 		if not isinstance(value, list):
# 			value = [value]
# 		for i in value:
# 			# create a 1D datatype for each joint
# 			data = Point()
# 			data.setActive(i)
# 			if self._curveTf:
# 				u = libcurve.getClosestU(self._curveTf, i)
# 				#data.u = u
# 				data.setU(u)
# 			self._joints.append(data)
# 		print "_joints is {}".format(str(self._joints))
#
#
# 	def passJoints(self, nameList):
# 		# at creation
# 		# overrides things for now - don't try to change the same datatype later
# 		self.joints = nameList
#
#
# 	def createJoints(self):
# 		for i in self.joints:
# 			joint = self.ECA("joint", i["name"])
# 			i["node"] = joint
#
# 		if self.chainedJoints:
# 			self.chainJoints()
#
#
# 	""" currently datatypes themselves do not save data;
# 	this is handled by individual ops. reasoning is that
# 	these datatypes should never need to be edited by op or
# 	user - they're just collections of useful information.
# 	user decides what to do with that information.
# 	...doesn't mean we shouldn't help the op along"""
#
#
# 	def updateData(self, data=None, joints=True, curves=True):
# 		"""explicitly define the data to be updated - could be inputs,
# 		outputs etc. example would be (from the parent op):
# 			self.saveData["jointcurve"] = {}
# 		and then populate that with the information from the datatype object
# 		"""
# 		pass
#
#
# 	def applyData(self, joints=True, curves=True):
# 		pass
#
#
# 	def passCurve(self, curve):
# 		# to make io easier - just set the datatype curve to the
# 		# live output of the layer
# 		pass
#
#
# 	def passUpCurve(self, upCurve):
# 		pass
#
#
# 	def chainJoints(self):
# 		for i, val in enumerate(self.joints):
# 			if i == 0:
# 				continue
# 			cmds.parent(val["node"], self.joints[i - 1]["node"])
# 			# val["node"].parentIs(self.joints[i-1]["node"])
# 		pass
#
#
# 	def emancipateJoints(self):
# 		# still unsure how to handle dag organisation - wait to see how
# 		# lowestCommonParent works out. might be better to let op handle it
# 		for i, val in enumerate(self.joints):
# 			cmds.parent(val["dag"], world=True)
# 		pass
#
#
# 	def driveCurveWithJoints(self):
# 		"""for every cv, check for the closest joint,
# 		and matrix constrain it to that joint"""
# 		print "driving curve with joints"
# 		print "joints are {}".format(self.joints)
# 		if not self.curveFn:
# 			print "no curveFn found"
# 			return False
# 		for curveFn, curveShape in zip(
# 				[self.curveFn, self.upCurveFn],
# 				[self.curveShape, self.upCurveShape]):
# 			cvPosList = curveFn.cvPositions() # kObject only
# 			for i, cv in enumerate(cvPosList):
# 				closest = self.joints[self.closestJoint(cv)]
# 				closestMat = closest.asMMatrix()
# 				offset = cv * closestMat.inverse()
#
# 				mult = self.ECN("pointMatrixMult", "driveCurveCvWithJointMat")
# 				cmds.setAttr(mult+".inPoint", *offset)
# 				cmds.connectAttr(closest.tf+".worldMatrix", mult+".inMatrix")
# 				cmds.connectAttr(mult+".output",
# 				                 curveShape+".controlPoints[{}]".format(i))
#
# 				#libtf.matrixConstraint(self.curveShape+".")
#
#
# 				pass
#
# 		pass
#
#
# 	def driveJointsWithCurve(self):
# 		print "driving joints with curve"
# 		print "joints are {}".format(self.joints)
# 		for i in self.joints:
# 			libcurve.curveRivet(i.tf, self.curveShape, i["u"],
# 			                    upCrv=self.upCurveShape)
# 		pass
#
# 	# more convenience methods
# 	def closestJoint(self, point, space="world"):
# 		"""point can be Point, MPoint, or tuple as returned from xform"""
# 		vec = om.MVector(point)
# 		closest = None
# 		mag = 10000.0
# 		index = 0
# 		for i, val in enumerate(self.joints):
# 			newMag = om.MVector(vec - val.asMVector()).length()
# 			#print "new mag is {}".format(newMag)
# 			if newMag < mag:
# 				#print "found new closest"
# 				closest = val
# 				mag = newMag
# 				index = i
# 		return index
# 		# works
#
#
#
#
# 		pass


class Surface(Datatype):
	def __init__(self):
		super(Surface, self).__init__()
		pass

class Volume(Datatype):
	def __init__(self):
		super(Volume, self).__init__()
		pass
