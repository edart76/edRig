from edRig.node import AbsoluteNode, ECA
from edRig.tilepile.ops.layer import LayerOp
class BezierOp(LayerOp):
	"""basis of all better ik splines -
	controls for curves
	also doubles as curve-from-points when degree is 1"""

	def defineAttrs(self):
		self.addInput(name="input1D", dataType="1D",
		              desc="curve to drive with bezier controls (optional)" )
		self.addInput(name="start0D", dataType="0D",
		              desc="point driving start of curve")
		self.addInput(name="end0D", dataType="0D",
		              desc="point driving end of curve")

		self.addOutput(name="output1D", dataType="1D",
		               desc="output curve")

	def defineSettings(self):
		self.addSetting(entryName="degree", value=3,
		                options=(1, 3))
		self.addSetting(entryName="controlType", value="curve",
		                options=("curve", "surface"))

	def execute(self):
		"""construct controls at input matrices, then move to position
		create curve from shape"""

		driverMat = getMatrixFromPlug(self.getInput("start0D").plug)


