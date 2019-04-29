# operations for listing, grouping, adding to sets etc
from maya import cmds
#from edRig.core import ECA, AbsoluteNode
#import maya.api.OpenMaya as om

class Globals(object):
	"""holder for various singleton nodes and values"""
	nodes = {
		"ctrlBlue" : {
			"type" : "colorConstant",
			"attrs" : {
				"inColor" : (0,0,1) # pure blue
			}
		},
		"ctrlYellow": {
			"type": "colorConstant",
			"attrs" : {
				"inColor" : (1,1,0)
			}
		},
		"ctrlCyan": {
			"type": "colorConstant",
			"attrs": {
				"inColor": (0, 1, 1)
			}
		},
	}

	def invokeNode(self, nodeDict, name=None):
		"""creates a node from globals library or lists and returns it"""
		name = name or nodeDict["name"]
		test = cmds.ls(name)
		if test:
			return test[0]
		node = cmds.createNode(nodeDict["type"], name=name)
		if "attrs" in nodeDict:
			for k, v in nodeDict["attrs"].iteritems():
				cmds.setAttr(k, v)
		return node

	def __getattr__(self, item):
		if item in self.nodes:
			return self.invokeNode(self.nodes[item], name=item)
		return super(Globals, self).__getattr__(item)




def listTopNodes():
	return set(cmds.ls("|*", recursive=True))