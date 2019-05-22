# wrappers for weight io, getting deformers in history, etc

from edRig import core
from maya import cmds

def addSelectedToDeformer(geo, deformer):
	""" _ """
	cmds.deformer(deformer, e=True, geometry=geo)
