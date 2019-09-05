# wrappers for weight io, getting deformers in history, etc

from edRig import core
from edRig.node import ECA, AbsoluteNode
from maya import cmds


class SkinCluster(AbsoluteNode):

	@property
	def influenceMap(self):
		"""return dict of index : influence
		:returns dict"""





def isDeformer(test):
	"""checks if test is some kind of deformer"""
	return "geometryFilter" in cmds.nodeType(test, inherited=True)

def addToDeformer(geo, deformer):
	""" _ """
	cmds.deformer(deformer, e=True, geometry=geo)

def getDeformers(geo):
	""":returns list of deformers in history, beginning with earliest"""
	print "ls his {} {}".format(geo, cmds.listHistory(geo))
	return [i for i in cmds.listHistory(geo) if isDeformer(i)]


