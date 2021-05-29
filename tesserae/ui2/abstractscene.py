from __future__ import annotations

from functools import partial, wraps
import math, random
from tree import Tree, Signal
from tree.ui.lib import KeyState, keyDict
from typing import TYPE_CHECKING, Union, Dict, List
from weakref import WeakSet, WeakValueDictionary, WeakKeyDictionary
# ugly fake imports for type hinting
if TYPE_CHECKING:
	from edRig.tesserae.ui2.abstractview import AbstractView
	from edRig.tesserae import AbstractGraph


# scene holding visual node graph
from PySide2 import QtCore, QtWidgets, QtGui
#from edRig.tesserae.ui2.abstracttile import AbstractTile, Knob, Pipe
from edRig.tesserae.ui3.abstracttile import AbstractTile, Knob, Pipe
#from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.abstractgraph import AbstractGraph
from edRig.tesserae.abstractnode import AbstractNode
from edRig.tesserae.abstractedge import AbstractEdge
from edRig.tesserae.ui2.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)
from edRig.tesserae.constant import debugEvents
from edRig.tesserae.ui2 import relax

class AbstractScene(QtWidgets.QGraphicsScene):
	"""graphics scene for interfacing with abstractgraph and ui
	hook directly into abstractgraph tree signals

	"""
	def __init__(self, parent=None, graph:AbstractGraph=None,
	             # view:"edRig.tesserae.ui2.AbstractView"=None
	             view:"AbstractView"=None
	             ):
		super(AbstractScene, self).__init__(parent)
		#self.graph = graph # AbstractGraph object
		self.views = [view]
		# eventually allowing multiple codependent views of the same graph
		self.activeView = view

		# scene is tied to GRAPH, not to view
		self._graph = graph


		self.setSceneRect(1000, 200, 0, 0)
		self.tiles = {} #type: Dict[AbstractNode, AbstractTile]
		#self.tiles = WeakKeyDictionary() #type: Dict[AbstractNode, AbstractTile]
		self.pipes = {} #type: Dict[AbstractEdge, Pipe]
		# self.pipes = WeakKeyDictionary() #type: Dict[AbstractEdge, Pipe]


		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

		# tree signal hookups
		self.graph.structureChanged.connect(self.onNodesChanged)
		self.graph.edgesChanged.connect(self.onEdgesChanged)

		# temp
		self.mouseMoveCounter = 0


	@property
	def graph(self)->AbstractGraph:
		return self._graph

	def getTile(self, node):
		"""returns tile for the given node, name, path or uuid
		"""
		print("scene getTile", node)
		node = self.graph.getNode(node)
		result = self.tiles.get(node)
		if not result:
			print("no tile for node {} found".format(node))
			return None
		return result

	### region graph signal functions
	def onNodesChanged(self, node, parent=None,
	                   eventType=Tree.StructureEvents.branchRemoved):
		print("scene onNodesChanged")
		print("node", node, "parent", parent)
		print("tiles", self.tiles)
		if not isinstance(node, AbstractNode):
			print("node is not abstract, skipping")
			return
		# node created
		if eventType == Tree.StructureEvents.branchAdded:
			print("scene signal node added")
			tile = self.makeTile(abstract=node)
			return tile
		elif eventType == Tree.StructureEvents.branchRemoved:
			print("scene signal node removed")
			tile = self.getTile(node)
			if tile:
				self.deleteTile(tile)
			return tile


	def addNode(self, nodeType:Union[str, AbstractNode], pos=None):
		"""This should not be called with string, only temporary
		till routing is fixed
		"""
		print("scene addNode", nodeType)
		# print("nodes", self.tiles)
		if isinstance(nodeType, str):
			newAbstract = self.graph.createNode(nodeType)
			self.graph.addNode(newAbstract)
			return
		else: newAbstract = nodeType
		pos = pos or self.activeView.camCentre
		tile = self.makeTile(abstract=newAbstract, pos=pos)


	def onEdgesChanged(self, edge:AbstractEdge,
	                   event=AbstractGraph.EdgeEvents.added):
		"""called when an edge is created or dereferenced in the graph"""
		print("scene onEdgesChanged")
		if event == AbstractGraph.EdgeEvents.removed:
			pipe = self.pipes.get(edge)
			if not pipe:
				return
			self.deletePipe(pipe)
		elif event == AbstractGraph.EdgeEvents.added:
			self.addEdgePipe(edge)


	def sync(self):
		"""catch-all method to keep ui in sync with graph"""
		print("scene sync")

		abstractNodes = self.graph.nodes

		# for i in abstractNodes:
		# 	if i not in list(self.tiles.keys()):
		# 		self.tiles[i] = self.makeTile(i)
		# for i in list(self.tiles.keys()):
		# 	if i not in abstractNodes:
		# 		self.deleteTile(i)

		# for i in list(self.tiles.values()):
		# 	i.sync()

		abstractEdges = self.graph.edges
		print("edges", self.graph.edges)
		for i in abstractEdges:
			if i not in list(self.pipes.keys()):
				self.pipes[i] = self.addEdgePipe(edge=i)
				self.addPipe(self.pipes[i])
		for i in list(self.pipes.keys()):
			if i not in abstractEdges:
				self.deletePipe(i)
		print("finished scene sync")

		self.updatePipePaths()

		#super(AbstractScene, self).update()
		self.update()

	def makeTile(self, abstract:AbstractNode=None,
	             pos:Union[
		             QtCore.QPoint, QtCore.QPointF, None]=None
	             )->AbstractTile:
		print("scene makeTile", abstract)
		#print("tiles", self.tiles)
		if isinstance(self.tiles.get(abstract), AbstractTile):
			raise RuntimeError("added abstract already in scene")
		tile = AbstractTile(abstractNode=abstract,
		                    widgetParent=self.parent(),
		                    #widgetParent=self.activeView,
		                    )
		self.addItem(tile)
		# get default position
		if pos is None:
			print("adding random pos")
			# pos = (self.activeView.camCentre +
			# 	QtCore.QPoint(random.random(), random.random()) * 10)
			pos = self.activeView.camCentre #type: QtCore.QPoint
			pos.setX(pos.x() + random.random() * 100)

		# # set random jitter position
		# tile.setPos(random.random(), random.random())
		# self.relaxItems([tile])
		if isinstance(pos, (QtCore.QPointF, QtCore.QPoint)):
			tile.setPos(pos)
		else:
			tile.setPos(*pos)
		self.tiles[abstract] = tile
		#self.addItem(tile.settingsProxy)
		self.relaxItems([tile], iterations=2)
		return tile

	def addEdgePipe(self, edge:AbstractEdge=None):
		"""can only be done with an existing abstractEdge"""
		if debugEvents: print("scene addEdgePipe")
		if edge:
			start = self.tiles[edge.source[0]].knobs[
				edge.source[1].stringAddress()]
			end = self.tiles[edge.dest[0]].knobs[
				edge.dest[1].stringAddress()]
			pipe = Pipe(start=start, end=end, edge=edge)

			self.pipes[edge] = pipe

			self.addPipe(pipe)

			return pipe

	def addPipe(self, pipe):
		self.addItem(pipe)
		pipe.drawPath(pipe.start, pipe.end)

	def updatePipePaths(self, tiles:List[AbstractTile]=None):
		"""updates everything for now - if that gets laggy only redraw changed"""
		# print("scene update")
		# print("graph edges", self.graph.edges)
		if tiles:
			edges = set()
			for i in tiles:
				# edges.update(i.abstract.edges)
				edges.update(self.graph.nodeEdges(i.abstract, all=True))
			pipes = [self.pipes[i] for i in edges]
		else:
			pipes = self.pipes.values()
		for i in pipes:
			i.redrawPath()

	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		if debugEvents:print("scene onDeleteCalled")
		if debugEvents: print("selection is {}".format(self.selectedItems()))
		# first selected nodes - in theory can just update graph and call sync
		for i in self.selectedTiles():
			self.graph.deleteNode(i.abstract)
			print("abstract graph nodes are {}".format(self.graph.knownNames))
			self.deleteTile(i)
		for i in self.selectedPipes():
			self.graph.deleteEdge(i.edge)
			#self.deletePipe(i)

		#print self.selectedTiles()


	def deleteTile(self, tile):
		"""ONLY VISUAL"""
		if isinstance(tile, AbstractNode):
			if tile not in list(self.tiles.keys()):
				return
			tile = self.tiles[tile]
		for i in tile.abstract.edges:
			pipe = self.pipes[i]
			self.deletePipe(pipe)
		# for k, v in self.tiles.iteritems():
		# 	if v == tile:
		# 		target = k
		#self.tiles.pop(target)
		self.tiles.pop(tile.abstract)
		self.removeItem(tile)

	def deleteEdgePipe(self, edge:AbstractEdge):
		"""called when a graph edge is deleted or dereferenced
		"""


	def deletePipe(self, pipe:Pipe):
		if debugEvents: print("scene deletePipe")
		# if isinstance(pipe, AbstractEdge):
		# 	if pipe not in list(self.pipes.keys()):
		# 		return
		# 	pipe = self.pipes[pipe]

		self.pipes.pop(pipe.edge)

		# remove pipe references from knobs
		for knob in pipe.start, pipe.end:
			if pipe in knob.pipes:
				knob.pipes.remove(pipe)
		self.removeItem(pipe)
		# i never want to tipe pipe


	def selectedTiles(self):
		nodes = []
		for item in self.selectedItems():
			if isinstance(item, AbstractTile):
				nodes.append(item)
		return nodes

	def selectedPipes(self):
		return [i for i in self.selectedItems()
		        if isinstance(i, Pipe)]

	def mousePressEvent(self, event):
		if debugEvents: print("scene mousePress")
		super(AbstractScene, self).mousePressEvent(event)
		if event.isAccepted():
			if debugEvents: print("scene mousePress accepted, returning")
			return True
		selected_nodes = self.selectedTiles()
		# if self.activeView:
		# 	self.activeView.beginDrawPipes(event)

	def mouseMoveEvent(self, event):

		self.updatePipePaths(self.selectedTiles())

		self.mouseMoveCounter += 1
		self.mouseMoveCounter = self.mouseMoveCounter % 6

		if self.mouseMoveCounter:
			return super(AbstractScene, self).mouseMoveEvent(event)

		# only activate occasionally
		# get intersecting tiles
		toRelax = []
		expand = 20
		margins = QtCore.QMargins(expand, expand, expand, expand)
		for i in self.selectedTiles():
			items = self.items(i.sceneBoundingRect().marginsAdded(margins))
			items = set(filter(lambda x: isinstance(x, AbstractTile), items))
			items = (items).difference(set(self.selectedTiles()))

			toRelax.extend(items)

		#for i in self.selectedTiles():
		#self.relaxItems(toRelax) # not needed
		#self.update()
		super(AbstractScene, self).mouseMoveEvent(event)

	def relaxItems(self, items, iterations=1):
		#print("scene relax items")
		for n in range(iterations):
			for i in items:
				force = relax.getForce(i)
				#print("force", force)
				i.setPos(i.pos() + force.toPointF())

	def layoutTiles(self, tiles:List[AbstractTile]=None):
		"""single shot layout of all given nodes
		seed nodes are only arranged vertically
		Longest critical path taken as the baseline,
		other nodes laid out relative to it


		"""
		tiles = tiles or set(self.tiles.values())
		nodes = set(i.abstract for i in tiles)
		islands = self.graph.getIslands(nodes)
		for index, island in islands.items():
			ordered = self.graph.orderNodes(island)

			# only x for now
			baseTile = self.tiles[ordered[0]]
			separation = 75
			baseX = baseTile.pos().x() + baseTile.sceneBoundingRect().width() + separation
			x = baseX
			for i in ordered[1:]:
				tile = self.tiles[i]
				tile.setX(x)
				x += tile.sceneBoundingRect().width() + separation
		self.updatePipePaths(tiles)

	def mouseReleaseEvent(self, event):
		if self.activeView:
			self.activeView.endDrawPipes(event)
		super(AbstractScene, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		#print("scene keyPressEvent", keyDict[event.key()])
		# for some reason focus events mess everything up
		super(AbstractScene, self).keyPressEvent(event)

	def dragMoveEvent(self, event:QtWidgets.QGraphicsSceneDragDropEvent):
		if debugEvents:print("scene dragMoveEvent")
		return super().dragMoveEvent(event)


	### region drawing

	def _draw_grid(self, painter, rect, pen, grid_size):
		# change to points
		lines = []
		left = int(rect.left()) - (int(rect.left()) % grid_size)
		top = int(rect.top()) - (int(rect.top()) % grid_size)
		x = left
		while x < rect.right():
			x += grid_size
			lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
		y = top
		while y < rect.bottom():
			y += grid_size
			lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
		painter.setPen(pen)
		painter.drawLines(lines)


	def drawBackground(self, painter, rect):
		#painter.save()
		# draw solid background
		color = QtGui.QColor(*self._bg_color)
		painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
		painter.setBrush(color)
		painter.drawRect(rect.normalized())
		if not self._grid:
			return
		zoom = self.activeView.get_zoom()
		grid_size = 20
		if zoom > -0.5:
			color = QtGui.QColor(*self.grid_color)
			pen = QtGui.QPen(color, 0.65)
			self._draw_grid(painter, rect, pen, grid_size)
		color = QtGui.QColor(*VIEWER_BG_COLOR)
		color = color.lighter(130)
		color = QtCore.Qt.lightGray

		pen = QtGui.QPen(color, 0.65)
		self._draw_grid(painter, rect, pen, grid_size * 8)

		# draw node set fields
		# how many sets is each node part of
		tileDepth = {i : 1 for i in self.tiles.values()}
		for n, (name, data) in enumerate(
				self.graph.nodeSets.items()):
			tiles = [self.tiles[i] for i in data.nodes]

			# get random colour for this set
			# replace with proper pastels at some point
			s = hash(name)
			random.seed(a=s)
			#random.setstate()
			colour = QtGui.QColor.fromRgbF(
				random.random(), random.random(), random.random(),
			)
			#colour = QtCore.Qt.yellow
			painter.pen().setColor(colour)
			painter.setPen(colour)
			colour.setAlphaF(0.2)
			painter.brush().setColor(colour)
			painter.setBrush(colour)

			# gather corner points of all nodes
			points = [None] * len(tiles) * 4
			for i, tile in enumerate(tiles):

				# expand for each set node is part of
				expansion = 10 * tileDepth[tile]
				margins = QtCore.QMargins(
					expansion, expansion, expansion, expansion
				)

				r = tile.sceneBoundingRect()
				r = r.marginsAdded(margins)
				points[i * 4] = r.topLeft()
				points[i * 4 + 1] = r.topRight()
				points[i * 4 + 2] = r.bottomRight()
				points[i * 4 + 3] = r.bottomLeft()

				tileDepth[tile] += 1
			# points = [QtCore.QPoint(j) for j in points]
			points = [j.toPoint() for j in points]
			poly = QtGui.QPolygon.fromList(points)
			#painter.drawConvexPolygon(points)
			painter.drawConvexPolygon(poly)


		#painter.restore()
	# endregion

	@property
	def grid(self):
		return self._grid


	@grid.setter
	def grid(self, mode=True):
		self._grid = mode


	@property
	def grid_color(self):
		return self._grid_color


	@grid_color.setter
	def grid_color(self, color=(0, 0, 0)):
		self._grid_color = color


	@property
	def background_color(self):
		return self._bg_color


	@background_color.setter
	def background_color(self, color=(0, 0, 0)):
		self._bg_color = color

	def serialiseUi(self, graphData):
		"""adds ui information to serialised output from graph
		no idea where better to put this"""
		for node, tile in self.tiles.items():
			graphData["nodes"][node.uid]["ui"] = tile.serialise()

	def regenUi(self, graphData):
		"""reapplies saved ui information to tiles"""
		for uid, info in graphData["nodes"].items():
			node = self.graph.nodeFromUID(uid)
			tile = self.tiles[node]
			tile.setPos(QtCore.QPointF(*info["ui"]["pos"]))
