""" this is the remnant of a totally failed experiment
originally this was an idea to treat points, curves and surfaces totally
agnostically in code and in maya, but it quickly became far too complex,
and it never actually worked.
we still maintain the principle in the structure of the system today"""
import edRig.node
from edRig import core, transform
import edRig.curve as libcurve
import edRig.transform as libtf
from maya import cmds
import maya.api.OpenMaya as om
from collections import OrderedDict
from edRig.core import shortUUID, randomWord
from edRig.node import AbsoluteNode, invokeNode
from edRig.tesserae.ops.op import Op
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
		node = edRig.node.ECA(type, name, *args)
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
		self.tf = edRig.node.AbsoluteNode(transform)
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
		if self.active.nodeType() == "joint":
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



class Surface(Datatype):
	def __init__(self):
		super(Surface, self).__init__()
		pass

class Volume(Datatype):
	def __init__(self):
		super(Volume, self).__init__()
		pass

class DimFn(object):
	"""function set for general work with dimensional data"""

	@classmethod
	def getPoint(cls, on=None, near=None, live=True):
		"""blanket catch-all method for getting closest point
		on curves, meshes, surfaces"""
		print "on is {}".format(on)
		plug = None
		if core.isPlug(on):
			plug = cls.getPointFromPlug(on, near)
		elif isinstance(on, Datatype):
			plug = on.activePlug
			plug = cls.getPointFromPlug(plug, near)
		print "plug is {}".format(plug)
		return plug

	@classmethod
	def getPointFromPlug(cls, on, near, up=None):
		"""returns matrix plug"""
		kind = cmds.getAttr(on, type=True)
		mat = None
		if kind == "matrix" :
			# my work is done
			mat = on
		else:
			dummy = edRig.node.ECA("locator", "pointProxy")
			transform.matchXforms(dummy, source=near)
			if kind == "nurbsCurve":
				u = libcurve.getClosestU(on, near)
				libcurve.curveRivet(dummy, on, u, upCrv=up)
				mat = dummy+".matrix"
		return mat




