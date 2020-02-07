""" hyperview describing topology of loom space """
from edRig.tesserae.abstractgraph import AbstractGraph
from edRig.tesserae.abstractnode import AbstractNode
from edRig.tesserae.abstractedge import AbstractEdge

from edRig.lib.python import AbstractTree

class LoomGraph(AbstractGraph):
	""" main graph for loom space
	undirected
	nothing executes """
	pass

class LoomNode(AbstractNode):
	""" node representing a loom field component
	may have unbounded number of topological connections
	represented in graph by number of polygon edges

	also saves the spherical information of which frames
	act over which angles

	"""

	pass

class LoomEdge(AbstractEdge):
	""" unsure of how to weight between edges and nodes, but suffice to
	say """