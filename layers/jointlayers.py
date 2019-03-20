# layers working with transforms, hierarchy, point data, joints
from edRig.core import ECN, con
from edRig import core, transform, attrio, control, curve
from maya import cmds
#from edRig.layers.base import LayerOp
from edRig.tilepile.ops.layer import LayerOp
import edRig.layers.base
from edRig.layers.datatypes import Point, Curve
import maya.api.OpenMaya as om
import random


# is it a good idea to split joint and point ops? idk but we're gonna find out


class SpookyLayerOp(LayerOp):
	# ops for working with spooky skeletons
	def __init__(self, name):
		#super(self.__class__, self).__init__(name)
		super(SpookyLayerOp, self).__init__(name)
		print "doot"


class JointCurveOp(SpookyLayerOp):
	# "simple" layer for creating starting skeletons
	# one-dimensional (curve) data element
	# the TRUE swag would be to inherit data structure itself,
	# with 0Ds making 1D making 2D etc

	# TO DO: move all joint creation methods to jointCurve datatype
	# to assist in other ops' implicit creation

	data = {
		"mode": {
			"value" : "joints",
			"options" : "joints or curve",
			"used" : "only at setup"},

		"joints": [
			{  # always correspond to the order in which joints are created
				"name": "base" + str(LayerOp.shortUUID(4)),
				"crosslock": False,
				# "dof" : "xyz",
				"rotOrder": "xyz"
			}
		],
		"curve": {
			"deg": 3,
			"closed": False
		},
		"upCurve": {
			"deg": 3,
			"closed": False
		}
	}


	def defineAttrs(self):
		self.addInput(name="parent", dataType="nD",
		              desc="dimensional input; this jointCurve will inherit all parent transformations")
		self.addInput(name="jointCount", dataType="int",
		              desc="number of joints to create along curve",
		              default=4, min=1)
		self.addInput(name="prefix", dataType="string",
		              desc="base name to assign joints on creation (editable later)",
		              default="jointCurve")

		self.addInput(name="mode", dataType="enum",
		              desc="build based on curve or on joints",
		              items=["curve", "joints"], default="joints")

		self.addOutput(name="jc", dataType="1D",
		               desc="static output jointcurve")
		# for i in range(self.getInput("jointCount").value):
		# 	jc.addAttr(name="point{}".format(i), dataType="0D",
		# 	               desc="individual points on curve", hType="leaf")
		self.refreshIo()


	def refreshIo(self, controller=None, attrChanged=None):
		update = False
		# here defines custom behaviour of the point outputs
		# self.log("attr changed is {}".format(attrChanged))
		# if attrChanged == "jointCount":
		# 	newLen = self.getInput("jointCount").value
		# 	oldLen = len(self.getOutput("jc").getChildren())
		# 	if newLen > oldLen:
		# 		for n in range(newLen - oldLen):
		# 			newPoint = self.getOutput("point0").copyAttr()
		# 			newPoint.name = "point{}".format(oldLen+n)
		# 			self.addOutput(parent=self.getOutput("jc"), attrItem=newPoint)
		# 	elif newLen < oldLen:
		# 		for n in range(oldLen - newLen):
		# 			self.getOutput("jc").removeAttr("point{}".format(oldLen-n))
		return update
		pass


	def __init__(self, name="JointCurveOp"):
		super(JointCurveOp, self).__init__(name)
		self.opName = name
		self.jointsToCreate = {}
		self.out1D = None
		self.joints = None
		self.mainCurve = None
		self.upCurve = None
		self.prefix = None
		print "inputs are {}".format(self.inputs)
		print "instance inputs are {}".format(self.inputs)
		print "inputs after super are {}".format(self.inputs)
		print "outputs after super are {}".format(self.outputs)
		print "doot doot"

	def execute(self):
		print "running jointCurve plan"
		# set up starter joints - only create controls if stop is true
		#self.out1D = Curve()

		print "inputs at plan are {}".format(self.inputs)

		self.updateInputs()

		self.setJointsToCreate()
		self.createJoints()
		self.createCurves()
		self.matchSavedJointInfo()
		self.update1D()

		self.memory.setClosed("joints", status=True)

		self.updateOutputs()

	def showGuides(self):
		print "running jointCurve planStop"
		#print "inputMode is {}".format(self.inputs["mode"]["value"])
		self.memory.setClosed("joints", status=False)
		self.memory.setClosed("curves", status=False)

		pointList = [Point(i) for i in self.joints]

		# if self.inputs["mode"]["value"] == "joints":
		if self.getInput("mode").value == "joints":
			self.matchControlsToJoints()
			self.out1D.skinToPoints(pointList)

		elif self.getInput("mode").value == "curve":
		#	raise NotImplementedError
			#self.matchControlsToCurve()
			for i in pointList:
				self.out1D.setRivetPoint(i)
		#	pass

		return 1

	def update1D(self):
		self.out1D = Curve(node=self.mainCurve)
		self.out1D.upCurve = self.upCurve
		for i in self.joints:
			u = curve.getClosestU(self.mainCurve, i)
			point = Point(i)
			self.out1D.addPoint(u, Point)
		pass

	def updateInputs(self):
		self.prefix = self.getInput("prefix").value

	def updateOutputs(self):
		"""transfer output objects to attribute values"""
		# print "out1D is {}".format(self.getOutput("jc"))
		self.getOutput("jc").value = self.out1D

	def setJointsToCreate(self):
		self.jointsToCreate = self.data["joints"]  # list of dicts
		prefix = self.getInput("prefix").value
		# CHECK that we have enough data slots for the number of joints we create
		currentLength = len(self.data["joints"])
		if currentLength < self.getInput("jointCount").value:

			# if creating 2 joints, should have keys 0 and 1 (end not created yet)
			for i in range(self.getInput("jointCount").value - currentLength):
				emptyData = {  # if creating 1 joint already, adds entry 1:name, etc
					"name": "{}{}_jnt".format(prefix, currentLength + i),
					"crosslock": False,
					"dof": "xyz",
					"rotOrder": "xyz"
				}
				# this way extending the chain uses existing info for new joints
				self.data["joints"].append(emptyData)
		# is there any data left over for the end joint (data 1 longer than jointcount)
		# or do we need to create it
		currentLength = len(self.data["joints"])
		if currentLength == self.getInput("jointCount").value:
			endData = {  # if creating 1 joint already, adds entry 1:name, etc
				"name": "{}{}_jnt".format(prefix, currentLength + 1),
				"dof": "xyz",
				"rotOrder": "xyz"
			}
			self.data["joints"].append(endData)

		"""
		if crosslock, joint upvector is locked to cross product of vectors to previous
		and next, length of average of each
		always create one end joint implicitly with no upvector
		"""


	def createJoints(self):
		# make joints, parent them
		jointCount = len(self.jointsToCreate)

		self.joints = []
		for i in range(jointCount):
			# create joint with right name
			pref = self.jointsToCreate[i]["name"]
			joint = self.ECA("joint", pref + "_planJnt")
			self.addTag(joint, "jointKeyTag", tagContent=pref)

			self.joints.append(joint)
			# refit this with scene scale eventually
			cmds.xform(joint, t=[random.random(), i * 5.0, random.random()])

			if i > 0:
				# self.joints[i] = cmds.parent(joint, self.joints[i-1])[0]
				# see what we had to put up with before i saved programming in maya
				cmds.parent(joint, self.joints[i - 1])

		cmds.parent(self.joints[0], self.setupGrp)

			#self.points.append(Point(node=joint))
			#self.out1D.addPoint(Point(node=joint))



	def createCurves(self):
		# first main curve
		points = []
		upPoints = []
		curveDeg = self.data["curve"]["deg"]
		curveClosed = self.data["curve"]["closed"]
		upCurveDeg = self.data["upCurve"]["deg"]
		upCurveClosed = self.data["upCurve"]["closed"]
		#curveSpans = self.data["curve"]["spans"]
		for i in self.joints:
			points.append(cmds.xform(i, q=True, ws=True, t=True))
		# first make linear curve
		linData = curve.curveFromCvs(points, deg=1, name=self.prefix+"_crv")
		#linearTf = linData["tf"]
		linearShape = linData["shape"]

		# rebuild in a way that is exactly reproducible every time
		self.mainCurve = core.AbsoluteNode(cmds.rebuildCurve(linearShape, ch=False, degree=curveDeg,
		                               rebuildType=0, fitRebuild=True)[0])
		#self.out1D.setActive(self.mainCurve)

		# now create upCurve
		for i in self.joints:
			#mat = core.MMatrixFrom(i)
			mat = om.MMatrix(cmds.getAttr(i+".worldMatrix[0]"))
			upPoints.append(transform.staticVecMatrixMult(
				mat, point=(1,0,0), length=1))
		#self.log("upPoints are {}".format(upPoints))
		upData = curve.curveFromCvs(upPoints, deg=1, name=self.prefix+"_upCrv")
		self.upCurve = core.AbsoluteNode(cmds.rebuildCurve(upData["shape"], ch=False, degree=upCurveDeg,
		                               rebuildType=0, fitRebuild=True)[0])

		pass


	def freezeJoints(self):
		#print self.joints
		for i in self.joints:
			#print i
			for ax in "XYZ":
				#print i + ".rotate" + ax
				core.breakConnections(i + ".rotate" + ax)
				core.breakConnections(i + ".translate" + ax)
		for i in self.joints:
			cmds.makeIdentity(i, apply=True, rotate=True)

	def matchSavedJointInfo(self):
		# wat up now swedes
		self.remember("joints", "xform", self.joints, jointMode=True)
		self.remember("joints", "attr", self.joints, transform=False)
		self.remember("curves", "shape", [self.upCurve.shape, self.mainCurve.shape])
		#print "memory after remember is {}".format(self.memory.serialiseMemory())
		# self.memory.recall("joints", "attr")
		# self.memory.recall("joints", "xform")
		# no but seriously swedes wat up now

	def updateSavedJointData(self):
		# update the dict
		#print "self.data is {}".format(self.data)
		self.memory.refresh("joints", "xform", jointMode=True)
		self.memory.refresh("curves", "shape")

	def matchControlsToJoints(self):
		# to be run if stopping on plan
		# after joints are created and moved into position,
		# create plan controls and match them to joints
		# then create all the fancy constraint rubbish

		self.jntCtrls = []
		self.aimCtrls = []

		for i, val in enumerate(self.joints):
			jntCtrl = control.Control(val, type="tet")
			self.jntCtrls.append(jntCtrl)
			transform.matchXforms(target=jntCtrl.tf, source=val)
			cmds.pointConstraint(jntCtrl.pivotLoc, val, mo=False)
			jntCtrl.pinShapesToPivot()

			if i < len(self.joints) - 1:
				cmds.setAttr(val + ".displayLocalAxis", 1)
				aimCtrl = control.Control(val + "Aim", type="sphere")
				self.aimCtrls.append(aimCtrl)
				prettyLine = curve.curveFromCvs(
					[jntCtrl.worldTrans, aimCtrl.worldTrans],
					name="upVectorCrv", deg=1, mode="live")

				# do pretty colours later

				pmm = core.ECn("pmm", "aimPmm")
				pmm.inPoint = (0, 0, 5)
				pmm.vectorMultiply = 0
				cmds.connectAttr(val + ".worldMatrix[0]", pmm + ".inMatrix")
				cmds.connectAttr(pmm + ".output", aimCtrl.tf + ".translate")
				core.breakConnections(aimCtrl.tf + ".translate")

				# last of all
				self.aimCtrls[i].reparentUnder(self.jntCtrls[i].pivotLoc)
			# print "self.jntCtrls is {}".format(self.jntCtrls)
			# print "self.jntCtrls is {}".format(self.aimCtrls)

		for i, val in enumerate(self.joints):
			if i < len(self.joints) - 1:
				jntAim = cmds.aimConstraint(self.jntCtrls[i + 1].pivotLoc, val,
				                            upVector=[0, 0, 1], aimVector=[1, 0, 0], mo=False,
				                            worldUpObject=self.aimCtrls[i].tf, worldUpType="object")

			if i > 0:
				# self.jntCtrls[i] = cmds.parent(self.jntCtrls[i].tf, self.jntCtrls[i-1].tf)[0]
				self.jntCtrls[i].reparentUnder(self.jntCtrls[i - 1].tf)
		pass
