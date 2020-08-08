
""" import stuff from scene or file """
import os
from edRig import cmds, om, core, pipeline, COMMON_PATH, AbsoluteNode, ECA, scene
from edRig.tesserae.ops.layer import LayerOp
from edRig.lib.python import AbstractTree

from edRig.tesserae import graph

# direct ps2 import, until it becomes a problem
from PySide2 import QtWidgets


class SourceOp(LayerOp):
	""" op to load or import resources from scene or file
	1 op per file source for now """

	def defineSettings(self):
		"""define which files should be loaded
		file : path
		+ - transformName : 2D
		+ - transformName : 0D
		"""
		self.settings["path"] = "/"
		self.settings["mode"] = "file"
		self.settings("mode").options = ["file", "folder", "scene"]

		# let user specify hierarchy for procedurally imported objects
		self.settings["hierarchy"] = None

		# node plug output is by default the same name as geometry
		self.settings["io.C_body"] = "2D"
		self.settings["io.C_body.overrideNode"] = "C_body"

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

		if self.s["mode"] == "scene":
			self.log("sourcing from scene")
		else:
			if self.s["mode"] == "file":
				self.loadFile(self.s["path"])
			elif self.s["mode"] == "folder":
				self.loadFolder(self.s["path"])

		for plug in self.s("io").branches:
			self.sourceNodes(plug.name, plug.value)

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
		for i in "mb", "ma", "obj", "fbx":
			path = pipeline.checkSuffix(path, suffix=i)
			if pipeline.checkFileExists(path):
				found = True
				break
		if not found:
			self.log( "no source found at {}".format(path) )
			return

		print(path)
		scene.importModel(path)

	def loadFolder(self, path, pattern=None):
		""" loads all model files within folder """
		path = pipeline.convertRootPath(path, toAbsolute=True)
		files = [i for i in os.listdir(path) if
		         os.path.isfile(os.path.join(path, i))]
		for i in files:
			scene.importModel(os.path.join(path,i) )


	@property
	def assetPath(self):
		""" path to current asset root """
		if graph():
			return graph().asset.path
		return COMMON_PATH

	def setFilePath(self):
		""" sets file path with gui menu """
		#print("asset path {}".format(self.assetPath))
		if self.settings["mode"] == "file":
			path = QtWidgets.QFileDialog.getOpenFileName(
				caption="open file",
				dir=self.assetPath)[0]
			# returns the path and the filter for some reason
		elif self.settings["mode"] == "folder":
			path = QtWidgets.QFileDialog.getExistingDirectory(
				caption="open folder",
				dir=self.assetPath)
			print("folder path {}".format(path))
		else: path = ""
		if not path:
			self.log("no path given")
			return

		path = pipeline.convertRootPath(path, toRelative=True)
		self.settings["path"] = path
		self.sync()

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





