# layers working with transforms, hierarchy, point data, joints
import edRig.node
from edRig.core import ECN, con
from edRig import core, transform, attrio, control, curve, point, ECA
from maya import cmds
from edRig.tesserae.ops.layer import LayerOp
from edRig.layers.datatypes import Point, Curve
import maya.api.OpenMaya as om
import random


# is it a good idea to split joint and point ops? idk but we're gonna find out

# we found out
# it wasn't

class SpookyLayerOp(LayerOp):
	# ops for working with spooky skeletons
	def __init__(self, name):
		super(SpookyLayerOp, self).__init__(name)
		print "doot"


class JointCurveOp(SpookyLayerOp):
	""" this should really just be two separate ops
	but it's fine

	active mode is regenerated first, and takes priority
	in defining the placement of the other

	eventually get rid of count as attribute, rely totally on
	settings and number of joint entries - for now just get it working

	"""


	def defineAttrs(self):
		self.addInput(name="parent", dataType="nD",
		              desc="dimensional input; this jointCurve will inherit all parent transformations")
		self.addInput(name="jointCount", dataType="int",
		              desc="number of joints to create along curve",
		              default=4, min=1)

		self.addOutput(name="jc", dataType="1D",
		               desc="static output jointcurve")


		# dynamic attributes
		# for i in range(self.getInput("jointCount").value):
		# 	self.addOutput(name="point{}".format(i), dataType="0D",
		# 	               desc="individual points on curve", hType="leaf")
		#self.refreshIo()

	def defineSettings(self):
		self.addSetting(entryName="prefix", value="c_")
		self.addSetting(entryName="mode", options=("joints", "curve"),
		                value="joints")
		self.addSetting(entryName="curve")
		self.settings["curve"]["degree"].value = 1
		self.settings["curve"]["closed"].value = 0

		self.addSetting(entryName="joints")
		for i in range( self.getInput("jointCount").value ):
			entry = self.settings["joints"][ "joint{}".format(i) ]






	def refreshSettings(self):
		"""add a settings entry for every joint"""
		for i in range(self.getInput("jointCount").value):
			jointName = "joint{}".format(i)
			jointEntry = self.settings["joints"].get(jointName)
			if not jointEntry:

				jointEntry["crossLock"].value = False


	def __init__(self, name="JointCurveOp"):
		super(JointCurveOp, self).__init__(name)
		self.opName = name
		self.jointsToCreate = {}
		self.out1D = None
		self.joints = None
		self.mainCurve = None
		self.upCurve = None
		self.prefix = None

		print "doot doot"

	def execute(self):
		# set up starter joints - only create controls if stop is true
		#self.out1D = Curve()

		print "inputs at plan are {}".format(self.inputs)

		self.updateInputs()

		if self.settings["mode"] == "joints":
			self.createJoints()
			self.matchCurvesToJoints()
		else:
			self.createCurves()
			self.matchJointsToCurve()

		# self.connectInputs()

		self.memory.setClosed("joints", status=True)
		self.updateOutputs()

	#@tidy
	def showGuides(self):
		print "running jointCurve planStop"
		#print "inputMode is {}".format(self.inputs["mode"]["value"])
		self.memory.setClosed("joints", status=False)
		self.memory.setClosed("curves", status=False)

		pointList = [Point(i) for i in self.joints]

		if self.getInput("mode").value == "joints":
			self.matchControlsToJoints()
			self.out1D.skinToPoints(pointList)

		elif self.getInput("mode").value == "curve":
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
		self.prefix = self.settings["prefix"]

	def connectInputs(self):
		"""connect space group to parent"""
		matPlug = point.getPoint(on=self.getInput("parent").plug,
		               near=self.joints[0])
		transform.decomposeMatrixPlug(matPlug, target=self.spaceGrp)

	def updateOutputs(self):
		"""transfer output objects to attribute values"""
		# print "out1D is {}".format(self.getOutput("jc"))
		self.getOutput("jc").value = self.out1D
		cmds.connectAttr(self.mainCurve.shape+".local",
		                 self.getOutput("jc").plug+".mainCurve")
		cmds.connectAttr(self.upCurve.shape + ".local",
		                 self.getOutput("jc").plug + ".upCurve")


	def createJoints(self):
		# make joints, parent them
		jointCount = len(self.jointsToCreate)

		jointDict = self.settings.get("joints")
		if not jointDict:
			return
		for k, v in jointDict.iteritems():
			print k, v








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
		self.mainCurve = edRig.node.AbsoluteNode(cmds.rebuildCurve(linearShape, ch=False, degree=curveDeg,
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
		self.upCurve = edRig.node.AbsoluteNode(cmds.rebuildCurve(upData["shape"], ch=False, degree=upCurveDeg,
		                                                         rebuildType=0, fitRebuild=True)[0])
		cmds.parent([self.mainCurve, self.upCurve], self.spaceGrp)

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
			jntCtrl = control.OldControl(val, type="tet")
			self.jntCtrls.append(jntCtrl)
			transform.matchXforms(target=jntCtrl.tf, source=val)
			cmds.pointConstraint(jntCtrl.pivotLoc, val, mo=False)
			jntCtrl.pinShapesToPivot()

			if i < len(self.joints) - 1:
				cmds.setAttr(val + ".displayLocalAxis", 1)
				aimCtrl = control.OldControl(val + "Aim", type="sphere")
				self.aimCtrls.append(aimCtrl)
				prettyLine = curve.curveFromCvs(
					[jntCtrl.worldTrans, aimCtrl.worldTrans],
					name="upVectorCrv", deg=1, mode="live")

				# do pretty colours later

				pmm = ECA("pmm", "aimPmm")
				pmm.set("inPoint", (0, 0, 5) )
				pmm.set("vectorMultiply", 0)
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
