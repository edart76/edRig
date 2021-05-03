
"""
functions for building EphRigs from maya nodes
"""

from types import FunctionType
import weakref

from maya import cmds
from maya.api import OpenMaya as om, OpenMayaAnim as oma

import networkx as nx
from tree import Tree

from edRig.ephrig.node import EphNode



nodeObjMap = weakref.WeakValueDictionary()

def getMObject(node):
	uid = cmds.ls(node, uuid=1)
	if nodeObjMap.get(uid):
		return nodeObjMap[uid]
	sel = om.MSelectionList()
	sel.add(node)
	obj = sel.getDependNode(0)
	nodeObjMap[uid] = obj
	return obj


def treeFromSkeleton(rootJnt, nameKey:FunctionType=None):
	""" makes a tree that is very spooky
	key is optional lambda to extract nice name from
	maya node string name
	store MObjects as tree values because we're mad lads
	"""
	mobj = getMObject(rootJnt)
	tree = Tree(name=rootJnt, val=mobj)
	for i in cmds.listRelatives(rootJnt, children=1) or []:
		tree.addChild(treeFromSkeleton(rootJnt))
	return tree

def ephRigFromTree(treeRoot:Tree):
	"""Should really be abstract
	create singly-connected tree-like graph from given tree root


	"""
	master = nx.DiGraph() # master topological graph

	# add EphNodes
	for branch in treeRoot.allBranches():
		node = EphNode(branch.name,
		               graph=master,
		               transformNode=branch.value)
		master.add_node(EphNode)
		branch.node = node # this is fine

	# add edges
	for branch in treeRoot.allBranches():
		if branch.parent:
			master.add_edge(branch.parent.node,
			                branch.node)






