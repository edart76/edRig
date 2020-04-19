# viewer widget for the abstract view
from PySide2 import QtCore, QtWidgets, QtGui

import edRig.pipeline
from edRig.tesserae.ui2.abstractscene import AbstractScene
from edRig.tesserae.abstractgraph import AbstractGraph
from edRig.tesserae.ui2.tabsearch import TabSearchWidget
from edRig.tesserae.ui2.abstracttile import AbstractTile, Knob, Pipe
from edRig.tesserae.ui2.style import *
from edRig.tesserae.ui2.context import ContextMenu
from edRig.tesserae.ui2.lib import ConfirmDialogue
from edRig.structures import ActionItem, ActionList
from edRig import pipeline, ROOT_PATH

ZOOM_MIN = -0.95
ZOOM_MAX = 2.0

class AbstractView(QtWidgets.QGraphicsView):
	"""simple class to view an abstractGraph's contents"""

	nodeDeleteCalled = QtCore.Signal()
	nodesSelected = QtCore.Signal(list)
	assetChanged = QtCore.Signal(list)

	"""for all modifications to the graph, take input from viewer, check
	legality against graph, modify graph, modify graphics scene"""
	def __init__(self, parent=None, graph=None):
		super(AbstractView, self).__init__(parent)
		# view the graph or create a new one
		if graph:
			self.graph = graph
		else:
			"""set up a new tesserae graph from scratch"""
			self.graph = AbstractGraph.startup()
		self.scene = AbstractScene(parent=None, graph=self.graph, view=self)
		self.setScene(self.scene)

		scene_area = 8000.0
		scene_pos = (scene_area / 2) * -1
		self.setSceneRect(scene_pos, scene_pos, scene_area, scene_area)
		self.setRenderHint(QtGui.QPainter.Antialiasing, True)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

		self._rubber_band = QtWidgets.QRubberBand(
			QtWidgets.QRubberBand.Rectangle, self)
		self.pipes = []

		self.LMB_state = False
		self.RMB_state = False
		self.MMB_state = False

		self._previous_pos = 0,0
		self.testPipe = None
		self._prev_selection = []

		# tab search
		self.tabSearch = TabSearchWidget(parent=self)
		self.tabSearch.set_nodes(self.graph.registeredNodes.keys())


		# signals
		self.tabSearch.search_submitted.connect(self.searchReceived)
		self.nodeDeleteCalled.connect( self.scene.onDeleteCalled )

		self._savePath = None
		self._filePath = None
		#self.saveFolder = None # given by asset

		#self.setWindowModality(QtCore.Qt.WindowModal)
		#self.setWindowModality(QtCore.Qt.ApplicationModal)

		self.contextMenu = ContextMenu(self)

		self._init_actions()


	@property
	def currentAsset(self):
		return self.graph.asset

	@property
	def savePath(self):
		return self._savePath or self.currentAsset.path
	@savePath.setter
	def savePath(self, val):
		self._savePath = val

	@property
	def filePath(self):
		""" exact path to save file """
		return self._filePath
	@filePath.setter
	def filePath(self, val):
		self._filePath = val

	def saveToScene(self):
		"""saves current file path"""
		currentInfo = pipeline.getSceneData()
		if self.savePath:
			currentInfo["tesserae.savePath"] = self.savePath
			currentInfo["tesserae.filePath"] = self.filePath
		pipeline.saveSceneData(currentInfo)
		#print( pipeline.getSceneData().serialise(pretty=True))

	def loadFromScene(self, force=True):
		""" loads current file path
		if force, loads entire graph"""
		info = pipeline.getSceneData()
		self.savePath = info["tesserae.savePath"]
		self.filePath = info["tesserae.filePath"]
		if force and pipeline.checkFileExists(self.filePath):
			print("forcing open from scene, self save path is {}".format(self.filePath))
			self.openTilePileFile(self.filePath, force=True)
		#print( info.serialise(pretty=True))

	def _init_actions(self):
		# setup tab search shortcut.
		tab = QtWidgets.QAction('Search Nodes', self)
		tab.setShortcut('tab')
		tab.triggered.connect(self.tabSearchToggle)
		self.addAction(tab)

		#setup_actions(self)
	# def setAsset(self, assetItem):
	# 	self.currentAsset = assetItem

	def sync(self):
		self.scene.sync()

	# capture events #####
	# def keyPressEvent(self, event):
	# 	"""test"""
	# 	#super(AbstractView, self).keyPressEvent(event)
	# 	print "viewer keyPress is {}".format(event.text())
	#
	# 	if event.matches(QtGui.QKeySequence.Delete):
	# 		# print "deleteCalled"
	# 		self.nodeDeleteCalled.emit()
	# 		self.scene.onDeleteCalled()
	# 		event.accept()
	# 		#event.ignore()
	# 	else:
	# 		pass
	# 		#super(AbstractView, self).keyPressEvent(event)
	# 	super(AbstractView, self).keyPressEvent(event)

	# 		#event.accept()
	# 	# elif event.key() == 0x01000001: # tab
		# 	self.tabSearchToggle()
		# 	event.accept()
		# elif event.key() == 0x53: # s
		# 	#self.saveAsTilePile()
		# 	pass
		# elif event.key() == 0x4e: # n
		# 	pass
		# elif event.key() == 0x46: # f
		# 	pass
		# elif event.key() == 0x43: # c
		# 	pass
		# elif event.key() == 0x56: #v
		# 	pass
		# elif event.key() == 0x45: #e
		# 	pass
		# else:
		# 	#super(AbstractView, self).keyPressEvent(event)
		# 	pass
		# else:
		# 	event.accept()

	def wheelEvent(self, event):
		adjust = (event.delta() / 120) * 0.1
		self._set_viewer_zoom(adjust)

	def contextMenuEvent(self, event):
		"""i'm really honestly quite sick of this softlocking my program"""

		super(AbstractView, self).contextMenuEvent(event)

		# just check in every widget if event has been used
		if event.isAccepted():
			return
		self.RMB_state = False
		self.buildContext()
		self.contextMenu.exec_(event.globalPos())
		# super(AbstractView, self).contextMenuEvent(event)

	""" view receives events first - calling super passes them to scene """


	def mousePressEvent(self, event):
		#print ("view mouse event")
		# called BEFORE scene event
		alt_modifier = event.modifiers() == QtCore.Qt.AltModifier
		shift_modifier = event.modifiers() == QtCore.Qt.ShiftModifier

		#event.accept() # still passed to scene
		#event.ignore() # still passed to scene lol

		items = self._items_near(self.mapToScene(event.pos()), None, 20, 20)
		nodes = [i for i in items if isinstance(i, AbstractTile)]

		if event.button() == QtCore.Qt.LeftButton:
			self.LMB_state = True
			# toggle extend node selection.
			if shift_modifier:
				for node in nodes:
					node.selected = not node.selected
			else:
				for i in self.selectedNodes():
					i.setSelected(False)
				for i in nodes:
					i.setSelected(True)
		elif event.button() == QtCore.Qt.RightButton:
			self.RMB_state = True
		elif event.button() == QtCore.Qt.MiddleButton:
			self.MMB_state = True
		self._origin_pos = event.pos()
		self._previous_pos = event.pos()
		self._prev_selection = self.selectedNodes()

		# close tab search
		if self.tabSearch.isVisible():
			self.tabSearchToggle()

		if alt_modifier:
			return

		# show selection selection marquee
		if self.LMB_state and not items:
			rect = QtCore.QRect(self._previous_pos, QtCore.QSize())
			rect = rect.normalized()
			map_rect = self.mapToScene(rect).boundingRect()
			self.scene.update(map_rect)
			self._rubber_band.setGeometry(rect)
			self._rubber_band.show()

		if not shift_modifier:
			super(AbstractView, self).mousePressEvent(event)

		if event.button() == QtCore.Qt.LeftButton:
			# emit specific node selected signal
			if self.selectedNodes():
				#self.node_selected.emit()
				self.nodesSelected.emit(self.selectedNodes())

	def mouseReleaseEvent(self, event):
		if event == QtGui.QContextMenuEvent:
			pass
		if event.button() == QtCore.Qt.LeftButton:
			self.LMB_state = False
		elif event.button() == QtCore.Qt.RightButton:
			self.RMB_state = False
		elif event.button() == QtCore.Qt.MiddleButton:
			self.MMB_state = False

		# hide selection marquee
		if self._rubber_band.isVisible():
			rect = self._rubber_band.rect()
			map_rect = self.mapToScene(rect).boundingRect()
			self._rubber_band.hide()
			self.scene.update(map_rect)

		super(AbstractView, self).mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		alt_modifier = event.modifiers() == QtCore.Qt.AltModifier
		shift_modifier = event.modifiers() == QtCore.Qt.ShiftModifier
		if self.MMB_state or (self.LMB_state and alt_modifier):
			pos_x = (event.x() - self._previous_pos.x())
			pos_y = (event.y() - self._previous_pos.y())
			self._set_viewer_pan(pos_x, pos_y)
		elif self.RMB_state:
			pos_x = (event.x() - self._previous_pos.x())
			zoom = 0.1 if pos_x > 0 else -0.1
			#self._set_viewer_zoom(zoom)
			#self.set_zoom(zoom)
			# avoid context stuff interfering


		if self.LMB_state and self._rubber_band.isVisible():
			rect = QtCore.QRect(self._origin_pos, event.pos()).normalized()
			map_rect = self.mapToScene(rect).boundingRect()
			path = QtGui.QPainterPath()
			path.addRect(map_rect)
			self._rubber_band.setGeometry(rect)
			self.scene.setSelectionArea(path, QtCore.Qt.IntersectsItemShape)
			self.scene.update(map_rect)

			if shift_modifier and self._prev_selection:
				for node in self._prev_selection:
					if node not in self.selectedNodes():
						node.selected = True

		self._previous_pos = event.pos()
		super(AbstractView, self).mouseMoveEvent(event)

	def sceneMouseMoveEvent(self, event):
		""" update test pipe"""
		if self.testPipe:
			knobs = self._items_near(event.scenePos(), Knob, 5, 5)
			pos = event.scenePos()
			if knobs:
				self._live_pipe.draw_path(self._start_port, None, knobs[0].scenePos())

				#self.testPipe.setEnd(knobs[0])
			else:
				self._live_pipe.draw_path(self._start_port, None, pos)
				#
				# self.testPipe.setEnd(event)

		if self.LMB_state:
			# nodes could be moving
			self.scene.updatePipePaths()

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
			print "legality is {}".format(legality)
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

		self.scene.addItem(self._live_pipe)
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
		# if not isinstance(pipe.start, Knob):
		# 	raise RuntimeError("pipe start is {}, pipe ain't got no knob".format(
		# 		pipe.start))
		startAttr = start.attr
		endAttr = dest.attr
		legality = self.graph.checkLegalConnection(
			source=startAttr, dest=endAttr)
		return legality

	def makeRealConnection(self, source, dest):
		"""eyy"""
		self.graph.addEdge(source.attr, dest.attr)
		#self.addPipe(source, dest)
		self.sync()

	def addPipe(self, source, dest):
		newPipe = Pipe(start=source, end=dest)
		self.pipes.append(newPipe)
		self.scene.addItem(newPipe)

	# event effects #######
	# view
	def _items_near(self, pos, item_type=None, width=20, height=20):
		x, y = pos.x() - width, pos.y() - height
		rect = QtCore.QRect(x, y, width, height)
		items = []
		for item in self.scene.items(rect):
			if not item_type or isinstance(item, item_type):
				items.append(item)
		return items

	# tab
	def tabSearchToggle(self):
		pos = self._previous_pos

		state = not self.tabSearch.isVisible()
		if state:
			rect = self.tabSearch.rect()
			new_pos = QtCore.QPoint(pos.x() - rect.width() / 2,
									pos.y() - rect.height() / 2)
			self.tabSearch.move(new_pos)
			self.tabSearch.setVisible(True)
			rect = self.mapToScene(rect).boundingRect()
			self.tabSearch.setFocus()
			self.tabSearch.setSelection(0, len(self.tabSearch.text()))
			#self.scene.update(rect)
		else:
			self.tabSearch.setVisible(False)
			#self.clearFocus()

	def searchReceived(self, name):
		pos = self.mapToScene(self._previous_pos)
		self.scene.addNode(name, pos)

	# nodes
	def selectedNodes(self):
		return  self.scene.selectedNodes()

	def move_nodes(self, nodes, pos=None, offset=None):
		group = self.scene.createItemGroup(nodes)
		group_rect = group.boundingRect()
		if pos:
			x, y = pos
		else:
			pos = self.mapToScene(self._previous_pos)
			x = pos.x() - group_rect.center().x()
			y = pos.y() - group_rect.center().y()
		if offset:
			x += offset[0]
			y += offset[1]
		group.setPos(x, y)
		self.scene.destroyItemGroup(group)


	# zoom
	def _set_viewer_zoom(self, value):
		if value == 0.0:
			return
		scale = 0.9 if value < 0.0 else 1.1
		zoom = self.get_zoom()
		if ZOOM_MIN >= zoom:
			if scale == 0.9:
				return
		if ZOOM_MAX <= zoom:
			if scale == 1.1:
				return
		self.scale(scale, scale)

	def get_zoom(self):
		transform = self.transform()
		cur_scale = (transform.m11(), transform.m22())
		return float('{:0.2f}'.format(cur_scale[0] - 1.0))

	def reset_zoom(self):
		self.scale(1.0, 1.0)
		self.resetMatrix()

	def set_zoom(self, value=0.0):
		if value == 0.0:
			self.reset_zoom()
			return
		zoom = self.get_zoom()
		if zoom < 0.0:
			if not (ZOOM_MIN <= zoom <= ZOOM_MAX):
				return
		else:
			if not (ZOOM_MIN <= value <= ZOOM_MAX):
				return
		value = value - zoom
		self._set_viewer_zoom(value)

	def zoom_to_nodes(self, nodes):
		rect = self._combined_rect(nodes)
		self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
		if self.get_zoom() > 0.1:
			self.reset_zoom()

	def _set_viewer_pan(self, pos_x, pos_y):
		scroll_x = self.horizontalScrollBar()
		scroll_y = self.verticalScrollBar()
		scroll_x.setValue(scroll_x.value() - pos_x)
		scroll_y.setValue(scroll_y.value() - pos_y)

	# serialisation and regeneration
	def serialise(self):
		"""literally just save camera position"""

	@staticmethod
	def fromDict(regen):
		"""read out camera position"""

	# context stuff
	def buildContext(self):
		"""called on rightclick - gathers all available actions
		and adds them to default"""
		self.contextMenu.clearCustomEntries()

		nodeActions = { "nodes" : [self.getTileActions()]} # returns combined dict
		nodeExecActions = self.getTileExecActions()
		# print "nodeExecActions are {}".format(nodeExecActions)
		if nodeExecActions:
			nodeActions["nodes"].append(nodeExecActions)

		execActions = { "execution" : self.graph.getExecActions(
			nodes=[i.abstract for i in self.selectedNodes()])}
		ioActions = { "io" : self.getIoActions()}

		if nodeActions["nodes"]:
			#self.contextMenu.addSubMenu(name="nodes", nodeActions)
			# print "context building from {}".format(nodeActions)
			self.contextMenu.buildMenusFromDict(nodeActions)

		self.contextMenu.buildMenusFromDict(execActions)
		self.contextMenu.buildMenusFromDict(ioActions)

	def getTileExecActions(self):
		"""allows building specific tiles to specific stages"""
		actions = {}
		for i in self.selectedNodes():
			actions.update(i.abstract.getExecActions())
		return actions

	def mergeActionDicts(self, base, target):
		"""if two identical paths appear, an actionList is created"""
		for k, v in base.iteritems():
			if target.get(k):
				if isinstance(v, dict) and isinstance(target[k], dict):

					self.mergeActionDicts(v, target[k])
				elif isinstance(v, (ActionItem, ActionList)) and \
					isinstance(target[k], (ActionItem, ActionList)):
						v.addAction(target[k])
		return base


	def getTileActions(self):
		"""desperately, desperately need a better way to concatenate
		similar actions into the same menu"""
		actions = {}
		tileDicts = []
		if not self.selectedNodes():
			return {}
		for i in self.selectedNodes():
			# print "tile get actions is {}".format(i.getActions())
			actions.update(i.getActions())
			tileDicts.append(i.getActions())
		if len(tileDicts) == 1:
			return tileDicts[0]

		base = tileDicts[0]
		for i in tileDicts:
			base = self.mergeActionDicts(base, i)
		return base


	def getIoActions(self):
		"""actions for opening, saving etc"""
		saveAction = ActionItem(execDict={
			"func" : self.saveTilePile}, name="Save")
		saveAsAction = ActionItem(
			execDict={"func" : self.saveAsTilePile, "kwargs" : {"defaultPath" :self.savePath}},
			name="Save As")
		openAction = ActionItem(execDict={
			"func" : self.openTilePileFile, "kwargs" : {"path" : self.savePath}},
			name="Open")
		newAction = ActionItem(execDict={
			"func" : self.newTilePile}, name="New")

		return {i.name : i for i in [saveAction, saveAsAction, openAction, newAction]}

	# io for entire system, put here as this is the point of greatest
	# user interaction

	def newTilePile(self):
		"""clears graph"""
		self.graph.clearSession()
		self.sync()

	def openTilePileFile(self, path=None, force=False):
		""" loads file, then sets asset correctly etc """
		if not path:
			path = self.savePath
		serialised = self.loadTilePileInfo(path=path, force=force)
		if not serialised:
			return
		newAsset = pipeline.assetFromName(serialised["asset"])
		if newAsset.path != self.currentAsset.path:
			if not force:
				if not ConfirmDialogue.confirm(self, "confirm asset change"):
					return
		self.graph.clearSession()
		self.assetChanged.emit([newAsset])
		#self.graph.setAsset(newAsset)
		self.graph = self.graph.fromDict(serialised)
		self.sync()
		self.scene.regenUi(serialised)
		print("savePath after open is {}".format(self.savePath))
		pass

	def loadTilePileInfo(self, path=None, force=False):
		""" loads serialised information from disk """
		if force:
			tilePileFile = path
		else:
			path = pipeline.dirFromPath(path)
			tilePileFile = QtWidgets.QFileDialog.getOpenFileName(
				parent=self, caption="load tile pile", dir=path)[0]

		if not tilePileFile or not pipeline.checkFileExists(tilePileFile):
			return
		self.savePath = tilePileFile
		self.filePath = tilePileFile
		serialised = pipeline.ioinfo(mode="in", path=tilePileFile)
		#print "loaded data is {}".format(serialised)
		return serialised

	def saveAsTilePile(self, path=None, defaultPath=None):
		saveData = self.graph.serialise()
		self.scene.serialiseUi(saveData)
		if not defaultPath:
			defaultPath = self.savePath or self.currentAsset.path or ROOT_PATH
		if not path:
			print "current asset is {}".format(self.currentAsset.name)
			print "asset path is {}".format(self.currentAsset.path)
			tilePileFile = QtWidgets.QFileDialog.getSaveFileName(
				parent=self, caption="save this pile of tiles",
				dir=defaultPath)[0]
		else:
			tilePileFile = path

		if not tilePileFile:
			return

		if not pipeline.checkJsonFileExists(tilePileFile):
			edRig.pipeline.makeBlankFile(path=tilePileFile)
		pipeline.ioinfo(name="testPileSaveAs", mode="out",
		              info=saveData, path=tilePileFile)

		self.savePath = tilePileFile
		self.filePath = tilePileFile

		# save graph path to scene to open more quickly
		self.saveToScene()

	def saveTilePile(self):
		self.saveAsTilePile(path=self.filePath)

	def onAssetChanged(self, assetInfos):
		self.graph.setAsset(assetInfos[0]) # assetItem
		self.savePath = assetInfos[0].path
		# self.graph.setDataPath(assetInfos)
