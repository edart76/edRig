# edge object in abstract graph


class AbstractEdge(object):
	"""connects two abstractNode/abstractAttr objects"""

	def __init__(self, source=None, dest=None, graph=None):
		"""source and dest to be abstractAttrItems"""
		self.graph = graph
		if source:
			self.sourceAttr = source
			self.sourceNode = source.node
		if dest:
			self.destAttr = dest
			self.destNode = dest.node
		self.dataType = self.sourceAttr.dataType


	def __str__(self):
		""" dirty solution to remove edge objects from serialisation process """
		return str( self.serialise() )

	# for anything dealing with nodes and attributes, return node first
	@property
	def source(self):
		return self.sourceNode, self.sourceAttr

	@property
	def dest(self):
		return self.destNode, self.destAttr

	def oppositeAttr(self, attr):
		""" given one attr, return its opposite,
		or None if attr is not recognised """
		if attr == self.sourceAttr:
			return self.destAttr
		elif attr == self.destAttr:
			return self.sourceAttr
		else:
			return None

	def serialise(self):
		"""store uids of nodes, and names of attributes - edges regenerated last"""
		serial = {
			"source" : {
				"node" : self.sourceNode.uid,
				"attr" : self.sourceAttr.name,
				"nodeName" : self.sourceNode.nodeName #readability
			},
			"dest" : {
				"node" : self.destNode.uid,
				"attr" : self.destAttr.name,
				"nodeName" : self.destNode.nodeName #matters
			}
		}
		return serial

	@staticmethod
	def fromDict(serial, graph=None):
		sourceNode = graph.nodeFromUID(serial["source"]["node"])
		sourceAttr = sourceNode.getOutput(serial["source"]["attr"])

		destNode = graph.nodeFromUID(serial["dest"]["node"])
		destAttr = destNode.getInput(serial["dest"]["attr"])

		return AbstractEdge(source=sourceAttr, dest=destAttr, graph=graph)

class AbstractRelation(object):
	"""base class for things like group boxes, vertex networks etc"""

	def __init__(self, graph=None, name=""):
		self.graph = graph
		self.nodes = []

class AbstractGroup(AbstractRelation):
	"""defines a basic group of nodes"""
	def __init__(self, graph=None, name=""):
		super(AbstractGroup, self).__init__(graph)






