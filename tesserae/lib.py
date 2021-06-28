
from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial
import traceback
from edRig.lib.python import AbstractTree
from edRig.tesserae.action import Action


"""frequently used methods and techniques"""
"""signal implementation from codeRecipe 576477"""


class GeneralExecutionManager(object):
	"""placeholder"""
	def __init__(self, real):
		self.real = real

	@staticmethod
	def printTraceback(tb_type, tb_val, tb):
		traceback.print_exception(tb_type, tb_val, tb)



def mergeActionTrees(trees:List[AbstractTree])->AbstractTree[Action]:
	"""given a list of trees with actionItems as values,
	OR DICTS OF ACTION ITEMS as values,
	merge corresponding actions into single"""

	resultTree = AbstractTree("actions")

	keySet = set()
	for tree in trees:
		keySet.update(set(tree.keys()))


	# iterate over all trees to combine their keys
	# if a key leads to a tree branch,
	# it will override any leaves of the same name
	for key in keySet:
		keyChildren = [] # any branches used by this key
		for tree in trees:
			if not key in tree.keys():
				continue
			# what if tree has depth?
			if tree(key).branches:
				keyChildren.append(tree(key))
				continue

			if not isinstance(tree[key], Action):
				continue

			if not resultTree.get(key):
				resultTree[key] = tree[key]
			else:
				resultTree[key].addAction(tree[key])

		if keyChildren:
			childBranch = mergeActionTrees(keyChildren)
			childBranch.name = key
			resultTree.addChild(childBranch)
	return resultTree



