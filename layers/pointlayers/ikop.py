from maya import cmds

from edRig import transform, utils
from edRig.layers.pointlayers import PointLayerOp


class IkOp(PointLayerOp):
	"""sets up ik behaviour"""

	def defineAttrs(self):
		self.addInput(name="base", dataType="0D",
		              desc="driver space for base")
		self.addInput(name="mid", dataType="0D", # needed for length
		              desc="driver space for mid (recommend similar as base)")
		self.addInput(name="end", dataType="0D",
		              desc="driver space for end effector")
		self.addInput(name="pv", dataType="0D",
		              desc="driver space for pole vector")
		# these can all be nD, and convert implicitly from higher Ds, but
		# it's really not a good idea for now

		self.addOutput(name="base", dataType="0D",
		               desc="output first ik segment")
		self.addOutput(name="mid", dataType="0D",
		               desc="output second ik segment")
		self.addOutput(name="tangent", dataType="0D",
		               desc="tangent point at ik hinge")

	def buildNodes(self):
		"""make all necessary nodes for ik"""
		self.base = self.ECA("joint", self.opName + "_ikBase")
		self.mid = self.ECA("joint", self.opName + "_ikMid")
		self.end = self.ECA("joint", self.opName + "_ikEnd")

		self.handleDriver = self.ECA("transform", self.opName + "_handleDriver")
		self.poleDriver = self.ECA("transform", self.opName + "_poleDriver")

		self.baseOffset = self.ECA("transform", self.opName+"_baseOffset")

	def setupBase(self):
		"""get point using recalled base position"""
		self.constrainToInput("base", target=self.baseOffset,
		                      closestPoint=self.base)
		self.base.parentTo(self.baseOffset)

	def setupChain(self):
		"""make intermediate joints"""
		# parent up ik like a basic boi
		self.end.parentTo(self.mid)
		self.mid.parentTo(self.base)

	def execute(self):
		"""once op settings are working, this will include mode to switch
		to fully trig-based ik"""
		#self.relative = self.settings["relative"]
		self.relative = False

		self.buildNodes()

		memoryNames = ["base", "mid", "end", "pv"]
		joints = [self.base, self.mid, self.end, self.poleDriver]

		self.initPositions(memoryNames, joints)

		"""new design pattern - remember worldspace position,
		constrain offset group, parent target,
		remember local space if necessary"""

		for name, joint in zip(memoryNames, joints):
			self.remember(infoName=name, infoType="xform", relative=None,
		              nodes=joint)

		self.setupBase()
		self.setupChain()




		# make pole marker
		self.poleMarker = self.makePoleMarker()

		# make ik
		self.handle = self.makeIk()

		# constrain handle driver space
		transform.decomposeMatrixPlug(self.getInput("end").plug,
		                              self.handleDriver)
		"""this seems overly simplistic but trust me it's all you need,
		i've thought it through"""
		transform.decomposeMatrixPlug(self.getInput("pv").plug,
		                              self.poleDriver)

		# set outputs
		cmds.connectAttr(self.base+".worldMatrix[0]",
		                 self.getOutput("base").plug)
		cmds.connectAttr(self.mid+".worldMatrix[0]",
		                 self.getOutput("mid").plug)


	def makeIk(self):
		"""creates an ik handle through joints"""
		name = self.opName+"_hdl"
		hdl = cmds.ikHandle(n=name, sj=self.base, ee=self.end, sol="ikRPsolver")
		return hdl


	def initPositions(self, names, joints):
		"""try to match joints to input points, if op is built for first"""
		memoryNames = ["base", "mid", "end"]
		joints = [self.base, self.mid, self.end]
		for joint, name in zip(joints, memoryNames):
			try:
				transform.matchMatrix(joint, self.getInput(name).plug)
			except:
				pass
