# scene holding visual node graph
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tesserae.ui2.abstracttile import AbstractTile, Knob, Pipe
#from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.abstractnode import AbstractNode
from edRig.tesserae.abstractedge import AbstractEdge
from edRig.tesserae.ui2.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)


class AbstractScene(QtWidgets.QGraphicsScene):
	"""graphics scene for interfacing with abstractgraph and ui"""
	def __init__(self, parent=None, graph=None, view=None):
		super(AbstractScene, self).__init__(parent)
		#self.abstractGraph = graph # AbstractGraph object
		self.views = [view]
		# eventually allowing multiple codependent views of the same graph
		self.activeView = view
		self.setSceneRect(1000, 200, 0, 0)
		self.tiles = {} # AbstractNode : AbstractTile
		self.pipes = {} # AbstractEdge : Pipe


		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

	@property
	def abstractGraph(self):
		return self.views[0].graph

	def addNode(self, nodeType, pos):
		newAbstract = self.abstractGraph.createNode(nodeType)
		self.abstractGraph.addNode(newAbstract)
		self.makeTile(abstract=newAbstract, pos=pos)
		print "end addnode"
		#self.sync()

	def sync(self):
		"""catch-all method to keep ui in sync with graph"""

		abstractNodes = self.abstractGraph.nodes
		#current = {tile:tile.abstract for tile in self.tiles.keys()}

		# print ""
		# print "current scene is {}".format(self.tiles)
		# print "current graph is {}".format(abstractNodes)

		for i in abstractNodes:
			if i not in self.tiles.keys():
				self.tiles[i] = self.makeTile(i)
		for i in self.tiles.keys():
			if i not in abstractNodes:
				self.deleteTile(i)

		for i in self.tiles.values():
			i.sync()

		abstractEdges = self.abstractGraph.edges
		for i in abstractEdges:
			if i not in self.pipes.keys():
				self.pipes[i] = self.makePipe(edge=i)
				self.addPipe(self.pipes[i])
		for i in self.pipes.keys():
			if i not in abstractEdges:
				self.deletePipe(i)
		print "finished sync"

		#super(AbstractScene, self).update()

	def makeTile(self, abstract=None, pos=(0,0)):
		print "making tile for {}".format(abstract)
		tile = AbstractTile(abstractNode=abstract, scene=self)
		self.addItem(tile)
		if isinstance(pos, QtCore.QPointF):
			tile.setPos(pos)
		else:
			tile.setPos(*pos)

		if not abstract:
			raise RuntimeError("wtf no abstract don't do that")
		if not tile in self.tiles.values():
			self.tiles[abstract] = tile

		print "added tile"
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
		assert isinstance(pipe, Pipe)
		self.addItem(pipe)
		pipe.draw_path(pipe.start, pipe.end)

	def updatePipePaths(self, nodes=None):
		"""updates everything for now - if that gets laggy only redraw changed"""
		for i in self.pipes.values():
			i.redrawPath()

	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def deleteTile(self, tile):
		"""ONLY VISUAL"""
		if isinstance(tile, AbstractNode):
			if tile not in self.tiles.keys():
				return
			tile = self.tiles[tile]
		for i in tile.pipes:
			self.deletePipe(i)
		for k, v in self.tiles.iteritems():
			if v == tile:
				target = k
		self.tiles.pop(target)
		self.removeItem(tile)

	def deletePipe(self, pipe):
		if isinstance(pipe, AbstractEdge):
			if pipe not in self.pipes.keys():
				return
			pipe = self.pipes[pipe]
		# for k, v in self.pipes.iteritems():
		# 	if v == pipe:
		# 		self.pipes.pop(k)
		self.pipes.pop([k for k, v in self.pipes.iteritems() if v == pipe][0])
		for i in pipe.start, pipe.end:
			if pipe in i.pipes:
				i.pipes.remove(pipe)
		self.removeItem(pipe)
		# i never want to tipe pipe

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		print "selection is {}".format(self.selectedItems())
		# first selected nodes - in theory can just update graph and call sync
		for i in self.selectedNodes():
			self.abstractGraph.deleteNode(i.abstract)
			print "abstract graph nodes are {}".format(self.abstractGraph.knownNames)
			self.deleteTile(i)
		for i in self.selectedPipes():
			self.abstractGraph.deleteEdge(i.edge)
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

		#print("scene press event")
		selected_nodes = self.selectedNodes()
		if self.activeView:
			self.activeView.sceneMousePressEvent(event)
		super(AbstractScene, self).mousePressEvent(event)
		keep_selection = any([
			event.button() == QtCore.Qt.MiddleButton,
			event.button() == QtCore.Qt.RightButton,
			event.modifiers() == QtCore.Qt.AltModifier
		])
		if keep_selection:
			for node in selected_nodes:
				print "selected node is {}".format(node)
				node.setSelected(True)

	def mouseMoveEvent(self, event):
		if self.activeView:
			self.activeView.sceneMouseMoveEvent(event)
		super(AbstractScene, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if self.activeView:
			self.activeView.sceneMouseReleaseEvent(event)
		super(AbstractScene, self).mouseReleaseEvent(event)

	# def keyPressEvent(self, event): # THIS GIVES A REAL BAD TIME
	# 	if self.activeView:
	# 		self.activeView.keyPressEvent(event)


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
		#color = color.darker(130)
		if zoom < -0.0:
			#color = color.darker(100 - int(zoom * 110))
			pass
		pen = QtGui.QPen(color, 0.65)
		self._draw_grid(painter, rect, pen, grid_size * 8)
		#painter.restore()


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
		for node, tile in self.tiles.iteritems():
			graphData["nodes"][node.uid]["ui"] = tile.serialise()

	def regenUi(self, graphData):
		"""reapplies saved ui information to tiles"""
		for uid, info in graphData["nodes"].iteritems():
			node = self.abstractGraph.nodeFromUID(uid)
			tile = self.tiles[node]
			tile.setPos(QtCore.QPointF(*info["ui"]["pos"]))
