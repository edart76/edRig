# layers working with transforms, hierarchy, point data, joints

from edRig import core, transform, attrio, control
from maya import cmds
from edRig.layers.datatypes import Point
from edRig.tilepile.ops.layer import LayerOp
import maya.api.OpenMaya as om
from edRig import control, core


class PointLayerOp(LayerOp):
	# don't know if this much inheritance is necessary
	# but better safe than sorry
	def __init__(self, name):
		super(PointLayerOp, self).__init__(name=name)
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


class ControlOp(PointLayerOp):
	"""creates an Fk control for user interaction
	no inputs"""
	def __init__(self, name):
		super(ControlOp, self).__init__(name)

	def defineAttrs(self):
		self.addInput(name="driverSpace", dataType="0D",
		              desc="space that control follows")

		self.addOutput(name="controlOutput", dataType="0D",
		               desc="output local space matrix from control")
		self.addOutput(name="controlOutputWorld", dataType="0D",
		               desc="output world space matrix from control")
		self.addOutput(name="controlUi", dataType="message",
		               desc="control ui shapes to be passed forwards")

	# def plan(self):
	# 	self.start = self.makeStarter(name=self.opName+"ctrlStarter", d="0D")
	#
	# def build(self):
	# 	self.control = control.FkControl(self.opName)
	# 	transform.matchXforms(source=self.start, target=self.control.uiOffset)
	# 	self.control.makeUi()
	# 	self.getInput("controlOutput").value = self.control.output
	# 	self.getInput("controlUi").value = Point(self.control.localOutput)

	def execute(self):
		self.control = control.FkControl(self.opName)
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
		cmds.parent(self.control.first["ui"], self.control.uiRoot)
		cmds.parent(self.control.uiOffset, self.control.first["ui"])

	def connectOutputs(self):
		"""connect plugs"""
		cmds.connectAttr(self.control.uiRoot+".message",
		                 self.getOutput("controlUi").plug)
		cmds.connectAttr(self.control.outputPlug,
		                 self.getOutput("controlOutput").plug)
		cmds.connectAttr(self.control.worldOutputPlug,
		                 self.getOutput("controlOutputWorld").plug)




