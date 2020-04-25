
from edRig import hou


def returnNode(parent, node_type, node_name):
	""" returns node of name if it exists,
	or creates new node of type """
	if any(i.name() == node_name for i in parent.children()):
		return parent.node(node_name)
	return parent.createNode(node_type, node_name=node_name)

def networkBoxFromComment(parent, comment=""):
	boxes = parent.networkBoxes()
	if not boxes: return None
	for i in boxes:
		if i.comment() == comment:
			return i