from maya import cmds
import maya.api.OpenMaya as om

from edRig import scene, core

class Material(object):
	"""base class for materials idk"""
	pass


def applyMaterialNode(matNode, target):
	"""applies material represented by node to target dag"""
	sg = getSGfromShader(matNode)
	if not sg:
		raise RuntimeError("sg not found for {}".format(matNode))
	cmds.sets([target], e=True, forceElement=sg)
	

def getSGfromShader(shader=None):
	if shader:
		if cmds.objExists(shader):
			sgq = cmds.listConnections(shader, d=True, et=True, t='shadingEngine')
			if sgq: 
				return sgq[0]

	return None


