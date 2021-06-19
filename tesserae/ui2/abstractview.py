# viewer widget for the abstract view
from PySide2 import QtCore, QtWidgets, QtGui

import edRig.pipeline
from edRig.tesserae.ui2.abstractscene import AbstractScene
from edRig.tesserae.abstractgraph import AbstractGraph
from edRig.tesserae.ui2.tabsearch import TabSearchWidget
# from edRig.tesserae.ui2.abstracttile import AbstractTile2, Knob, Pipe
from edRig.tesserae.ui3.abstracttile import AbstractTile2, Knob, Pipe
from edRig.tesserae.ui2.style import *
from edRig.tesserae.ui2.context import ContextMenu
from edRig.tesserae.constant import debugEvents
from edRig.tesserae.ui2.lib import ConfirmDialogue, KeyState
from edRig.structures import ActionItem, ActionList
from edRig import pipeline, ROOT_PATH

ZOOM_MIN = -0.95
ZOOM_MAX = 2.0

"""
view receives events first
"""

def widgets_at(pos):
	"""Return ALL widgets at `pos`

	Arguments:
		pos (QPoint): Position at which to get widgets

	"""

	widgets = []
	# widget_at = QtGui.qApp.widgetAt(pos)
	widget_at = QtWidgets.QApplication.instance().widgetAt(pos)


	while widget_at:
		widgets.append(widget_at)

		# Make widget invisible to further enquiries
		widget_at.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
		widget_at = QtWidgets.QApplication.instance().widgetAt(pos)

	# Restore attribute
	for widget in widgets:
		widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

	return widgets


class AbstractView(QtWidgets.QGraphicsView):
	"""simple class to view an graph's contents"""

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

		self.keyState = KeyState()

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

		#self.keyState.LMB = self.keyState.LMB
		self.RMB_state = False
		self.MMB_state = False
		self.shift_state = False
		self.ctrl_state = False
		self.alt_state = False

		self._previous_pos = 0,0
		self.testPipe = None #type: Pipe
		self._livePipe = None #type: Pipe
		self._prev_selection = []

		# tab search
		self.tabSearch = TabSearchWidget(parent=self)
		self.tabSearch.setItems(list(self.graph.registeredNodes.keys()))


		# signals
		self.tabSearch.searchSubmitted.connect(self.onSearchReceived)
		self.nodeDeleteCalled.connect( self.scene.onDeleteCalled )

		self._savePath = None
		self._filePath = None

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
		
	def mapToScene(self, val):
		if isinstance(val, QtCore.QPointF):
			val = val.toPoint()
		return super(AbstractView, self).mapToScene(val)

	def saveToScene(self):
		"""saves current file path"""
		currentInfo = pipeline.getSceneData()

		if self.savePath:

			currentInfo["tesserae.savePath"] = self.savePath
			currentInfo["tesserae.filePath"] = self.filePath
			currentInfo["tesserae.asset"] = self.currentAsset.path
		pipeline.saveSceneData(currentInfo)

	def loadFromScene(self, force=True):
		""" loads current file path
		if force, loads entire graph"""
		info = pipeline.getSceneData()

		if info["tesserae.asset"]:
			self.graph.setAsset( pipeline.AssetItem( info["tesserae.asset"]) )
		self.savePath = info["tesserae.savePath"]
		self.filePath = info["tesserae.filePath"]
		if force and pipeline.checkFileExists(self.filePath):
			print(("forcing open from scene, self save path is {}".format(self.filePath)))
			self.openTilePileFile(self.filePath, force=True)

	def _init_actions(self):
		# setup tab search shortcut.
		# couldn't find another way to override focusing
		tab = QtWidgets.QAction('Search Nodes', self)
		tab.setShortcut('tab')
		tab.triggered.connect(self.tabSearchToggle)
		self.addAction(tab)


	def sync(self):
		self.scene.sync()


	def wheelEvent(self, event):
		self.keyState.syncModifiers(event)
		event.ignore()
		#print("view wheel event accepted {}".format(event.isAccepted()))

		adjust = (event.delta() / 120) * 0.1
		#self.setViewerZoom(adjust, event.globalPos())
		self.setViewerZoom(adjust, event.pos())

	# def scrollEvent(self, event): # never called
	# 	print("view scrollEvent")

	def scrollContentsBy(self, dx, dy):
		""" parent class scroll function """
		#print("keystate shift {}".format(self.keyState.shift))

		if self.keyState.shift:
			#print("scrollContents setViewerZoom")
			self.setViewerZoom(dx * dy / 1200)
			return
		else:
			super(AbstractView, self).scrollContentsBy(dx, dy)
			pass

	def keyPressEvent(self, event):
		# print("view keyPressEvent", event.key())
		self.keyState.keyPressed(event)
		if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
			self.nodeDeleteCalled.emit()
			return True

		super(AbstractView, self).keyPressEvent(event)

	def contextMenuEvent(self, event):
		"""i'm really honestly quite sick of this softlocking my program"""
		super(AbstractView, self).contextMenuEvent(event)
		if event.isAccepted():
			return
		self.buildContext()
		self.contextMenu.exec_(event.globalPos())


	""" view receives events first - calling super passes them to scene """
	
	def dragMoveEvent(self, event:QtGui.QDragMoveEvent):
		if debugEvents: print("view dragMoveEvent")
		return super(AbstractView, self).dragMoveEvent(event)

	def mousePressEvent(self, event):
		if debugEvents: print ("view mousePress event")

		#check if any proxy widgets are under click
		pos = event.pos()
		found = self.items(pos)
		proxies = [i for i in found if isinstance(
			i, QtWidgets.QGraphicsProxyWidget)]
		# if proxies:
		# 	proxies[0].widget().mousePressEvent(event)
		# 	# event.accept()
		# 	# return True
		# 	#return

		super(AbstractView, self).mousePressEvent(event)
		if event.isAccepted():
			#print("view mousePress accepted, returning")
			return True

		self.keyState.mousePressed(event)

		# called BEFORE scene event
		alt_modifier = self.keyState.alt
		shift_modifier = self.keyState.shift

		items = self.itemsNear(self.mapToScene(event.pos()), None, 20, 20)
		nodes = [i for i in items if isinstance(i, AbstractTile2)]

		if self.keyState.LMB:
			# toggle extend node selection.
			if shift_modifier:
				for node in nodes:
					node.selected = not node.selected
			else:
				for i in self.selectedTiles():
					i.setSelected(False)
				for i in nodes:
					i.setSelected(True)

		self._origin_pos = event.pos()
		self._previous_pos = event.pos()
		self._prev_selection = self.selectedTiles()

		# close tab search
		if self.tabSearch.isVisible():
			self.tabSearchToggle()

		if alt_modifier:
			return

		# show selection selection marquee
		if self.keyState.LMB and not items:
			rect = QtCore.QRect(self._previous_pos, QtCore.QSize())
			rect = rect.normalized()
			map_rect = self.mapToScene(rect).boundingRect()
			self.scene.update(map_rect)
			self._rubber_band.setGeometry(rect)
			self._rubber_band.show()


		if event.button() == QtCore.Qt.LeftButton:
			# emit specific node selected signal
			if self.selectedTiles():
				#self.node_selected.emit()
				self.nodesSelected.emit(self.selectedTiles())

		self.beginDrawPipes(event)
		super(AbstractView, self).mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		self.keyState.mouseReleased(event)

		# hide selection marquee
		if self._rubber_band.isVisible():
			rect = self._rubber_band.rect()
			map_rect = self.mapToScene(rect).boundingRect()
			self._rubber_band.hide()
			self.scene.update(map_rect)

		self.endDrawPipes(event)
		super(AbstractView, self).mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		"""Managing selection first,
		then updating pipe paths"""

		if self.keyState.MMB or (self.keyState.LMB and self.keyState.alt):
			pos_x = (event.x() - self._previous_pos.x())
			pos_y = (event.y() - self._previous_pos.y())
			self._set_viewer_pan(pos_x, pos_y)
		elif self.keyState.RMB:
			pos_x = (event.x() - self._previous_pos.x())
			zoom = 0.1 if pos_x > 0 else -0.1
			#self.setViewerZoom(zoom)
			#self.set_zoom(zoom)
			# avoid context stuff interfering


		if self.keyState.LMB and self._rubber_band.isVisible():
			rect = QtCore.QRect(self._origin_pos, event.pos()).normalized()
			map_rect = self.mapToScene(rect).boundingRect()
			path = QtGui.QPainterPath()
			path.addRect(map_rect)
			self._rubber_band.setGeometry(rect)
			self.scene.setSelectionArea(path, QtCore.Qt.IntersectsItemShape)
			self.scene.update(map_rect)

			if self.keyState.shift and self._prev_selection:
				for node in self._prev_selection:
					if node not in self.selectedTiles():
						node.selected = True

		self._previous_pos = event.pos()

		# update pipe drawing
		self.updatePipePaths(event)

		super(AbstractView, self).mouseMoveEvent(event)

	def updatePipePaths(self, event):
		""" update test pipe"""
		if self.testPipe:
			pos = self.mapToScene(event.pos())
			# knobs = self.itemsNear(event.scenePos(), Knob, 5, 5)
			knobs = self.itemsNear(pos, Knob, 5, 5)
			if knobs:
				self._livePipe.drawPath(self._startPort, None, knobs[0].scenePos())

				#self.testPipe.setEnd(knobs[0])
			else:
				self._livePipe.drawPath(self._startPort, None, pos)
				#
				# self.testPipe.setEnd(event)

		if self.keyState.LMB:
			# nodes could be moving
			self.scene.updatePipePaths()

	def beginDrawPipes(self, event):
		"""triggered mouse press event for the scene (takes priority over viewer).
		 - detect selected pipe and start connection
		 - remap Shift and Ctrl modifier
		currently we control pipe connections from here"""
		self.keyState.keyPressed(event)

		if not self.keyState.alt:
			pos = self.mapToScene(event.pos())
			knobs = self.itemsNear(pos, Knob, 5, 5)
			if knobs:
				self.testPipe = self.beginTestConnection(knobs[0]) # begins test visual connection
				#self.testPipe.setEnd(event)


	def endDrawPipes(self, event):
		""" if a valid testPipe is created, check legality against graph
		before connecting in graph and view"""
		self.keyState.keyPressed(event)
		if isinstance(event.pos(), QtCore.QPointF):
			pos = event.pos().toPoint()
		else:
			pos = event.pos()
		pos = self.mapToScene(pos)
		if self.testPipe:
			# look for juicy knobs
			knobs = self.itemsNear(pos, Knob, 5, 5)
			if not knobs:
				# destroy test pipe
				self.endLiveConnection()

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
			self.endLiveConnection()

	def beginTestConnection(self, selected_port:Knob):
		"""	create new pipe for the connection.	"""
		if not selected_port:
			return
		self._startPort = selected_port
		self._livePipe = Pipe()
		self._livePipe.activate()
		self._livePipe.style = PIPE_STYLE_DASHED
		self._livePipe.start = self._startPort

		self.scene.addItem(self._livePipe)
		return self._livePipe

	def endLiveConnection(self):
		"""	delete live connection pipe and reset start port."""
		if self._livePipe:
			self._livePipe.delete()
			self.scene.removeItem(self._livePipe)
			self._livePipe = None
		self._startPort = None
		self.testPipe = None

	def checkLegalConnection(self, start:Knob, dest:Knob):
		"""checks with graph if attempted connection is legal
		ONLY WORKS ON KNOBS"""
		startAttr = start.tree
		endAttr = dest.tree
		legality = self.graph.checkLegalConnection(
			source=startAttr, dest=endAttr)
		return legality

	def makeRealConnection(self, source, dest):
		"""eyy"""
		self.graph.addEdge(source.tree, dest.tree)
		self.sync()

	def addPipe(self, source, dest):
		newPipe = Pipe(start=source, end=dest)
		self.pipes.append(newPipe)
		self.scene.addItem(newPipe)

	# event effects #######
	# view
	def itemsNear(self, pos, item_type=None, width=20, height=20):
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

	def onSearchReceived(self, name):
		pos = self.mapToScene(self._previous_pos)
		#self.scene.addNode(name, pos)
		# direct graph connection?
		self.graph.addNode(name)

	# nodes
	def selectedTiles(self):
		return  self.scene.selectedTiles()

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
	def setViewerZoom(self, value, pos=None):
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
		if not pos: return

		viewPos = QtCore.QPoint(self.transform().m31(), self.transform().m32() )
		vec = (pos - viewPos) * value
		#self.translate( vec.x(), vec.y())


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
		self.setViewerZoom(value)

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

	@property
	def posX(self):
		"""viewport x position"""
		return self.horizontalScrollBar().value()

	@property
	def posY(self):
		"""viewport Y position"""
		return self.verticalScrollBar().value()

	@property
	def camPos(self):
		"""return x and y of current view scroll"""
		return QtCore.QPoint(self.posX, self.posY)

	@property
	def camCentre(self):
		return self.mapToScene(self.viewport().rect().center())

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
			nodes=[i.abstract for i in self.selectedTiles()])}
		ioActions = { "io" : self.getIoActions()}

		if nodeActions["nodes"]:
			self.contextMenu.buildMenusFromDict(nodeActions)

		self.contextMenu.buildMenusFromDict(execActions)
		self.contextMenu.buildMenusFromDict(ioActions)

	def getTileExecActions(self):
		"""allows building specific tiles to specific stages"""
		actions = {}
		for i in self.selectedTiles():
			actions.update(i.abstract.getExecActions())
		return actions

	def mergeActionDicts(self, base, target):
		"""if two identical paths appear, an actionList is created"""
		for k, v in base.items():
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
		tileDicts = []
		if not self.selectedTiles():
			return {}
		for i in self.selectedTiles():
			# print "tile get actions is {}".format(i.getActions())
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
		print(("savePath after open is {}".format(self.savePath)))
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
			print(( "current asset is {}".format(self.currentAsset.name) ))
			print(( "asset path is {}".format(self.currentAsset.path) ))
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
