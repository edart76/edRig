# # base machinery for all visual nodes in TilePile
#
# from tree import Tree, TreeWidget
# from tree.ui.widget import AllEventEater
#
#
# from PySide2 import QtCore, QtWidgets, QtGui
# from edRig.tesserae.abstractnode import AbstractNode, AbstractAttr
# #from edRig.tesserae.ui2 import tilewidgets, tilesettings
# from edRig.tesserae.ui2 import tilewidgets
#
# from edRig.tesserae.ui2.style import *
#
#
# PIPE_STYLES = {
#     PIPE_STYLE_DEFAULT: QtCore.Qt.PenStyle.SolidLine,
#     PIPE_STYLE_DASHED: QtCore.Qt.PenStyle.DashDotDotLine,
#     PIPE_STYLE_DOTTED: QtCore.Qt.PenStyle.DotLine
# }
#
# entryHeight = 20
# nameBarHeight = 30
#
# """
# events are gathered from QGraphicsScene and view,
# passed through those objects,
# THEN passed to the proxy widgets.
#
# """
#
#
#
# class AbstractTile2(QtWidgets.QGraphicsItem):
# 	""" starting this over """
# 	def __init__(self, parent=None, abstractNode=None):
# 		super(AbstractTile2, self).__init__(parent)
# 		if not isinstance(abstractNode, AbstractNode):
# 			raise RuntimeError("no abstractNode provided!")
# 		self.abstract = abstractNode
#
# 		self.attrBlocks = [None, None] # input, output
# 		self.entries = {}
#
# 		self.nameTag = tilewidgets.NameTagWidget(self, abstractNode.nodeName)
# 		self.classTag = QtWidgets.QGraphicsTextItem(
# 			self.abstract.__class__.__name__, self)
#
# 		self.settingsWidg = self.addSettings(self.abstract.settings)
# 		self.settingsWidg.expandAll()
#
# 		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable) # ????
# 		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable) # ????
#
# 		# signals
# 		self.nameTag.value_changed.connect(self._onNameChange)
# 		self.actions = {}
# 		self.abstract.sync.connect(self.sync)
#
# 		# set reference to this tile on abstractNode
# 		self.abstract.ui = self
#
# 		# appearance
# 		self.width, self.height = self.getSize()
# 		self.entryHeight = 20
# 		self.colour = self.abstract.extras.get("colour", (50, 50, 120))
# 		self.borderColour = (200,200,250)
# 		textColour = QtGui.QColor(200, 200, 200)
# 		self.classTag.setDefaultTextColor(textColour)
# 		self.classTag.setPos(self.boundingRect().width(), 0)
#
#
# 	def sync(self):
# 		"""update attrBlocks"""
#
# 		# remove old entries
# 		for i in self.attrBlocks:
# 			self.scene().removeItem(i)
# 		self.attrBlocks = []
# 		self.entries.clear()
#
# 		# generate new blocks
# 		for i in (self.abstract.inputRoot, self.abstract.outputRoot):
# 			entry = TileEntry(parent=self,
# 			                  attrItem=i,
# 			                  text=False)
# 			entry.arrange()
# 			self.entries.update(entry.getEntryMap())
# 			self.attrBlocks.append(entry)
#
# 		# resizing
# 		self.width, self.height = self.getSize()
# 		self.arrange()
#
# 	def arrange(self):
# 		for i in self.attrBlocks:
# 			i.arrange()
# 		y = nameBarHeight # height of name and class tag
#
# 		self.attrBlocks[0].setPos(0, y)
# 		y += self.attrBlocks[0].rect().height() + 7
#
# 		self.attrBlocks[1].setPos(0, y)
# 		y += self.attrBlocks[0].rect().height() + 7
#
# 		y += 30
#
# 		self.settingsWidg.resizeToTree()
# 		self.settingsProxy.setGeometry( QtCore.QRect(0.0, self.height,
# 		                               self.settingsWidg.width(),
# 		                               self.settingsWidg.height() ) )
#
# 		#self.settingsProxy.setPos(0, self.height )
#
#
# 	def _onNameChange(self, widget, name):
# 		self.abstract.rename(name)
#
#
# 	def getSize(self):
# 		"""
# 		calculate minimum node size.
# 		"""
# 		minRect = self.nameTag.boundingRect()
# 		minWidth = minRect.x() + 150
# 		minHeight = minRect.y() + 20
#
# 		for i in self.attrBlocks:
# 			if not i:
# 				continue
# 			minHeight += i.boundingRect().height() + 10
#
# 		self.width = minWidth
# 		self.height = minHeight
# 		return minWidth, minHeight
#
# 	def boundingRect(self):
# 		minWidth, minHeight = self.getSize()
# 		return QtCore.QRect(0, 0, minWidth, minHeight)
#
# 	def paint(self, painter, option, widget):
# 		painter.save()
# 		self.getSize()
#
# 		baseBorder = 1.0
# 		rect = QtCore.QRectF(0.5 - (baseBorder / 2),
# 							 0.5 - (baseBorder / 2),
# 							 self.width + baseBorder,
# 							 self.height + baseBorder)
# 		radius_x = 2
# 		radius_y = 2
# 		path = QtGui.QPainterPath()
# 		path.addRoundedRect(rect, radius_x, radius_y)
# 		painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
# 		painter.drawPath(path)
#
# 		rect = self.boundingRect()
# 		bg_color = QtGui.QColor(*self.colour)
# 		painter.setBrush(bg_color)
# 		painter.setPen(QtCore.Qt.NoPen)
# 		#painter.drawRoundRect(rect, radius_x, radius_y)
# 		painter.drawRect(rect)
#
# 		if self.isSelected():
# 			painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
# 			painter.drawRoundRect(rect, radius_x, radius_y)
#
# 		label_rect = QtCore.QRectF(rect.left() + (radius_x / 2),
# 								   rect.top() + (radius_x / 2),
# 								   self.width - (radius_x / 1.25),
# 								   28)
# 		path = QtGui.QPainterPath()
# 		path.addRoundedRect(label_rect, radius_x / 1.5, radius_y / 1.5)
# 		painter.setBrush(QtGui.QColor(0, 0, 0, 50))
# 		painter.fillPath(path, painter.brush())
#
# 		border_width = 0.8
# 		border_color = QtGui.QColor(*self.borderColour)
# 		if self.isSelected():
# 			border_width = 1.2
# 			border_color = QtGui.QColor(*NODE_SEL_BORDER_COLOR)
# 		border_rect = QtCore.QRectF(rect.left() - (border_width / 2),
# 									rect.top() - (border_width / 2),
# 									rect.width() + border_width,
# 									rect.height() + border_width)
# 		path = QtGui.QPainterPath()
# 		path.addRoundedRect(border_rect, radius_x, radius_y)
# 		painter.setBrush(QtCore.Qt.NoBrush)
# 		painter.setPen(QtGui.QPen(border_color, border_width))
# 		painter.drawPath(path)
# 		#print "end paint"
#
# 		painter.restore()
#
# 	def addSettings(self, tree):
# 		"""create a new abstractTree widget and add it to the bottom of node"""
# 		self.settingsProxy = QtWidgets.QGraphicsProxyWidget(self)
# 		# self.settingsWidg = tilesettings.TileSettings(parent=None,
# 		#                                               tree= tree)
#
# 		#eater = AllEventEater(self.settingsProxy)
# 		#self.settingsProxy.installEventFilter(eater)
#
# 		# eater stops events from being sent DOWNWARDS
# 		# no use now
#
# 		self.settingsWidg = TreeWidget(parent=None,
# 		                               tree=tree)
# 		self.settingsProxy.setWidget(self.settingsWidg)
#
# 		# connect collapse and expand signals to update size properly
# 		# self.settingsWidg.collapsed.connect( self._resizeSettings )
# 		# self.settingsWidg.expanded.connect( self._resizeSettings )
#
# 		#self.addWidget
# 		return self.settingsWidg
#
# 	def getActions(self):
# 		return self.abstract.getAllActions()
#
# 	def serialise(self):
# 		"""save position in view"""
# 		return {
# 			"pos" :	(self.pos().x(), self.pos().y()),
# 			}
#
# # class AbstractTile(QtWidgets.QGraphicsItem):
# # 	"""base for any tile in the ui"""
# #
# # 	@property
# # 	def pipes(self):
# # 		"""all visual pipes connected to this tile"""
# # 		p = []
# # 		for i in self.knobs:
# # 			#if hasattr(i, "pipes"):
# # 			p += i.pipes
# # 		return p
# #
# # 	@property
# # 	def knobs(self):
# # 		return [v.knob for v in list(self.entries.values()) if v.knob]
# #
# # 	def getKnob(self, knobName):
# # 		"""you know that feeling when you need a very specific kind of knob"""
# # 		return self.entries[knobName].knob
# #
# # 	# signal responses
# # 	def _onNameTagChange(self, widget, name):
# # 		self.abstract.rename(name)
# #
# # 	def setSelected(self, selected):
# # 		self.selected = selected
# # 		super(AbstractTile, self).setSelected(selected)
# #
# # 	# visuals
# # 	def boundingRect(self):
# # 		width, height = self.syncSize()
# # 		return QtCore.QRectF(0.0, 0.0, width, height)
# #
# # 	def arrangeText(self):
# # 		self.classTag.setPos(self.boundingRect().width(), 0)
# #
# #
# # 	def setTextColour(self, color):
# # 		"""set colours of text categories used in tile"""
# # 		text_color = QtGui.QColor(*color)
# # 		self.classTag.setDefaultTextColor(text_color)
# #
# #
# # 	@property
# # 	def icon(self):
# # 		return self._properties['icon']
# #
# # 	@icon.setter
# # 	def icon(self, path=None):
# # 		self._properties['icon'] = path
# # 		path = path or ICON_NODE_BASE
# # 		pixmap = QtGui.QPixmap(path)
# # 		pixmap = pixmap.scaledToHeight(NODE_ICON_SIZE,
# # 									   QtCore.Qt.SmoothTransformation)
# # 		self._icon_item.setPixmap(pixmap)
# # 		#if self.scene():
# # 		#	self.post_init()
# #
# # 	@property
# # 	def width(self):
# # 		return self._width
# #
# # 	@width.setter
# # 	def width(self, width=0.0):
# # 		#w, h = self.syncSize()
# # 		#self._width = width if width > w else w
# # 		#width = width if width > w else w
# # 		#self._width = width
# # 		self._width = width
# #
# # 	@property
# # 	def height(self):
# # 		return self._height
# #
# # 	@height.setter
# # 	def height(self, height=0.0):
# #
# # 		self._height = height
# #
# # 	def serialise(self):
# # 		"""save position in view"""
# # 		return {
# # 			"pos" :	(self.pos().x(), self.pos().y()),
# # 			}
#
#
# class TileEntry(QtWidgets.QGraphicsRectItem):
# 	"""individual shelf for knob and associated widget
# 	 """
# 	def __init__(self, parent=None, attrItem:AbstractAttr=None,
# 	             text=True, depth=0):
# 		if not attrItem:
# 			raise RuntimeError("no attrItem supplied!")
# 		super(TileEntry, self).__init__(parent)
#
# 		self.attr = attrItem
# 		self.name = attrItem.name
# 		self.dataType = attrItem.dataType
# 		self.depth = depth
#
#
# 		# base visual dimensions
# 		self.edgePad = 5
# 		self.unitHeight = entryHeight
#
# 		self.setRect(0,0,self.parentItem().boundingRect().width() - self.edgePad,
# 		             self.unitHeight)
# 		depth += 1
#
# 		self.children = [ TileEntry(
# 			parent=self, attrItem=i, depth=depth)
# 				for i in attrItem.branches ]
#
#
# 		self.extras = self.attr.extras
# 		self.role = attrItem.role
# 		self.widg = None
# 		self.label = None
# 		self.knob = None
#
# 		# overridden later by arrange()
# 		if attrItem.isConnectable():
# 			self.knob = Knob(self, attr=self.attr)
# 		else:
# 			self.knob = None
#
# 		self.setToolTip(self.attr.desc)
#
# 		self.text = QtWidgets.QGraphicsTextItem(self.attr.name, self)
# 		self.text.adjustSize()
# 		if not text:
# 			self.text.setVisible( False )
#
# 		self.pen = QtGui.QPen()
# 		self.brush = QtGui.QBrush()
# 		self.setPen(self.pen)
# 		self.setBrush(self.brush)
#
# 		#self.arrange()
#
# 	@property
# 	def width(self):
# 		return self.boundingRect().width()
# 	@property
# 	def height(self):
# 		return self.boundingRect().height()
#
# 	def onConnectionMade(self):
# 		"""disable widget if it exists"""
# 		if self.widg and self.role == "input":
# 			self.widg.disable()
#
# 	def onConnectionBroken(self, dest):
# 		"""disable widget if it exists"""
# 		if self.widg and self.role == "input":
# 			self.widg.enable()
#
# 	# def setAttrValue(self, name, val):
# 	# 	"""given tuple of (name, value) when widget changes"""
# 	# 	self.attr.value = val
#
# 	def getEntryMap(self):
# 		""" returns map of {address : entry} for all child entries """
# 		entryMap = {self.attr.stringAddress() : self}
# 		for i in self.children:
# 			entryMap.update(i.getEntryMap())
# 		return entryMap
#
#
#
# 	def arrange(self, parentWidth=None, depth=0, n=0, d=0):
# 		"""recursively lay out tree structure
# 		 """
# 		depth = self.depth
# 		f = 1 if self.role == "output" else -1
#
# 		y = n * (self.unitHeight + 3)
# 		x = (depth - 1) * 5 * f
# 		depth += 1
#
# 		y +=3
#
# 		self.setPos(x, y)
#
# 		for i in self.children:
# 			i.arrange(depth=depth, n=n)
# 			n += 1
#
# 		height = sum([i.rect().height() for i in self.children])
# 		height = height + self.unitHeight
#
# 		mainWidth = self.rect().width()
# 		parentWidth = parentWidth or self.parentItem().width
#
# 		self.setRect( 0, 0, parentWidth, height)
#
# 		if self.label:
# 			labelRect = self.label.boundingRect()
# 			self.label.setPos(0, 0)
#
# 		# place text outside node
# 		textBox = self.text.boundingRect()
# 		textWidth = textBox.width() + 30
#
# 		if self.role == "output":
# 			x = mainWidth
# 			textX = mainWidth - textWidth
# 			# if self.knob:
# 			# 	textX = mainWidth + 30
# 			# else: textX = mainWidth + 5
# 		else:
# 			# position knob on left
# 			x = -20
# 			#textX = textWidth * -1
# 			textX = 20
# 		if self.knob:
# 			knobY = self.height /2.0 - self.knob.boundingRect().height() / 2.0
# 			self.knob.setPos(x, 0)
# 		self.text.setPos(textX, 1)
#
#
# 	def makeWidg(self):
# 		name = self.attr.name
# 		value = self.attr.value
# 		# print ""
# 		# print "widg attr is {}, value is {}".format(self.attr, self.attr.value)
# 		if self.dataType == "int":
# 			widg = tilewidgets.NodeIntSpinbox(parent=self, name=name,
# 			                                  value=value, min=self.extras.get("min"),
# 			                                  max=self.extras.get("max"))
# 		elif self.dataType == "float":
# 			widg = tilewidgets.NodeFloatSpinbox(parent=self, name=name,
# 			                                  value=value, min=self.extras.get("min"),
# 			                                  max=self.extras.get("max"))
# 		elif self.dataType == "enum":
# 			widg = tilewidgets.NodeComboBox(parent=self, name=name,
# 			                                value=value,
# 			                                items= self.extras.get("items"))
# 		elif self.dataType == "string":
# 			widg = tilewidgets.NodeLineEdit(parent=self, name=name,
# 			                                text=value)
# 		elif self.dataType == "boolean":
# 			widg = tilewidgets.NodeCheckBox(parent=self, name=name,
# 			                                state=value)
# 		elif self.dataType == "colour":
# 			widg = tilewidgets.NodeColourBox(parent=self, name=name,
# 			                                 value=value)
# 		else:
# 			raise RuntimeError("datatype {} not associated with tileWidget".format(
# 				self.dataType))
# 		return widg
#
# class PassthroughTileEntry(TileEntry):
# 	"""same as above but for pass-through attributes
# 	extraAttr MUST be an output"""
#
# 	def __init__(self, extraAttr=None, *args, **kwargs):
# 		"""input attr still informs the main entry body"""
# 		if extraAttr.role != "output":
# 			raise RuntimeError("passthrough tileEntry called incorrectly,"
# 			                   "extraAttr must be output")
# 		super(PassthroughTileEntry, self).__init__(*args, **kwargs)
# 		if self.attr.role != "input":
# 			raise RuntimeError("passthrough tileEntry called incorrectly,"
# 			                   "first attr must be input")
# 		self.extraAttr = extraAttr
# 		self.role = "passthrough"
#
# 		self.extraText = QtWidgets.QGraphicsTextItem(self.extraAttr.name, self)
# 		self.extraText.adjustSize()
#
# 		self.extraKnob = Knob(self, attr=self.extraAttr)
#
# 		self.arrangeExtra()
#
#
# 	def arrangeExtra(self):
# 		"""someday go back and refactor this, but for now it's fine"""
#
# 		# place text outside node
# 		textBox = self.extraText.boundingRect()
# 		textWidth = textBox.width() + 30
# 		mainWidth = self.rect().width()
#
# 		x = mainWidth
# 		textX = mainWidth + 30
# 		knobY = self.height /2.0 - self.extraKnob.boundingRect().height() / 2.0
# 		self.extraKnob.setPos(x, knobY)
# 		self.extraText.setPos(textX, 1)
#
#
# class Knob(QtWidgets.QGraphicsRectItem):
# 	"""handle marking inputs and outputs"""
# 	def __init__(self, parent=None, attr=None, extras={}):
# 		# parent is qGraphicsWidget, attr is AttrItem
# 		super(Knob, self).__init__(parent)
# 		self.extras = dict(extras)
# 		self.baseSize = 20
# 		self.setRect(0,0, self.baseSize, self.baseSize)
# 		if not attr:
# 			raise RuntimeError("no attrItem supplied")
# 		#self.attr = attr
# 		self.role = self.attr.role
# 		self.name = self.attr.name
# 		self.colour = self.attr.colour
# 		self.pipes = []
# 		self.pen = QtGui.QPen()
# 		self.pen.setStyle(QtCore.Qt.NoPen)
# 		self.brush = QtGui.QBrush(QtGui.QColor(*self.colour),
# 		                          bs=QtCore.Qt.SolidPattern)
# 		#self.brush.setColor()
# 		self.setPen(self.pen)
# 		self.setBrush(self.brush)
# 		self.setAcceptHoverEvents(True)
#
# 	@property
# 	def attr(self):
# 		return self.parentItem().attr
#
# 	def __repr__(self):
# 		return self.name
#
# 	# visuals
# 	def hoverEnterEvent(self, event):
# 		"""tweak to allow knobs to expand pleasingly when you touch them"""
# 		self.setTumescent()
#
# 	def hoverLeaveEvent(self, event):
# 		"""return knobs to normal flaccid state"""
# 		self.setFlaccid()
#
# 	def setTumescent(self):
# 		scale = 1.3
# 		new = int(self.baseSize * scale)
# 		newOrigin = (new - self.baseSize) / 2
# 		self.setRect(-newOrigin, -newOrigin, new, new)
#
# 	def setFlaccid(self):
# 		self.setRect(0, 0, self.baseSize, self.baseSize)
#
# class Pipe(QtWidgets.QGraphicsPathItem):
# 	"""tis a noble thing to be a bridge between knobs"""
#
# 	def __init__(self, start=None, end=None, edge=None):
# 		super(Pipe, self).__init__()
# 		self.setZValue(Z_VAL_PIPE)
# 		self.setAcceptHoverEvents(True)
# 		self._color = start.colour if start else PIPE_DEFAULT_COLOR
# 		self._style = PIPE_STYLE_DEFAULT
# 		self._active = False
# 		self._highlight = False
# 		self._start = start
# 		self._end = end
# 		self.pen = None
# 		self.setFlags(
# 			QtWidgets.QGraphicsItem.ItemIsSelectable
# 		)
#
# 		self.edge = edge
#
#
# 	def setSelected(self, selected):
# 		if selected:
# 			self.highlight()
# 		if not selected:
# 			self.reset()
# 		super(Pipe, self).setSelected(selected)
#
# 	def paint(self, painter, option, widget):
# 		color = QtGui.QColor(*self._color)
# 		pen_style = PIPE_STYLES.get(self.style)
# 		pen_width = PIPE_WIDTH
# 		if self._active:
# 			color = QtGui.QColor(*PIPE_ACTIVE_COLOR)
# 		elif self._highlight:
# 			color = QtGui.QColor(*PIPE_HIGHLIGHT_COLOR)
# 			pen_style = PIPE_STYLES.get(PIPE_STYLE_DEFAULT)
#
# 		if self.start and self.end:
# 			# use later for proper freezing/approval
# 			pass
# 			# in_node = self.start.node
# 			# out_node = self.end.node
# 			# if in_node.disabled or out_node.disabled:
# 			# 	color.setAlpha(200)
# 			# 	pen_width += 0.2
# 			# 	pen_style = PIPE_STYLES.get(PIPE_STYLE_DOTTED)
#
# 		if self.isSelected():
# 			#painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
# 			#colour = QtGui.QColor(200, 200, 100)
# 			# self._highlight = True
# 			pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
# 			pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
#
# 		else:
# 			pen = QtGui.QPen(color, pen_width)
# 			pen.setStyle(pen_style)
#
# 		pen.setCapStyle(QtCore.Qt.RoundCap)
#
# 		painter.setPen(self.pen or pen)
# 		painter.setRenderHint(painter.Antialiasing, True)
# 		painter.drawPath(self.path())
#
# 	def drawPath(self, startPort, endPort, cursorPos=None):
# 		if not startPort:
# 			return
# 		offset = (startPort.boundingRect().width() / 2)
# 		pos1 = startPort.scenePos()
# 		pos1.setX(pos1.x() + offset)
# 		pos1.setY(pos1.y() + offset)
# 		if cursorPos:
# 			pos2 = cursorPos
# 		elif endPort:
# 			offset = startPort.boundingRect().width() / 2
# 			pos2 = endPort.scenePos()
# 			pos2.setX(pos2.x() + offset)
# 			pos2.setY(pos2.y() + offset)
# 		else:
# 			return
#
# 		line = QtCore.QLineF(pos1, pos2)
# 		path = QtGui.QPainterPath()
# 		path.moveTo(line.x1(), line.y1())
#
# 		# if self.viewer_pipe_layout() == PIPE_LAYOUT_STRAIGHT:
# 		# 	path.lineTo(pos2)
# 		# 	self.setPath(path)
# 		# 	return
#
# 		ctrOffsetX1, ctrOffsetX2 = pos1.x(), pos2.x()
# 		tangent = ctrOffsetX1 - ctrOffsetX2
# 		tangent = (tangent * -1) if tangent < 0 else tangent
#
# 		maxWidth = startPort.parentItem().boundingRect().width() / 2
# 		tangent = maxWidth if tangent > maxWidth else tangent
#
# 		if startPort.role == "input":
# 			ctrOffsetX1 -= tangent
# 			ctrOffsetX2 += tangent
# 		elif startPort.role == "output":
# 			ctrOffsetX1 += tangent
# 			ctrOffsetX2 -= tangent
#
# 		ctrPoint1 = QtCore.QPointF(ctrOffsetX1, pos1.y())
# 		ctrPoint2 = QtCore.QPointF(ctrOffsetX2, pos2.y())
# 		path.cubicTo(ctrPoint1, ctrPoint2, pos2)
# 		self.setPath(path)
#
# 	def redrawPath(self):
# 		"""updates path shape"""
# 		self.drawPath(self.start, self.end)
#
# 	def activate(self):
# 		self._active = True
# 		pen = QtGui.QPen(QtGui.QColor(*PIPE_ACTIVE_COLOR), 2)
# 		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
# 		self.setPen(pen)
#
# 	def active(self):
# 		return self._active
#
# 	def highlight(self):
# 		self._highlight = True
# 		pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
# 		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
# 		self.setPen(pen)
#
# 	def highlighted(self):
# 		return self._highlight
#
# 	def reset(self):
# 		self._active = False
# 		self._highlight = False
# 		pen = QtGui.QPen(QtGui.QColor(*self.color), 2)
# 		pen.setStyle(PIPE_STYLES.get(self.style))
# 		self.setPen(pen)
#
# 	@property
# 	def start(self):
# 		return self._start
#
# 	@start.setter
# 	def start(self, port):
# 		if isinstance(port, Knob) or not port:
# 			self._start = port
# 		else:
# 			self._start = None
#
# 	@property
# 	def end(self):
# 		return self._end
#
# 	@end.setter
# 	def end(self, port):
# 		if isinstance(port, Knob) or not port:
# 			self._end = port
# 		else:
# 			self._end = None
#
# 	@property
# 	def color(self):
# 		return self._color
#
# 	@color.setter
# 	def color(self, color):
# 		self._color = color
#
# 	@property
# 	def style(self):
# 		return self._style
#
# 	@style.setter
# 	def style(self, style):
# 		self._style = style
#
#
#
#
#
#
#
