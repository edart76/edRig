# edge object in abstract graph
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple
if TYPE_CHECKING:
	from edRig.tesserae.abstractnode import AbstractNode
	from edRig.tesserae.abstractattr import AbstractAttr
	from edRig.tesserae.abstractgraph import AbstractGraph

from tree import Signal

class AbstractEdge(object):
	"""connects two abstractNode/abstractAttr objects"""


	def __init__(self, source:"AbstractAttr"=None,
	             dest:"AbstractAttr"=None,
	             graph:"AbstractGraph"=None):
		"""source and dest to be abstractAttrItems"""
		self.graph = graph
		if source:
			self.sourceAttr = source
			self.sourceNode = source.node
		if dest:
			self.destAttr = dest
			self.destNode = dest.node
		self.dataType = self.sourceAttr.dataType

		# signal on edge garbage collected / destroyed
		self.edgeDestroyed = Signal()


	def __str__(self):
		""" dirty solution to remove edge objects from serialisation process """
		return str( self.serialise() )

	def __del__(self):
		"""fires edge death signal"""
		self.edgeDestroyed()

	# for anything dealing with nodes and attributes, return node first
	@property
	def source(self)->Tuple["AbstractNode", "AbstractAttr"]:
		return self.sourceNode, self.sourceAttr

	@property
	def dest(self)->Tuple["AbstractNode", "AbstractAttr"]:
		return self.destNode, self.destAttr

	def oppositeAttr(self, attr)->"AbstractAttr":
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






