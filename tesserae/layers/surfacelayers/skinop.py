
from edRig.tesserae.ops.layer import LayerOp
from edRig.layers.surfacelayers import MeshOp

from edRig import cmds, om


class SkinOp(MeshOp):
	"""creates a skincluster on a mesh and saves the weights
	in future should work for other dimensions, but that gets tricky
	this sounds like the easiest thing in the world but it's actually
	hell
	the correct way to use this is one individual skin per driver group"""
	GPUable = True

	data = {
		"bindMethod" : {
			"options" : ["fromSaved", "fast", "quality"],
			"value" : "fromSaved" }

	}

	def __init__(self, name):
		super(SkinOp, self).__init__(name=name)
	# self.addInputWithAction(suffix="_in", datatype="nD",
	#                         desc="additional driver of the skincluster")

	def defineAttrs(self):
		self.addOutput(name="outSurface", dataType="2D",
		               desc="output from skincluster")

		self.addInput(name="inSurface", dataType="2D",
		              desc="surface to use for skincluster")
		self.addInput(name="inverseSpace", dataType="0D",
		              desc="(optional) parent space of influence, to make skin local")
		self.addInput(name="influence_in", dataType="nD", hType="array",
		              desc="driver of the skincluster")

	def defineSettings(self):
		"""ooh boy"""
		# first the path to the weight file to use
		self.addSetting(entryName="weightPath",
		                value="(assetpath)/assemblyData/weights/(opName)")
		# every op has only one file for storing weights
		# later with images maps are saved as different channels



	def refreshIo(self, controller=None, attrChanged=None):
		"""add array behaviour for influence inputs
		NOOO don't do that"""
		pass

	# def plan(self):
	# 	pass
	# no plan for skincluster

	def execute(self):
		"""
		get inputs and surfaces as correct representations
		make skincluster
		remember weights of individual influences in sequence
		LATER, enable painting mask per influence to be more procedural
		currently this is completely vulnerable to joint changes -
		decide on your skeleton before doing this.
		FOR NOW, save the proper sequence, and check
		if that still matches the input"""

		# APPARENTLY, ngSkinTools has full io support including layers.
		# if masks are too tricky, pursue this

		inMeshPlug = self.getInput("inSurface").plug
		targetMesh = self.ECA("mesh", n=self.opName+"_proxy")

		self.liveInfs = self.getLiveInfluences()

		self.skin = self.makeSkin(targetMesh)
		print("self.skin is {}".format(self.skin))


	# above line will do whatever conversion it has to and create a new
	# shape node as active - use this to make the skin
	# worry about GPU chaining later
	# worry about it in abject terror

	def getLiveInfluences(self):
		"""unpacks the node's inputs and converts each to joints"""
		infDict = {}
		for i, val in enumerate(self.searchInputs("_in")):
			if not val.value:
				continue
			infName = val.name.split("_")[0]
			infDict[infName] = []
			if val.datatype == "0D":
				infDict[infName][0] = val.value.asJoint()
			elif val.datatype == "1D" or val.datatype == "2D" or val.datatype == "nD":
				infs = [n.asJoint() for n in val.value.getPoints()]
				for n, inf in enumerate(infs):
					infDict[infName][n] = inf
			else:
				raise RuntimeError("datatype not supported by skinOp!")
		return infDict

	"""so IN THEORY, it is possible to do enough runtime processing on skin weights
	to make them reasonably robust to changes in influence resolution.
	consider that any weights painted beyond the influence's true form (ie
	outside the boundaries of a driving curve or surface) can probably be assumed to
	belong to those boundaries no matter the internal resolution - the only weights
	requiring interpolation SHOULD be those within influence object. The test is
	simple - if a normal ray from anywhere on the object passes close to the point,
	that point is considered within the influence.

	actual skincluster node indices considered malleable - the indices don't need to be
	reapplied in the right order, but every influence's weights should be 
	associated with it when stored
	at the lowest level, query the names of each skin influence based on name - it's
	fine as long as we don't act on that again
	"""

	def makeSkin(self, target):
		"""makes an empty skincluster on target shape"""
		temp = cmds.createNode("joint", n=self.opName+"_identity")
		return cmds.skinCluster(temp, target)


