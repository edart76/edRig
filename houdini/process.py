
""" testing system to automatically build and run given houdini scene
 on given file inputs (and potentially later with given parametres)
 """

# later we could specify parametre presets in this form
specParametres = {
	"myHDA_1" : {"paramA" : 3}
}
# for now stick to specific houdini file

from edRig import hou

class HoudiniSceneProcess(object):
	""" wrapper representing a houdini scene
	for processing information
	for now consider only geometry inputs and outputs

	initialised within a live instance of houdini
	"""

	def __init__(self):
		print(self.inputNodes())

	def inputNodes(self):
		"""return list of file nodes in inputs"""
		return hou.node("/obj/INPUTS").children()


	def sceneInputs(self):
		"""return dict of {inputName : nodePath}
		for each node and path
		"""



