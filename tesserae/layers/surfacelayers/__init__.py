from edRig.tesserae.ops.layer import LayerOp

class MeshOp(LayerOp):
	"""create and remember tech meshes"""

	def defineAttrs(self):
		self.addInput(name="input0D", dataType="0D",
		               desc="input transform for mesh")
		self.addOutput(name="output2D", dataType="2D",
		               desc="output created mesh")

