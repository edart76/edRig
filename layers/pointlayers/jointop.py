""" create a joint chain, giving 0D outputs """
from edRig.tesserae.ops.layer import LayerOp

class JointOp(LayerOp):
	""" boom, the end, start over
	again """

	def defineAttrs(self):
		self.addInput(name="parent", dataType="nD",
		              desc="parent input")
		""" """

		self.addOutput(name="jc", dataType="1D",
		               desc="static output jointcurve")

		# point array
		array = self.addOutput(name="points", dataType="0D",
		               hType="array", desc="output points")
		array.setChildKwargs(dataType="0D", desc="output point")


	def defineSettings(self):
		self.settings["joints"]["jointA"] = None


	def matchOutputsToSettings(self):
		jointTree = self.settings["joints"]
		outputs = jointTree.keys()
		pointPlug = self.getOutput("points")
		specList = [ {"name" : i} for i in outputs]
		pointPlug.matchArrayToSpec(spec=specList)


	def execute(self):

		self.updateOutputs()
