# new hotness

from edRig.tesserae.abstractgraph import AbstractGraph
# main top-level graph, so user can script effectively
# graph = property(fget=lambda : AbstractGraph.graphRegister["main"])  # type: AbstractGraph
# graph = lambda : AbstractGraph.graphRegister["main"] # type: AbstractGraph

@property
def mainGraph(self)->AbstractGraph:
	return AbstractGraph.graphRegister["main"]

"""Going to stop with the absract/real divide, 
and set nodes as proper branches of graph
complexity is killing this project and me
"""