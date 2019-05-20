# layers working with transforms, hierarchy, point data, joints

from edRig import core, transform, attrio, control, attr, control
from maya import cmds
from edRig.layers.datatypes import Point, DimFn
from edRig.tilepile.ops.layer import LayerOp
import maya.api.OpenMaya as om


class PointLayerOp(LayerOp):
	# don't know if this much inheritance is necessary
	# but better safe than sorry
	def __init__(self, *args, **kwargs):
		super(PointLayerOp, self).__init__(*args, **kwargs)
		print "PointLayerOp instantiated"

class PointOp(PointLayerOp):
	"""creates a 0D point
	:/
	"""

	def defineAttrs(self):
		self.addInput(name="parent", dataType="nD",
		              desc="driver of the point")
		self.addOutput(name="pointLocal", dataType="0D",
		               desc="output point local transforms")
		self.addOutput(name="pointWorld", dataType="0D",
		               desc="output point local transforms")

	def execute(self):
		self.point = self.ECA("joint", name=self.opName+"_point")
		self.offsetGrp = self.ECA("transform", name=self.opName+"_offset")

		# if input is point, match to it on first
		parent = self.getInput("parent")
		if parent.connections: # this really isn't legal but whatever
			if parent.connections[0].sourceAttr.dataType == "0D":
				matchMat = transform.matrixFromPlug(parent.plug)
				transform.matchMatrix(self.point, matchMat)

		self.remember("pointPos", "xform", self.point)

		# drive with input
		inputPlug = DimFn.getPoint(on=self.getInput("parent").plug, near=self.point)

		# later remove offset group and construct offset
		transform.decomposeMatrixPlug(inputPlug, self.offsetGrp)
		#
		cmds.parent(self.point, self.offsetGrp)

		cmds.connectAttr(self.point+".matrix",
		                 self.getOutput("pointLocal").plug)
		cmds.connectAttr(self.point+".worldMatrix[0]",
		                 self.getOutput("pointWorld").plug)
		# currently local will of course give nothing

	def showGuides(self):
		ctrl = control.FkControl(self.opName+"_guide")
		transform.matchXforms(ctrl.first["ui"], self.point)
		cmds.parent(self.point, ctrl.first["ui"])

class ControlOp(PointLayerOp):
	"""creates an Fk control for user interaction
	no inputs"""

	def defineAttrs(self):
		self.addInput(name="driverSpace", dataType="0D",
		              desc="space that control follows")

		self.addOutput(name="controlOutput", dataType="0D",
		               desc="output local space matrix from control")
		self.addOutput(name="controlOutputWorld", dataType="0D",
		               desc="output world space matrix from control")
		self.addOutput(name="controlUi", dataType="message",
		               desc="control ui shapes to be passed forwards")

	def defineSettings(self):
		"""set options for control type"""
		self.addSetting(entryName="controlType", options=["curve", "surface"],
		                value="curve")
		self.addSetting(entryName="controlCount", value=1)

	def execute(self):
		count = self.settings["controlCount"].value
		controlType = min(self.settings["controlType"].value, 1)
		self.control = control.FkControl(self.opName, layers=count,
		                                 controlType=controlType)

		self.connectInputs()

		self.remember("offset", "xform", self.control.uiOffset)
		self.remember("ctrlShapes", "shape", self.control.shapes)

		self.connectOutputs()
		"""
		self.remember("joints", "xform", self.joints, jointMode=True)
		self.remember("joints", "attr", self.joints, transform=False)
		self.remember("curves", "shape", [self.upCurve.shape, self.mainCurve.shape])
		"""

	def showGuides(self):
		"""connects first ui ctrl to uiOffset group of control"""
		transform.zeroTransforms(self.control.first["ui"])
		cmds.parent(self.control.first["ui"], self.control.uiRoot)
		cmds.parent(self.control.uiOffset, self.control.first["ui"])

	def connectInputs(self):
		"""connect driving space to control
		offset not necessary as we recall world transforms just after"""

		# attr.con(self.getInput("driverSpace").plug,
		#          self.control.uiRoot)
		transform.decomposeMatrixPlug(self.getInput("driverSpace").plug(),
		                              self.control.uiRoot)

	def connectOutputs(self):
		"""connect plugs"""
		cmds.connectAttr(self.control.uiRoot+".message",
		                 self.getOutput("controlUi").plug())
		cmds.connectAttr(self.control.outputPlug,
		                 self.getOutput("controlOutput").plug())
		cmds.connectAttr(self.control.worldOutputPlug,
		                 self.getOutput("controlOutputWorld").plug())


class IkOp(PointLayerOp):
	"""sets up ik behaviour"""

	def defineAttrs(self):
		self.addInput(name="base", dataType="0D",
		              desc="driver space for base")
		self.addInput(name="mid", dataType="0D", # needed for length
		              desc="driver space for mid (recommend similar as base)")
		self.addInput(name="end", dataType="0D",
		              desc="driver space for end effector")
		self.addInput(name="pv", dataType="0D",
		              desc="driver space for pole vector")
		# these can all be nD, and convert implicitly from higher Ds, but
		# it's really not a good idea for now

		self.addOutput(name="base", dataType="0D",
		               desc="output first ik segment")
		self.addOutput(name="mid", dataType="0D",
		               desc="output second ik segment")
		self.addOutput(name="tangent", dataType="0D",
		               desc="tangent point at ik hinge")

	def execute(self):
		"""once op settings are working, this will include mode to switch
		to fully trig-based ik"""
		self.base = self.ECA("joint", self.opName+"_ikBase")
		self.mid = self.ECA("joint", self.opName + "_ikMid")
		self.end = self.ECA("joint", self.opName + "_ikEnd")

		self.handleDriver = self.ECA("transform", self.opName+"_handleDriver")
		self.poleDriver = self.ECA("transform", self.opName+"_poleDriver")


		memoryNames = ["base", "mid", "end"]
		joints = [self.base, self.mid, self.end]

		# match to inputs, then remember position
		for name, joint in zip(memoryNames, joints):
			plug = self.getInput(name).plug
			matchMat = transform.matrixFromPlug(plug)
			transform.matchMatrix(joint, matchMat)

			self.remember(infoName=name, infoType="xform")

		# parent up ik like a basic boi
		cmds.parent(self.end, self.mid)
		cmds.parent(self.mid, self.base)

		# make pole marker
		self.poleMarker = self.makePoleMarker()

		# make ik
		self.handle = self.makeIk()

		# constrain handle driver space
		transform.decomposeMatrixPlug(self.getInput("end").plug,
		                              self.handleDriver)
		"""this seems overly simplistic but trust me it's all you need,
		i've thought it through"""
		transform.decomposeMatrixPlug(self.getInput("pv").plug,
		                              self.poleDriver)

		# set outputs
		cmds.connectAttr(self.base+".worldMatrix[0]",
		                 self.getOutput("base").plug)
		cmds.connectAttr(self.mid+".worldMatrix[0]",
		                 self.getOutput("mid").plug)

	def makePoleMarker(self):
		"""creates a transform at optimal range for being a pole"""

	def makeIk(self):
		"""creates an ik handle through joints"""
		name = self.opName+"_hdl"
		hdl = cmds.ikHandle(n=name, sj=self.base, ee=self.end, sol="ikRPsolver")
		return hdl





