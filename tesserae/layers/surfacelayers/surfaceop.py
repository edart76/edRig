"""basic op for creating surfaces"""
"""ctrl P for function arguments"""

from edRig.tesserae.ops.layer import LayerOp

class SurfaceOp(LayerOp):
	"""build a simple shape and remember it"""

	def defineAttrs(self):
		self.addInput(name="space0D", dataType="0D",
		              desc="parent space for shape")
		self.addOutput(name="out2D", dataType="2D",
		               desc="created surface")