
""" import stuff from scene or file """

from edRig import cmds, om, core, pipeline, COMMON_PATH
from edRig.tesserae.ops.layer import LayerOp

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
		self.settings["fileA.C_body"] = "2D"

	def defineAttrs(self):
		pass

	def onSync(self):
		""" don't try to change datatype of created attrs """
		spec = {}

		for i in self.settings.branches:
			for n in i.branches:
				attrName = n.name
				attrType = n.value

				# move this to a common function
				if not self.getOutput(attrName):
					self.addOutput(name=attrName,
					               dataType=attrType)
				spec[attrName] = attrType

		for i in self.outputs:
			if spec.get( i.name ) != i.dataType:
				self.removeAttr( i.name, role="output")

	# --- execution ---
	def execute(self):
		for i in self.settings.branches:
			if i.value == "scene":
				self.log("sourcing {} from scene".format(i.name))
			else:
				self.sourceFile(i.value)


	# file io
	def sourceFromScene(self, nodeName):
		""" load node directly from """
		if not cmds.ls( nodeName ):
			raise RuntimeError( "given node {} does not exist in scene"
			                    .format(nodeName))

	def sourceFile(self, path):
		""" import 3d file """
		path = pipeline.convertRootPath(path, toAbsolute=True)
		for i in "mb", "ma", "obj":
			path = pipeline.checkSuffix(path, suffix=i)
			if pipeline.checkFileExists(path):
				break

		# reference
		cmds.file( path, i=1 )






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





