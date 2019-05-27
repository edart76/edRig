from edRig import transform, control
from edRig.layers.datatypes import DimFn
from edRig.layers.pointlayers import PointLayerOp


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