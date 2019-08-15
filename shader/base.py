# dcc agnostic, high-level system for blending and appyling
# shader and material layers
from edRig import COMMON_PATH
from edRig.structures import FilePathTree, Completer

matPrefs = {
	"albedo" : "alb",
	"specular" : "spc",
	"roughness" : "oof",
	"metalness" : "mtl",
	"emissive" : "ems",
	"subsurface" : "sss",
	"anisotropy" : "iso",
	"iridescence" : "iri"
}


class MaterialTree(object):
	"""end representation of a material map set"""
	def __init__(self, materialName="blankMat", path=COMMON_PATH):
		self.matName = materialName
		self.channels = {} # albedo, spec, roughness, not rgb
		self.files = FilePathTree(path).materials
	pass

class MaterialLayer(object):
	"""components of a material tree"""
	def __init__(self, parent, name="newLayer"):
		self.parent = parent
		self.matName = parent.matName
		self.layerName = name

class MaterialTypeCompleter(Completer):
	"""returns list of all current material folders"""
