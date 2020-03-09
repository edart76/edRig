
""" import stuff from scene or file """

from edRig import cmds, om, core, pipeline, COMMON_PATH, AbsoluteNode, ECA
from edRig.tesserae.ops.layer import LayerOp
from edRig.lib.python import AbstractTree

from edRig.tesserae import graph




class SourceOp(LayerOp):
	""" op to load or import resources from scene or file
	1 op per file source for now """

	def defineSettings(self):
		"""define which files should be loaded
		file : path
		+ - transformName : 2D
		+ - transformName : 0D
		"""
		self.settings["fileA"] = "/"
		#self.settings["fileA.C_body"] = "2D"
		self.settings["fileA.body"] = "C_body_mesh"
		self.settings["fileA._version"] = "latest"

	def defineAttrs(self):
		pass

	def onSync(self):
		""" don't try to change datatype of created attrs """
		spec = {}

		for i in self.settings.branches:
			for n in i.branches:
				attrName = n.name
				#attrType = n.value
				attrType = "nD"

				if attrName == "_version" :
					continue

				# move this to a common function
				if not self.getOutput(attrName):
					self.addOutput(name=attrName,
					               dataType=attrType)
				spec[attrName] = attrType

		for i in self.outputs:
			if spec.get( i.name ) != i.dataType:
				self.removeAttr( i.name, role="output")

	def __init__(self, *args, **kwargs):
		super(SourceOp, self).__init__(*args, **kwargs)
		self.addAction(func=self.setFilePath, name="choose file")

	# --- execution ---
	def execute(self):
		for i in self.settings.branches:
			if i.value == "scene":
				self.log("sourcing {} from scene".format(i.name))
			else:
				self.loadFile(i.value, version=i["_version"])
			for n in i.branches:
				if n.name == "_version":
					continue
				self.sourceNodes(n.name, n.value)

	# connecting nodes from scene
	def sourceNodes(self, outputName="output", nodeName=""):
		if not cmds.ls(nodeName):
			self.log("no node found of name {}, skipping source".format(nodeName))
			return None
		node = AbsoluteNode( nodeName )

		if node.shape:
			node = node.shape
			self.log("node {}".format(node))
			self.log(" node isShape {}".format(node.isShape()))
			self.log("node shape {}".format(node.shape) )
			dataType = self.dataTypeForNodeType(node.shape.nodeType())
		else:
			dataType = "0D"
		""" no sophisticated guessing for input nodes
		if it has a shape, you want the shape """

		sourcePlug = node.outWorld

		outputPlug = self.getOutput(outputName).plug
		AbsoluteNode.con(sourcePlug, outputPlug)



	# file io
	def sourceFromScene(self, nodeName):
		""" load node directly from """
		if not cmds.ls( nodeName ):
			raise RuntimeError( "given node {} does not exist in scene"
			                    .format(nodeName))

	def loadFile(self, path, version="latest"):
		""" import 3d file """
		path = pipeline.convertRootPath(path, toAbsolute=True)
		found = False
		for i in "mb", "ma", "obj":
			path = pipeline.checkSuffix(path, suffix=i)
			if pipeline.checkFileExists(path):
				found = True
				break
		if not found:
			self.log( "no source found at {}".format(path) )
			return

		if version == "latest":
			path = self.getLatestVersion(path)
		# reference
		cmds.file( path, i=1 )

	@property
	def assetPath(self):
		""" path to current asset root """
		# if graph:
		# 	return graph.asset.path
		return COMMON_PATH

	def setFilePath(self):
		""" sets file path with gui menu """
		#path = fileDialog(defaultPath=self.assetPath)
		path = None
		if not path:
			return
		path = pipeline.convertRootPath(path, toRelative=True)
		self.settings["fileA"] = path

	def getLatestVersion(self, path):
		""" returns the latest v*** version in given folder """
		return pipeline.getLatestVersions(versions=1, path=path)[0]






""" a more advanced version of this will work by asset, and
dynamically create a corresponding settings tree
entries can then be enabled and disabled

eg
character
	+ - costume
		+ - buttons : 0D array
		+ - cloth : 2D
		+ - final : 2D
	+ - body
		+ - L_eye : 0D
		+ - R_eye : 0D
		+ - final : 2D
		
etc

this can be neatly mirrored in the export,
defining elements of the 3d scene to be exposed as asset
plugs


 """





