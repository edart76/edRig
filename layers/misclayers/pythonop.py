
from edRig.tesserae.ops.layer import LayerOp



class PythonOp(LayerOp):
	"""base class for text-editor python snippets"""


	def defineAttrs(self):
		self.addInput(name="code", dataType="text")

	def __init__(self, *args, **kwargs):
		super(PythonOp, self).__init__(*args, **kwargs)
		self.text = ""

	def execute(self):
		text = self.getInput("code")
		scope = (locals(), globals())
		exec text in scope

