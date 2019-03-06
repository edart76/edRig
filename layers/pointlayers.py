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
		self.addOutput(name="point", dataType="0D",
		               desc="output point")

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
		self.addOutput(name="controlUi", dataType="custom",
		               desc="control ui shape to be passed forwards")

	def plan(self):
		self.start = self.makeStarter(name=self.opName+"ctrlStarter", d="0D")

	def build(self):
		self.control = control.FkControl(self.opName)
		transform.matchXforms(source=self.start, target=self.control.controlGrp)
		self.control.makeUi()
		self.getInput("controlOutput").value = self.control.output
		self.getInput("controlUi").value = Point(self.control.localOutput)






