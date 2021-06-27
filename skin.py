from edRig import AbsoluteNode
from edRig import attr
from edRig.maya import core
import maya.api.OpenMayaAnim as oma

class SkinCluster(AbsoluteNode):

	def __new__(cls, node):
		# make sure node always has access to MFnSkinCluster
		absolute = super(SkinCluster, cls).__new__(cls, node)
		absolute.skinFn = oma.MFnSkinCluster(absolute.MObject)
		absolute._outputShape = None


	@property
	def influenceMap(self):
		"""return dict of index : influence
		please use for main interaction, for clarity
		:returns dict"""
		infMap = {}
		for i, n in enumerate(self.influences()):
			# possibly extend with method of connection, if locked etc
			infMap[n] = { "node" : i}
		return infMap


	def influences(self):
		""" returns absoluteNodes for all connected drivers """
		dags = self.skinFn.influenceObjects()
		return [AbsoluteNode( i.fullPathName() ) for i in dags]

	def connectDirtyPlugs(self, target):
		"""effectively creates a master/slave relationship between skcs,
		ensuring slave updates when master is painted"""
		plugs = ("paintArrDirty", "wtDirty")
		for i in plugs:
			self.con( i, target + "." + i)


	@property
	def outputShape(self):
		"""
		unfortunately we need a shape to make the api work properly """
		test = attr.getImmediateFuture( self + ".outputGeometry[0]" )
		test = [ AbsoluteNode(i) for i in test]
		shape = [i for i in test if i.isShape()]
		if not shape:
			self._makeProxyOutputShape()
			return self.outputShape
		return shape[0]

	def _makeProxyOutputShape(self):
		"""create shape node for showing current output of skincluster"""
		shape = core.makeShape(self.name + "Output", "mesh")
		self.con( self.output, shape + ".inMesh")

	@property
	def bindPose(self):
		"""returns the bind pose node if it exists
		basically delete this"""
		return [ attr.getImmediatePast( self + ".bindPose") or [None] ][0][0]



	@property
	def input(self):
		return self + ".inputGeometry[0]"
	@property
	def output(self):
		return self + ".outputGeometry[0]"