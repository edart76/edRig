# layers working with transforms, hierarchy, point data, joints

import edRig.maya.core.node
from edRig import transform, control, curve, point, ECA, plug, \
	cmds, om
from edRig.maya import core

from edRig.tesserae.ops.layer import LayerOp


# is it a good idea to split joint and point ops? idk but we're gonna find out

# we found out
# it wasn't

class SpookyLayerOp(LayerOp):
	# ops for working with spooky skeletons
	def __init__(self, *args, **kwargs):
		super(SpookyLayerOp, self).__init__(*args, **kwargs)
		print( "doot")


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
		""" NB: allowing this as nD implies that all individual points
		will be driven equally by distortion of the parent space, not just the
		root point
		this may at some point change due to difficulty of implementation and
		redundancy compared to dedicated ops"""

		self.addOutput(name="jc", dataType="1D",
		               desc="static output jointcurve")

		# point array
		array = self.addOutput(name="points", dataType="0D",
		               hType="array", desc="output points")
		array.setChildKwargs(dataType="0D", desc="output point")


	def defineSettings(self):
		#self.addSetting(entryName="prefix", value="c_")
		self.addSetting(entryName="priority", options=("joints", "curve"),
		                value="joints")
		self.addSetting(entryName="curve")
		self.settings["curve.degree"] = 1
		self.settings["curve.closed"] = 0

		self.addSetting(entryName="joints")
		for i in range( 4 ):
			entry = self.settings["joints.joint{}".format(i) ]


	def onSync(self):
		self.matchOutputsToSettings()

	def matchOutputsToSettings(self):
		jointTree = self.settings("joints")
		outputs = list(jointTree.keys())
		pointPlug = self.getOutput("points")
		specList = [ {"name" : i} for i in outputs]
		#self.log( "specList {}".format(specList))
		#print( pointPlug.display())
		pointPlug.matchArrayToSpec(spec=specList)


	def execute(self):

		#self.prefix = self.settings["prefix"]
		self.joints = []
		self.mainCurve, self.upCurve = None, None

		self.createJoints()
		self.createCurves()

		#self.loadMemory()
		print("jointCurve memory is {}".format(self.memory.display()))

		if self.settings["priority"] == "joints":
			self.matchCurveToJoints()
			self.remember("joints", "attr", self.joints, transformAttrs=False)
			self.remember("joints", "xform", self.joints, jointMode=True)
			# self.remember("joints", "attr", self.joints, transformAttrs=False)
			self.freezeJoints()
			#self.refreshMemoryAndSave()

		else:
			self.matchJointsToCurve()
			self.remember("curve", "shape",
			              nodes=[self.mainCurve.shape, self.upCurve.shape])

		# self.memory.setClosed("curves", status=True)
		# self.memory.setClosed("joints", status=True)
		self.updateOutputs()

	""" consider behaviour when adding new joints - 
	a curve-driven system should seek to preserve original point positions
	while maintaining equal spacing between transforms
	in this case, consider adding any new joints in a binary split
	sort of manner
	
	ie for an original number of joints n, being increased to n + 1,
	the position of each joint n should vary minimally
	
	i'm sick of agonising over it - two modes are totally independent of
	each other
	
	"""

	def matchJointsToCurve(self):
		""" rivet joints to curve and upCurve"""

		n = len( self.joints )
		for i in range( n ):
			u = 1.0 / (n - 1) * i
			# create pcis
			pci = curve.pciAtU(self.mainCurve.shape + ".local", u=u, )
			upPci = curve.pciAtU(self.upCurve.shape + ".local", u=u, )
			upVec = plug.vecFromTo( pci + ".position", upPci + ".position")
			jntMat = curve.matrixPlugFromPci(pci, upVector=upVec)

			# self.joints[i].disconnect("inverseScale")

			self.joints[i].parentTo(self.opGrp, r=1)

			transform.decomposeMatrixPlug(jntMat, self.joints[i])
			self.joints[i].set("inverseScale", (1, 1, 1))

			#self.joints[i].setDrawingOverride(referenced=1)
		pass

	def matchCurveToJoints(self):
		""" attach curve and upcurve to joints """
		for i, val in enumerate(self.joints):
			# main curve points
			posPmm = ECA("pointMatrixMult", n="main{}_pos".format(i))
			posPmm.con(val + ".worldMatrix[0]", posPmm + ".inMatrix")
			posPmm.con("output", self.mainCurve + ".controlPoints[{}]".format(i))

			# upCurve points
			upPmm = ECA("pointMatrixMult", n="up{}_pos".format(i))
			upPmm.set("inPoint", (0, 1, 0))
			upPmm.con(val + ".worldMatrix[0]", "inMatrix")
			upPmm.con("output", self.upCurve + ".controlPoints[{}]".format(i))

		# simple for now in that it only affects cvs, not edit points
		pass


	def createJoints(self):
		entry = self.settings("joints")
		for i, val in enumerate(entry.keys()):
			joint = self.ECA("joint", name=val)
			self.joints.append(joint)
			joint.set("translateY", i * 5)

			if i :
				joint.parentTo(self.joints[i - 1])

		return self.joints

	def createCurves(self):
		# first main curve
		points = []
		upPoints = []
		degree = int(self.settings["curve.degree"])
		# matching to joints on creation is fine, both will be reset later
		for i in self.joints:
			points.append(cmds.xform(i, q=True, ws=True, t=True))
		# first make linear curve
		#linearShape = curve.curveFromCvs(points, deg=1, name=self.prefix+"_crv")
		linearShape = curve.curveFromCvs(points, deg=1, name=self.opName+"_mainCrv")
		self.mainCurve = edRig.maya.core.node.AbsoluteNode(
			cmds.rebuildCurve(linearShape, ch=False, degree=degree,
		                        rebuildType=0, fitRebuild=True)[0])
		# now create upCurve
		# we will one day be free of it
		for i in self.joints:
			mat = om.MMatrix(cmds.getAttr(i+".worldMatrix[0]"))
			upPoints.append(transform.staticVecMatrixMult(
				mat, point=(1,0,0), length=1))
		#self.log("upPoints are {}".format(upPoints))
		upShape = curve.curveFromCvs(upPoints, deg=1, name=self.opName+"_upCrv")
		self.upCurve = edRig.maya.core.node.AbsoluteNode(
			cmds.rebuildCurve(upShape, ch=False, degree=degree,
		    rebuildType=0, fitRebuild=True)[0])
		cmds.parent([self.mainCurve, self.upCurve], self.spaceGrp)


	#@tidy
	def showGuides(self):

		if self.settings["priority"] == "joints":
			self.matchControlsToJoints()
			#self.out1D.skinToPoints(pointList)
			for i in self.joints:
				self.markAsGuide(i)


		elif self.settings["priority"] == "curve":
			self.memory.setClosed("curves", status=False)
			for i in self.joints:
				#self.out1D.setRivetPoint(i)
				u = curve.getClosestU(self.mainCurve, tf=i.transform)
				curve.curveRivet(
					point, self.mainCurve.shape, u,
					upCrv=self.upCurve.shape)
			self.markAsGuide(self.mainCurve)
			self.markAsGuide(self.upCurve)

		return 1

	def connectInputs(self):
		"""connect space group to parent"""
		matPlug = point.getPoint(on=self.getInput("parent").plug,
		               near=self.joints[0])
		transform.decomposeMatrixPlug(matPlug, target=self.spaceGrp)

	def updateOutputs(self):
		"""transfer output objects to attribute values"""
		# print "out1D is {}".format(self.getOutput("jc"))
		# self.getOutput("jc").value = self.out1D
		cmds.connectAttr(self.mainCurve.shape+".local",
		                 self.getOutput("jc").plug+".mainCurve")
		cmds.connectAttr(self.upCurve.shape + ".local",
		                 self.getOutput("jc").plug + ".upCurve")


	def freezeJoints(self):
		for i in self.joints:
			for ax in "XYZ":
				core.breakConnections(i + ".rotate" + ax)
				core.breakConnections(i + ".translate" + ax)
		for i in self.joints:
			cmds.makeIdentity(i, apply=True, rotate=True)

	def matchSavedJointInfo(self):
		# wat up now swedes
		self.remember("joints", "xform", self.joints, jointMode=True)
		self.remember("joints", "attr", self.joints, transformAttrs=False)
		self.remember("curves", "shape", [self.upCurve.shape, self.mainCurve.shape])
		#print "memory after remember is {}".format(self.memory.serialiseMemory())
		# self.memory.reapplyData("joints", "attr")
		# self.memory.reapplyData("joints", "xform")
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

# lib functions --------
def skinToPoints( points=None, curve=None, name=None):
	""" :param points : list(AbsoluteNode) """
	null = ECA("joint", name=name+"SkinNull")
	mainSkin = cmds.skinCluster(null.node, curve, name=name+"mainSkin",
	                            toSelectedBones=True, skinMethod=1)
	for i in points:
		if not i.nodeType() == "joint":
			continue
		cmds.skinCluster(mainSkin, edit=True, ai=i.transform)
	return { "null" : null,
	         "skin" : mainSkin}