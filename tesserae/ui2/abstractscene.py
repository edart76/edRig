from __future__ import annotations

from functools import partial, wraps
from tree import Tree, Signal
from typing import TYPE_CHECKING, Union

# ugly fake imports for type hinting
if TYPE_CHECKING:
	from edRig.tesserae.ui2.abstractview import AbstractView
	from edRig.tesserae import AbstractGraph


# scene holding visual node graph
from PySide2 import QtCore, QtWidgets, QtGui
#from edRig.tesserae.ui2.abstracttile import AbstractTile, Knob, Pipe
from edRig.tesserae.ui3.abstracttile import AbstractTile, Knob, Pipe
#from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.abstractnode import AbstractNode
from edRig.tesserae.abstractedge import AbstractEdge
from edRig.tesserae.ui2.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)
from edRig.tesserae.constant import debugEvents

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
		self.tiles = {} # AbstractNode : AbstractTile
		self.pipes = {} # AbstractEdge : Pipe


		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

		# tree signal hookups
		self.graph.structureChanged.connect(self.onNodesChanged)

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
		self.makeTile(abstract=newAbstract, pos=pos)

	def sync(self):
		"""catch-all method to keep ui in sync with graph"""
		print("scene sync")
		return

		abstractNodes = self.graph.nodes

		for i in abstractNodes:
			if i not in list(self.tiles.keys()):
				self.tiles[i] = self.makeTile(i)
		for i in list(self.tiles.keys()):
			if i not in abstractNodes:
				self.deleteTile(i)

		for i in list(self.tiles.values()):
			i.sync()

		abstractEdges = self.graph.edges
		for i in abstractEdges:
			if i not in list(self.pipes.keys()):
				self.pipes[i] = self.makePipe(edge=i)
				self.addPipe(self.pipes[i])
		for i in list(self.pipes.keys()):
			if i not in abstractEdges:
				self.deletePipe(i)
		print("finished scene sync")

		self.updatePipePaths()

		#super(AbstractScene, self).update()

	def makeTile(self, abstract:AbstractNode=None,
	             pos:Union[
		             QtCore.QPoint, QtCore.QPointF, None]=None
	             )->AbstractTile:
		#print("scene makeTile", abstract)
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
			pos = pos or self.activeView.camCentre
		if isinstance(pos, (QtCore.QPointF, QtCore.QPoint)):
			tile.setPos(pos)
		else:
			tile.setPos(*pos)
		self.tiles[abstract] = tile
		#self.addItem(tile.settingsProxy)
		return tile

	def makePipe(self, edge=None, start=None, end=None):
		"""can only be done with an existing abstractEdge"""
		if edge:
			start = self.tiles[edge.source[0]].getKnob(edge.source[1].name)
			end = self.tiles[edge.dest[0]].getKnob(edge.dest[1].name)
			pipe = Pipe(start=start, end=end, edge=edge)
			start.pipes.append(pipe)
			end.pipes.append(pipe)

			return pipe

	def addPipe(self, pipe):
		self.addItem(pipe)
		pipe.drawPath(pipe.start, pipe.end)

	def updatePipePaths(self, nodes=None):
		"""updates everything for now - if that gets laggy only redraw changed"""
		for i in list(self.pipes.values()):
			i.redrawPath()

	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

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

	def deletePipe(self, pipe):
		if isinstance(pipe, AbstractEdge):
			if pipe not in list(self.pipes.keys()):
				return
			pipe = self.pipes[pipe]
		# for k, v in self.pipes.iteritems():
		# 	if v == pipe:
		# 		self.pipes.pop(k)
		#self.pipes.pop([k for k, v in self.pipes.iteritems() if v == pipe][0])
		self.pipes.pop(pipe.edge)

		# remove pipe references from knobs
		for knob in pipe.start, pipe.end:
			if pipe in knob.pipes:
				knob.pipes.remove(pipe)
		self.removeItem(pipe)
		# i never want to tipe pipe

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		print("scene onDeleteCalled")
		print("selection is {}".format(self.selectedItems()))
		# first selected nodes - in theory can just update graph and call sync
		for i in self.selectedNodes():
			self.graph.deleteNode(i.abstract)
			print("abstract graph nodes are {}".format(self.graph.knownNames))
			self.deleteTile(i)
		for i in self.selectedPipes():
			self.graph.deleteEdge(i.edge)
			self.deletePipe(i)

		#print self.selectedNodes()

	def selectedNodes(self):
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
			print("scene mousePress accepted, returning")
			return True
		selected_nodes = self.selectedNodes()
		# if self.activeView:
		# 	self.activeView.sceneMousePressEvent(event)

	def mouseMoveEvent(self, event):
		# if self.activeView:
		# 	self.activeView.sceneMouseMoveEvent(event)
		super(AbstractScene, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if self.activeView:
			self.activeView.sceneMouseReleaseEvent(event)
		super(AbstractScene, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		print("scene keyPressEvent")
		super(AbstractScene, self).keyPressEvent(event)


	def sceneMouseMoveEvent(self, event):
		""" update test pipe"""
		if self.testPipe:
			knobs = self._items_near(event.scenePos(), Knob, 5, 5)
			pos = event.scenePos()
			if knobs:
				self._live_pipe.drawPath(self._start_port, None, knobs[0].scenePos())

				#self.testPipe.setEnd(knobs[0])
			else:
				self._live_pipe.drawPath(self._start_port, None, pos)
				#
				# self.testPipe.setEnd(event)

		if self.keyState.LMB:
			# nodes could be moving
			# self.scene.updatePipePaths()
			self.updatePipePaths()

	def sceneMousePressEvent(self, event):
		"""triggered mouse press event for the scene (takes priority over viewer).
		 - detect selected pipe and start connection
		 - remap Shift and Ctrl modifier
		currently we control pipe connections from here"""
		ctrl_modifier = event.modifiers() == QtCore.Qt.ControlModifier
		alt_modifier = event.modifiers() == QtCore.Qt.AltModifier
		shift_modifier = event.modifiers() == QtCore.Qt.ShiftModifier
		if shift_modifier:
			event.setModifiers(QtCore.Qt.ControlModifier)
		elif ctrl_modifier:
			event.setModifiers(QtCore.Qt.ShiftModifier)

		if not alt_modifier:
			pos = event.scenePos()
			knobs = self._items_near(pos, Knob, 5, 5)
			if knobs:
				self.testPipe = self.beginTestConnection(knobs[0]) # begins test visual connection
				#self.testPipe.setEnd(event)


	def sceneMouseReleaseEvent(self, event):
		""" if a valid testPipe is created, check legality against graph
		before connecting in graph and view"""

		if event.modifiers() == QtCore.Qt.ShiftModifier:
			event.setModifiers(QtCore.Qt.ControlModifier)

		pos = event.scenePos()
		if self.testPipe:
			# look for juicy knobs
			knobs = self._items_near(pos, Knob, 5, 5)
			if not knobs:
				# destroy test pipe
				self.end_live_connection()

				return
			# making connections in reverse is fine - reorder knobs in this case
			if knobs[0].role == "output":
				legality = self.checkLegalConnection(knobs[0], self.testPipe.start)
			else:
				legality = self.checkLegalConnection(self.testPipe.start, knobs[0])
			print(( "legality is {}".format(legality)))
			if legality:
				self.makeRealConnection(#pipe=self.testPipe,
										source=self.testPipe.start, dest=knobs[0])
			self.end_live_connection()

	#def start_live_connection(self, selected_port):
	def beginTestConnection(self, selected_port):
		"""	create new pipe for the connection.	"""
		if not selected_port:
			return
		self._start_port = selected_port
		self._live_pipe = Pipe()
		self._live_pipe.activate()
		self._live_pipe.style = PIPE_STYLE_DASHED
		# if self._start_port.type == IN_PORT:
		# 	self._live_pipe.input_port = self._start_port
		# elif self._start_port == OUT_PORT:
		# 	self._live_pipe.output_port = self._start_port
		self._live_pipe.start = self._start_port

		# self.scene.addItem(self._live_pipe)
		self.addItem(self._live_pipe)
		return self._live_pipe

	def end_live_connection(self):
		"""	delete live connection pipe and reset start port."""
		if self._live_pipe:
			self._live_pipe.delete()
			self._live_pipe = None
		self._start_port = None
		self.testPipe = None

	def checkLegalConnection(self, start, dest):
		"""checks with graph if attempted connection is legal
		ONLY WORKS ON KNOBS"""
		startAttr = start.attr
		endAttr = dest.attr
		legality = self.graph.checkLegalConnection(
			source=startAttr, dest=endAttr)
		return legality

	def makeRealConnection(self, source, dest):
		"""eyy"""
		self.graph.addEdge(source.attr, dest.attr)
		self.sync()

	def addPipe(self, source, dest):
		newPipe = Pipe(start=source, end=dest)
		#self.pipes.append(newPipe)
		# self.scene.addItem(newPipe)
		self.addItem(newPipe)

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
		# if zoom < -0.0:
		# 	color = color.lighter(100 - int(zoom * 110))
		# 	pass
		pen = QtGui.QPen(color, 0.65)
		self._draw_grid(painter, rect, pen, grid_size * 8)
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
