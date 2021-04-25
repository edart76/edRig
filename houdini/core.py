
from edRig import hou
from edRig.lib import python
reload(python)


def returnNode(parent, node_type, node_name):
	""" returns node of name if it exists,
	or creates new node of type """
	if any(i.name() == node_name for i in parent.children()):
		return parent.node(node_name)
	return parent.createNode(node_type, node_name=node_name)


def sortNodes(nodes):
	""" sorts nodes into alphabetical order, basic consistency
	across merges """
	return sorted(nodes, key=lambda x : x.name())

def checkIfMergesDirty(itemsToMerge, existingMerges):
	""" not trying to insert at index or anything, just simple
	check if merges need rebuilt """
	existingPaths = [i.parm("objpath1").evalAsString() for i in existingMerges]
	newPaths = [i.path() for i in itemsToMerge]
	if set(existingPaths) != set(newPaths): # any discrepancy?
		return True
	return False


def addPathParm(node, parmName="path", path=None):
	""" adds path to node, optionally populates it """

	parm = hou.StringParmTemplate(
		name=parmName, label=parmName, num_components=1,
		default_value=path, string_type=hou.stringParmType.NodeReference
	)
	parmGroup = node.parmTemplateGroup()
	parmGroup.addParmTemplate( parm )
	return parm




