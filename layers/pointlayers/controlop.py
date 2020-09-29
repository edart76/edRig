from maya import cmds
from edRig import control, transform
from edRig.layers.pointlayers import PointLayerOp


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
		self.addSetting(entryName="controlType",
		                options=["curve", "surface", "sliding"],
		                value="curve")
		self.addSetting(entryName="controlCount", value=1),
		self.addSetting(entryName="controlColour",
		                value=(0, 0, 256))

	def execute(self):
		# count = min(self.settings["controlCount"].value, 1)
		# controlType = self.settings["controlType"].value

		self.control = control.FkControl(name=self.opName, layers=count,
		                                 controlType=controlType)

		self.connectInputs()

		self.remember("offset", "xform", self.control.uiOffset)
		self.remember("ctrlShapes", "shape", self.control.shapes)

		self.connectOutputs()


	def showGuides(self):
		"""connects first ui ctrl to uiOffset group of control"""
		#transform.zeroTransforms(self.control.first)
		# cmds.parent(self.control.first, self.control.uiRoot)
		# cmds.parent(self.control.uiOffset, self.control.first, r=True)
		# self.control.markAsGuides()

	def connectInputs(self):
		"""connect driving space to control
		offset not necessary as we recall world transforms just after"""
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