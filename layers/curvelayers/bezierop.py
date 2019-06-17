from edRig.node import AbsoluteNode, ECA
from edRig.tilepile.ops.layer import LayerOp
from edRig import utils, control, curve


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

		self.addInput(name="mid0D", dataType="0D", hType="array",
		              desc="midpoint controls of curve")

		self.addOutput(name="output1D", dataType="1D",
		               desc="output curve")

	def defineSettings(self):
		self.addSetting(entryName="degree", value=3,
		                options=(1, 3))
		self.addSetting(entryName="controlType", value="curve",
		                options=("curve", "surface"))
		self.addSetting(entryName="makeStart", value=True,
		                options=bool)
		self.addSetting(entryName="makeEnd", value=True,
		                options=bool)

	def execute(self):
		"""construct controls at input matrices, then move to position
		create curve from shape"""
		self.controls = []
		curveAttr = self.getInput("input1D")
		midAttr = self.getInput("mid0D")
		if not curveAttr.isConnected():
			curvePlug = curve.makeLine(self.opName + "_crv").shape.outLocal
		else:
			curvePlug = curveAttr.plug

		self.outCrv = curve.makeLine(self.opName + "_outCrv")

		if self.settings["makeStart"]:
			ctrlData = self.makeControl("start", u=0, pointAttr=None,
			                 retrogradeHdl=False)

		for i, val in enumerate(midAttr.getConnectedChildren()):
			u = (1.0 / len(midAttr.getConnectedChildren()) + 2) * (i + 1)
			ctrlData = self.makeControl("mid{}".format(i),
			                            u=u, pointAttr=val)

		if self.settings["makeEnd"]:
			ctrlData = self.makeControl("end", u=0, pointAttr=None,
			                 progradeHdl=False)

		handles = []
		# set up bezier-esque system
		for i, val in enumerate(self.controls):
			self.remember("ctrlOffsets", "xform", val.uiOffset)
			self.remember("ctrlShapes", "shape", val.shapes)

			retro = False if val is self.controls[0] else True
			pro = False if val is self.controls[1] else True

			handlePlugs = self.makeHandles(val, pro, retro, handles)


		self.connectHandles(handles)

	def makeHandles(self, control, pro, retro, handles):
		"""create matrix mults to capture points ahead and behind control"""
		points = ( (1,0,0), (0,0,0), (-1, 0, 0))
		for i, val in (pro, True, retro):
			if val:
				pmm = ECA("pointMatrixMult")
				pmm.con(control.world, pmm+".inMatrix")
				pmm.set("inPoint", points[i])
				handles.append(pmm+".output")


	def connectHandles(self, pointPlugs):
		"""connects locators directly to control points of curve
		resamples curve if necessary"""
		degree = self.settings["degree"]
		curve.rebuildCurve(self.outCrv, spans=len(pointPlugs), ch=False,
		                   degree=degree)
		for i, val in enumerate(pointPlugs):
			# expects triples
			self.outCrv.con(val, self.outCrv+".controlPoints[{}]".format(i))



	def makeControl(self, name, u=0.5, pointAttr=None,
	                progradeHdl=True, retrogradeHdl=True):
		"""priority goes 0D input > 1D input > none
		prograde is defined as positive X"""
		ctrl = control.FkControl(self.opName + "_startCtrl",
		                              layers=1,
		                              controlType=self.settings["controlType"])
		ctrl.first
		self.controls.append(ctrl)
		return ctrl






