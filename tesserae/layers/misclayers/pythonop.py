
from edRig.tesserae.ops.layer import LayerOp

from edRig import cmds, om


class PythonOp(LayerOp):
	"""
	op allowing execution of arbitrary code
	from files
	or in very worst case text snippet
	"""


	def defineAttrs(self):
		self.addInput(name="code", dataType="text")

	def __init__(self, *args, **kwargs):
		super(PythonOp, self).__init__(*args, **kwargs)
		self.text = ""

	def execute(self):

		# define scope in which to execute code
		scopeVars = {"cmds" : cmds,
		             "om" : om,
		             "op" : self}

		text = self.getInput("code")

		scope = (locals(), globals())
		exec(text, scope)

