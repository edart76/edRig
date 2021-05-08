
"""
abstract system for the graph structure -

for now, use simply directed structure from skeleton

a single master graph is maintained as source of truth for topology,
and for each user input selected, a child graph is created,
covering only the affected nodes
User transformations are summed across each graph and combined
to give final effects on maya nodes

Simply:

			/ --- ToolGraph \
MasterGraph  -----------> combine ---> result
			\ --- ToolGraph /

for finding the path of the

"""

from collections import defaultdict, namedtuple
import networkx as nx # gonna be awkward if nxt gets involved

from tree import Tree

#EphEdge = namedtuple("EphEdge", ["src", "dest", "data"])

# class EphGraph(object):
# 	"""Holder for whole graph system - probably
# 	should not have dynamic structure
# 	holds persistent node sets
# 	"""

class EphNode(object):
	"""SHAMELESS copy from Mme Anzovin
	we assume the node object will be added to graph externally"""
	def __init__(self, name, graph:nx.DiGraph=None,
	             transformNode=None, # MAYBE
	             ):
		self.name = name
		self.graph = graph
		# will node receive direct user input
		self.isUserInput = False
		# does node delimit a region
		self.isBreakpoint = False
		self.tf = transformNode

	def __hash__(self):
		return id(self)

	def inEdges(self):
		return self.graph.in_edges(self)

	def outEdges(self):
		return self.graph.out_edges(self)







