# fucnctions for renumbering mesh points, getting weights,
# interfacing between weights and maps etc
# additionally for working with nurbs shapes
from edRig import core, attr
from edRig.core import AbsoluteNode, ECA
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from maya import cmds



def getConnectedDeformers(target):
	"""gets all chained deformers since the previous shape node"""
	shape = core.shapeFrom(target)

def getMeshInfo(target):
	"""saves mesh vertex positions and connections to data"""

def getWeights(targetMesh, targetDeformer, attr):
	"""gets normal weights"""

def getSkinWeights(shape, skin, influenceList=None):
	"""returns large tuple of form
	( (weights list for influence i), (for i+1)) etc"""
	skin = AbsoluteNode(core.shapeFrom(skin))
	skinFn = oma.MFnSkincluster(skin.MObject)

def getPaintable(shape):
	pass

def splitHistoryAtPlug(inputPlug, name="split"):
	"""inserts tweak node directly BEFORE specified plug, allowing
	GPU-safe extraction of mesh data at any point
	:returns plug"""
	driver = attr.getDrivingPlug(inputPlug)
	tweak = ECA("tweak", name=name)
	cmds.connectAttr(driver, tweak+".input[0].inputGeometry")
	return tweak + ".outputGeometry[0]"

def getLiveMatrixOnMesh(meshShape, closeTo):
	"""attach a nurbs surface to nearest face, then get matrix from that"""
	mesh = AbsoluteNode(meshShape)

def attachNurbsSurfaceToMesh(meshShape, pntList):
	"""attach nurbs surface to target points"""
	nurbs = ECA("nurbsSurface")
	# no checking for crossed surface here
	for i, val in enumerate(pntList):
		cmds.connectAttr(meshShape+".points[{}]".format(val),
		                 nurbs+".controlPoints[{}]".format(i))
	return nurbs




"""
weightlist attribute common to deformers
weightList - array, one per mesh
	weightList[0]
		weights - array, one per vertex
			weights[12] - most of the time, just a straight float value
			weights[13]
			weights[14]
this is common across most deformers, and worth assuming for default behaviour


SKINCLUSTERS ARE DIFFERENT
weightList - array, ONE PER VERTEX
	weightList[1]
		weights - array, ONE PER INFLUENCE ON SKINCLUSTER, indexed in sync
			weights[0]
			weights[1] - this would be for three joints
			weights[2]
	weightList[2]
		weights
			weights[0]
			weights[1]
			weights[2]

weights often stored only if they deviate from a base value - a bend deformer is 1
if no weights are painted, arrays remain at [0]


best to do this with a default-override system

override deformer type
	so specify entirely bespoke ways of handling, ie skin
	
override attribute maps
	pick out weights to register
	save weights by default, don't error if something isn't there
	
goal is to have dict of { vertexIndex : weight }
for skins just use list or dict of influences, but store
weights of each influence in the same way

"""

class DeformerWrapper(object):
	"""interface for setting and getting weights"""

	def __init__(self, deformerNode):
		self.defaults = {
			"default": {
				"weightList": self.getGenericWeights},
			"skinCluster": {
				"weightList": self.getSkinWeights,
				"blendWeights": self.getGenericWeights}
		} # tried to make this a class attribute, but couldn't
		# work out how to direct to call instance methods

		self.node = AbsoluteNode(deformerNode)
		self.deformerType = self.node.MFnDependency.typeName
		print "new deformer wrapper is type {}".format(self.deformerType)

		if self.node.MObject.hasFn(681): # skinClusterFilter
			self.fn = oma.MFnSkincluster(self.node.MObject)
		else:
			self.fn = oma.MFnGeometryFilter(self.node.MObject)

		if self.deformerType in self.defaults.keys():
			self.treatment = self.defaults[self.deformerType]
		else:
			self.treatment = self.defaults["default"]
		self.attrs = self.treatment.keys()

	def getComponentObject(self):
		setFn = om.MFnSet(self.fn.deformerSet())
		members = setFn.getMembers(True) # MSelectionList, flatten=True
		print "members is {}".format(members)






	def getSkinWeights(self):
		"""returns dict of all vertex weighs per influence
		copied in part from charactersetup.com"""
		returnDict = {}
		influences = self.fn.influenceObjects() # MDagPathArray
		numInfluences = len(influences)

		wlPlug = self.fn.findPlug("weightList")
		wlAttr = wlPlug.attribute()
		wPlug = self.fn.findPlug("weights")
		wAttr = wPlug.attribute()


		# create a dict whose key is MPlug index and value is influenceList index
		infIds = {}
		for i in range(numInfluences):
			#returnDict[i] = {}
			infId = int(self.fn.indexForInfluenceObject(influences[i]))
			#infIds[infId] = i
			returnDict[infId] = {}

			for n in xrange(wlPlug.numElements()):
				# iterating over all vertices

				# point the wPlug to index representing this vertex
				wPlug.selectAncestorLogicalIndex(n, wlAttr)

				# we keep zero-weights for now, unless they get slow
				# copying an MPlug every vertex also seems slow
				vPlug = om.MPlug(wPlug)
				vPlug.selectAncestorLogicalIndex(i, wAttr)
				try:
					returnDict[infId][n] = vPlug.asDouble()
				except KeyError:
					pass

		return returnDict

	def setSkinWeights(self, weightsDict):
		pass






	def getGenericWeights(self, weightAttr):
		"""used for any attribute of the normal weightsList form"""



	def setMapAttrs(self, attrs=None):
		"""override maps to save on a specific wrapper"""
		self.attrs = attrs

	def gatherAllWeights(self):
		"""return dict in format of:
		{ "blendWeights" : { # attrName
			0 : 0.2, # dict as returned by specific function
			2 : 0.4},
		"weightList : {
			[
				{ 0 : 0.2,
				4 : 0.5,
				5 : 0.7 },
				{ 3 : 0.1,
				 2 : 0.1 }
			]
		} etc"""
		pass





