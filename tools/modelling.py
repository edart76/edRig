from __future__ import print_function
from maya import cmds
from edRig import deformer, AbsoluteNode, ECA, dynamics, muscle
from edRig.tools.ui.setup import UiTool
from edRig.lib.python import getUserInput

#### deformers
@UiTool
def addSelectedToDeformer(sel):
	"""check through selection to see if there are deformers
	if not get deformer in first geo history and use that"""
	targetDeformer = None
	sel = [AbsoluteNode(i)for i in sel]
	sel = [i.shape for i in sel if i.isDag()]
	print("sel {}".format(sel))
	if not sel:
		print("nothing selected")
		return
	selDeformers = [i for i in sel if deformer.isDeformer(i)]
	print("selDeformers {}".format(selDeformers))
	if selDeformers:
		targetDeformer = selDeformers
	else:
		for i in sel:
			targetDeformer = deformer.getDeformers(i)
			print("i getDeformer {}".format(targetDeformer))
			if targetDeformer:
				break
	if not targetDeformer:
		print("no deformer found")
		return
	targetDeformer = targetDeformer[0]
	for i in [n for n in sel if not deformer.isDeformer(n)]:
		deformer.addToDeformer(i, targetDeformer)

#### shape stuff
@UiTool
def makeShapeLayer(sel):
	"""create new layer drawing from target shape"""
	if not sel:
		print("nothing selected")
		return
	name = getUserInput("name new layer") or "newLayer"
	#print( name )
	sel = [AbsoluteNode(i).shape for i in sel]
	sel = [i for i in sel if i.isShape()]
	shapes = [i.getShapeLayer(name=name) for i in sel]
	#print("type shapes {}, {}".format( type( shapes[0]), shapes[0] ) )
	for i in shapes:
		print("type i {}".format(type(i)))
		print("i transform {}".format(i.transform))
		i.transform.set("translateZ", 1, relative=True)
	return shapes




#### dynamics

def makeCurveDynamic(sel):
	"""allows modelling using tension and collision
	expose tether controls for both ends if curve is not closed"""

def makeMuscleCurve(sel):
	"""creates a muscle curve from target, following source live by default"""
	if not sel:
		return
	sel = [AbsoluteNode(i) for i in sel]
	muscle.MuscleCurve.create(sel)

def constrainDynamicCurves(sel):
	"""create dynamic constraint between any two points of two curves"""
	if not sel: return
	if len(sel) != 2:
		raise RuntimeError("select two dynamic curves' cvs")


	# sel = [AbsoluteNode(i) for i in sel]
	# sel = [dynamics.NHair.fromDynamicCurve(i) for i in sel]
	# dynamics.constrainClosestPoints(sel[0], sel[1])

