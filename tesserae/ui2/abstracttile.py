# base machinery for all visual nodes in TilePile
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tesserae.abstractnode import AbstractNode, AbstractAttr
from edRig.tesserae.ui2 import tilewidgets, tilesettings
from edRig.tesserae.ui2.style import *
#import math


PIPE_STYLES = {
    PIPE_STYLE_DEFAULT: QtCore.Qt.PenStyle.SolidLine,
    PIPE_STYLE_DASHED: QtCore.Qt.PenStyle.DashDotDotLine,
    PIPE_STYLE_DOTTED: QtCore.Qt.PenStyle.DotLine
}

entryHeight = 20
nameBarHeight = 30

class AbstractTile(QtWidgets.QGraphicsItem):
	"""base for any tile in the ui"""

	"""connection events are collected in viewer, passed to graph, verified and enacted
	then call sync on affected nodes"""

	def __init__(self, parent=None, abstractNode=None, scene=None, **kwargs):
		if not isinstance(abstractNode, AbstractNode):
			raise RuntimeError("no abstractNode provided!")
		self.abstract = abstractNode
		self.name = abstractNode.nodeName
		super(AbstractTile, self).__init__(parent)
		self.scene = scene
		self.extras = dict(kwargs)
		self.attrBlocks = [None, None] # input, output,  neutral(?)
		self.entries = {} # every individual tile entry from blocks

		self._width = 30
		self._height = 30
		self.entryHeight = 20

		self.selected = False
		self.colour = self.abstract.colour
		self.borderColour = (200,200,250)

		# widgets
		self.nameTag = tilewidgets.NameTagWidget(self, abstractNode.nodeName)
		self.classTag = QtWidgets.QGraphicsTextItem(
			self.abstract.__class__.__name__, self)

		self.settingsWidg = self.addSettings(self.abstract.settings)
		self.memoryWidg = None # soon

		# flags?
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable) # ????
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable) # ????

		#print "abstract inputs are {}".format(self.abstract.inputs)

		self.sync()


		# arrange items
		self.arrangeText()
		#self.arrangeEntries()

		self.setTextColour((200, 200, 200))

		# signals
		self.nameTag.value_changed.connect(self._onNameChange)
		self.actions = {}
		self.abstract.sync.connect(self.sync)

	@property
	def inBlock(self):
		return self.attrBlocks[0]
	@property
	def outBlock(self):
		return self.attrBlocks[1]

	def _resizeSettings(self, *args, **kwargs):
		self.syncSize()
		self.settingsWidg.resizeToTree()
		#self.settingsProxy.resize(self.width, self.settingsWidg.height() )
		self.settingsProxy.resize(self.settingsWidg.width(),
		                          self.settingsWidg.height() )
		#self.settingsProxy.resize(self.width, 500 )
		# self.settingsProxy.adjustSize() # does not work properly
		self.settingsProxy.setPos(0, self.height )

	def addSettings(self, tree):
		"""create a new abstractTree widget and add it to the bottom of node"""
		self.settingsProxy = QtWidgets.QGraphicsProxyWidget(self)
		self.settingsWidg = tilesettings.TileSettings(parent=None,
		                                              tree= tree)

		# def _resizeSettings(*args, **kwargs):
		# 	self.settingsProxy.resize(self.width, settingsWidg.height() * 1.5)

		self.settingsProxy.setWidget(self.settingsWidg)

		# connect collapse and expand signals to update size properly
		self.settingsWidg.collapsed.connect( self._resizeSettings )
		self.settingsWidg.expanded.connect( self._resizeSettings )
		self._resizeSettings()

		#self.addWidget
		return self.settingsWidg

	def sync(self):
		"""update attrBlocks"""
		self.abstract.log("")
		self.abstract.log("begin abstractTile sync")
		# self.abstract.log("abstract attrs are {}, {}".format(
		# 	self.abstract.inputs, self.abstract.outputs))

		# remove old entries
		for i in self.attrBlocks:
			self.scene.removeItem(i)
		self.attrBlocks = [None, None]
		self.entries.clear()

		# generate new blocks
		inEntry = TileEntry(parent=self,
		                  attrItem=self.abstract.inputRoot,
		                  scene=self.scene, text=False)
		self.attrBlocks[0] = inEntry
		inEntry.arrange()

		outEntry = TileEntry(parent=self,
		                  attrItem=self.abstract.outputRoot,
		                  scene=self.scene, text=False)
		self.attrBlocks[1] = outEntry
		outEntry.arrange()


		# resizing
		self.width, self.height = self.syncSize()
		# for i in self.entries.values():
		# 	i.setRect(0,0, self.width, self.entryHeight)

		self.arrange()

	def arrange(self):
		for i in self.attrBlocks:
			i.arrange()
		y = nameBarHeight # height of name and class tag

		self.attrBlocks[0].setPos(0, y)
		y += self.attrBlocks[0].rect().height() + 7

		self.attrBlocks[1].setPos(0, y)
		y += self.attrBlocks[0].rect().height() + 7

		y += 30

		self.syncSize()
		self._resizeSettings()


	def syncSize(self):
		"""
		calculate minimum node size.
		"""
		width = 0.0
		minRect = self.nameTag.boundingRect()
		minWidth = minRect.x() + 150
		minHeight = minRect.y() + 20
		# for i in self.entries.values():
		# 	minHeight += entryHeight + 2
		# 	minWidth = max(minWidth, i.boundingRect().width())
		for i in self.attrBlocks:
			if not i:
				continue
			minHeight += i.boundingRect().height() + 5
			#minWidth = max( minWidth, i.boundingRect().width() )


		#self.prepareGeometryChange()
		self.width = minWidth
		self.height = minHeight
		self.update()
		return minWidth, minHeight

	def getActions(self):
		return self.abstract.getAllActions()

	@property
	def pipes(self):
		"""all visual pipes connected to this tile"""
		p = []
		for i in self.knobs:
			#if hasattr(i, "pipes"):
			p += i.pipes
		return p

	@property
	def knobs(self):
		return [v.knob for v in self.entries.values() if v.knob]

	def getKnob(self, knobName):
		"""you know that feeling when you need a very specific kind of knob"""
		return self.entries[knobName].knob

	# signal responses
	def _onNameChange(self, widget, name):
		self.abstract.rename(name)

	def setSelected(self, selected):
		self.selected = selected
		super(AbstractTile, self).setSelected(selected)

	# visuals
	def boundingRect(self):
		width, height = self.syncSize()
		return QtCore.QRectF(0.0, 0.0, width, height)

	def arrangeText(self):
		self.classTag.setPos(self.boundingRect().width(), 0)


	def setTextColour(self, color):
		"""set colours of text categories used in tile"""
		text_color = QtGui.QColor(*color)
		self.classTag.setDefaultTextColor(text_color)

	def paint(self, painter, option, widget):
		painter.save()

		bg_border = 1.0
		rect = QtCore.QRectF(0.5 - (bg_border / 2),
							 0.5 - (bg_border / 2),
							 self.width + bg_border,
							 self.height + bg_border)
		radius_x = 2
		radius_y = 2
		path = QtGui.QPainterPath()
		path.addRoundedRect(rect, radius_x, radius_y)
		painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
		painter.drawPath(path)

		rect = self.boundingRect()
		bg_color = QtGui.QColor(*self.colour)
		painter.setBrush(bg_color)
		painter.setPen(QtCore.Qt.NoPen)
		#painter.drawRoundRect(rect, radius_x, radius_y)
		painter.drawRect(rect)

		if self.selected:
			painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
			painter.drawRoundRect(rect, radius_x, radius_y)

		label_rect = QtCore.QRectF(rect.left() + (radius_x / 2),
								   rect.top() + (radius_x / 2),
								   self.width - (radius_x / 1.25),
								   28)
		path = QtGui.QPainterPath()
		path.addRoundedRect(label_rect, radius_x / 1.5, radius_y / 1.5)
		painter.setBrush(QtGui.QColor(0, 0, 0, 50))
		painter.fillPath(path, painter.brush())

		border_width = 0.8
		border_color = QtGui.QColor(*self.borderColour)
		if self.selected:
			border_width = 1.2
			border_color = QtGui.QColor(*NODE_SEL_BORDER_COLOR)
		border_rect = QtCore.QRectF(rect.left() - (border_width / 2),
									rect.top() - (border_width / 2),
									rect.width() + border_width,
									rect.height() + border_width)
		path = QtGui.QPainterPath()
		path.addRoundedRect(border_rect, radius_x, radius_y)
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.setPen(QtGui.QPen(border_color, border_width))
		painter.drawPath(path)
		#print "end paint"

		painter.restore()

	# set positions of widgets
	def positionName(self):
		"""centres nametag widget"""
		nameBox = self.nameTag.boundingRect()
		#x = (self.width / 2)# - (nameBox.width() / 2)
		x = self.width
		self.nameTag.setPos(x, 1.0)


	def delete(self):
		for i in self.entries.values():
			#self.deleteKnob(i)
			i.delete()
		self.scene.deleteNode(self)

	@property
	def icon(self):
		return self._properties['icon']

	@icon.setter
	def icon(self, path=None):
		self._properties['icon'] = path
		path = path or ICON_NODE_BASE
		pixmap = QtGui.QPixmap(path)
		pixmap = pixmap.scaledToHeight(NODE_ICON_SIZE,
									   QtCore.Qt.SmoothTransformation)
		self._icon_item.setPixmap(pixmap)
		#if self.scene():
		#	self.post_init()

	@property
	def width(self):
		return self._width

	@width.setter
	def width(self, width=0.0):
		#w, h = self.syncSize()
		#self._width = width if width > w else w
		#width = width if width > w else w
		#self._width = width
		self._width = width

	@property
	def height(self):
		return self._height

	@height.setter
	def height(self, height=0.0):
		# w, h = self.syncSize()
		# h = 70 if h < 70 else h
		# self._height = height if height > h else h
		#height = height if height > h else h
		#self._height = height
		self._height = height

	def serialise(self):
		"""save position in view"""
		return {
			"pos" :	(self.pos().x(), self.pos().y()),
			}


class TileEntry(QtWidgets.QGraphicsRectItem):
	"""individual shelf for knob and associated widget
	this sadly locks us into left-to-right rectangular widgets...for now...
	should read and arrange attributes recursively from tree leaves
	doesn't do that yet """
	def __init__(self, parent=None, attrItem=None, scene=None,
	             text=True):
		if not attrItem:
			raise RuntimeError("no attrItem supplied!")
		#print("attritem {} type {}".format( attrItem.name, type(attrItem)))
		super(TileEntry, self).__init__(parent)

		self.parent = parent
		self.scene = scene
		self.attr = attrItem
		self.name = attrItem.name
		self.dataType = attrItem.dataType

		# base visual dimensions
		self.edgePad = 5
		self.unitHeight = entryHeight

		# update parent with shared entry dict
		self.entries = self.parent.entries
		self.entries[ self.name ] = self

		self.setRect(0,0,self.parent.boundingRect().width() - self.edgePad,
		             self.unitHeight)

		self.children = [ TileEntry(
			parent=self, attrItem=i, scene=self.scene)
				for i in attrItem.children if isinstance(i, AbstractAttr) ]


		self.extras = self.attr.extras
		self.role = attrItem.role
		self.widg = None
		self.label = None
		self.knob = None

		# overridden later by arrange()
		if attrItem.isConnectable():
			self.knob = Knob(self, attr=self.attr)
		else:
			self.knob = None

		self.setToolTip(self.attr.desc)

		self.text = QtWidgets.QGraphicsTextItem(self.attr.name, self)
		self.text.adjustSize()
		if not text:
			self.text.setVisible( False )

		self.pen = QtGui.QPen()
		self.brush = QtGui.QBrush()
		self.setPen(self.pen)
		self.setBrush(self.brush)

		#self.arrange()

	@property
	def width(self):
		return self.boundingRect().width()
	@property
	def height(self):
		return self.boundingRect().height()

	def onConnectionMade(self):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.disable()

	def onConnectionBroken(self, dest):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.enable()

	def setAttrValue(self, name, val):
		"""given tuple of (name, value) when widget changes"""
		self.attr.value = val

	def sync(self):
		"""disable widget if connected, update widget value etc"""

	def arrange(self, parentWidth=None, depth=0, n=0, d=0):
		"""recursively lay out tree structure
		not sure this is totally solid yet but for now it works
		 """

		f = 1 if self.role == "output" else -1

		y = n * (self.unitHeight + 3)
		x = (depth - 1) * 5 * f
		depth += 1

		y +=3

		self.setPos(x, y)
		#n += 1

		for i in self.children:
			# n += 1
			i.arrange(depth=depth, n=n)
			n += 1

		n = d
		height = sum([i.rect().height() for i in self.children])
		height = height + self.unitHeight

		if self.children:
			height += 3

		# no more widgets
		midHeight = self.height / 2.0
		midWidth = self.width / 2.0
		mainWidth = self.rect().width()
		parentWidth = parentWidth or self.parent.width


		#self.setRect( x, y, parentWidth, height)
		self.setRect( 0, 0, parentWidth, height)


		if self.label:
			labelRect = self.label.boundingRect()
			self.label.setPos(0, 0)

		# place text outside node
		textBox = self.text.boundingRect()
		textWidth = textBox.width() + 30

		if self.role == "output":
			x = mainWidth
			if self.knob:
				textX = mainWidth + 30
			else: textX = mainWidth + 5
		else:
			# position knob on left
			x = -20
			textX = textWidth * -1
		if self.knob:
			knobY = self.height /2.0 - self.knob.boundingRect().height() / 2.0
			self.knob.setPos(x, 0)
		self.text.setPos(textX, 1)


	def makeWidg(self):
		name = self.attr.name
		value = self.attr.value
		# print ""
		# print "widg attr is {}, value is {}".format(self.attr, self.attr.value)
		if self.dataType == "int":
			widg = tilewidgets.NodeIntSpinbox(parent=self, name=name,
			                                  value=value, min=self.extras.get("min"),
			                                  max=self.extras.get("max"))
		elif self.dataType == "float":
			widg = tilewidgets.NodeFloatSpinbox(parent=self, name=name,
			                                  value=value, min=self.extras.get("min"),
			                                  max=self.extras.get("max"))
		elif self.dataType == "enum":
			widg = tilewidgets.NodeComboBox(parent=self, name=name,
			                                value=value,
			                                items= self.extras.get("items"))
		elif self.dataType == "string":
			widg = tilewidgets.NodeLineEdit(parent=self, name=name,
			                                text=value)
		elif self.dataType == "boolean":
			widg = tilewidgets.NodeCheckBox(parent=self, name=name,
			                                state=value)
		elif self.dataType == "colour":
			widg = tilewidgets.NodeColourBox(parent=self, name=name,
			                                 value=value)
		else:
			raise RuntimeError("datatype {} not associated with tileWidget".format(
				self.dataType))
		return widg

class PassthroughTileEntry(TileEntry):
	"""same as above but for pass-through attributes
	extraAttr MUST be an output"""

	def __init__(self, extraAttr=None, *args, **kwargs):
		"""input attr still informs the main entry body"""
		if extraAttr.role != "output":
			raise RuntimeError("passthrough tileEntry called incorrectly,"
			                   "extraAttr must be output")
		super(PassthroughTileEntry, self).__init__(*args, **kwargs)
		if self.attr.role != "input":
			raise RuntimeError("passthrough tileEntry called incorrectly,"
			                   "first attr must be input")
		self.extraAttr = extraAttr
		self.role = "passthrough"

		self.extraText = QtWidgets.QGraphicsTextItem(self.extraAttr.name, self)
		self.extraText.adjustSize()

		self.extraKnob = Knob(self, attr=self.extraAttr)

		self.arrangeExtra()


	def arrangeExtra(self):
		"""someday go back and refactor this, but for now it's fine"""

		# place text outside node
		textBox = self.extraText.boundingRect()
		textWidth = textBox.width() + 30
		mainWidth = self.rect().width()

		x = mainWidth
		textX = mainWidth + 30
		knobY = self.height /2.0 - self.extraKnob.boundingRect().height() / 2.0
		self.extraKnob.setPos(x, knobY)
		self.extraText.setPos(textX, 1)


class Knob(QtWidgets.QGraphicsRectItem):
	"""handle marking inputs and outputs"""
	def __init__(self, parent=None, attr=None, extras={}):
		# parent is qGraphicsWidget, attr is AttrItem
		super(Knob, self).__init__(parent)
		self.parent = parent
		self.extras = dict(extras)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not attr:
			raise RuntimeError("no attrItem supplied")
		#self.attr = attr
		self.role = self.attr.role
		self.name = self.attr.name
		self.colour = self.attr.colour
		self.pipes = []
		self.pen = QtGui.QPen()
		self.pen.setStyle(QtCore.Qt.NoPen)
		self.brush = QtGui.QBrush(QtGui.QColor(*self.colour),
		                          bs=QtCore.Qt.SolidPattern)
		#self.brush.setColor()
		self.setPen(self.pen)
		self.setBrush(self.brush)
		self.setAcceptHoverEvents(True)

	@property
	def attr(self):
		return self.parent.attr

	def __repr__(self):
		return self.name

	# def onConnectionMade(self, dest):
	# 	"""in case"""
	#
	# def onConnectionBroken(self, dest):
	# 	pass
	#
	# def removePipe(self, pipe):
	# 	self.pipes = [i for i in self.pipes if i != pipe]
	#
	# def delete(self):
	# 	"""literally the reason i broke up with NodeGraphQt"""

	# visuals
	def hoverEnterEvent(self, event):
		"""tweak to allow knobs to expand pleasingly when you touch them"""
		self.setTumescent()

	def hoverLeaveEvent(self, event):
		"""return knobs to normal flaccid state"""
		self.setFlaccid()

	def setTumescent(self):
		new = int(self.baseSize * 1.5)
		# self.setRect(0, new/1.25, new, new)
		self.setRect(0, 0, new, new)

	def setFlaccid(self):
		self.setRect(0, 0, self.baseSize, self.baseSize)

class Pipe(QtWidgets.QGraphicsPathItem):
	"""tis a noble thing to be a bridge between knobs"""

	def __init__(self, start=None, end=None, edge=None):
		super(Pipe, self).__init__()
		self.setZValue(Z_VAL_PIPE)
		self.setAcceptHoverEvents(True)
		self._color = start.colour if start else PIPE_DEFAULT_COLOR
		self._style = PIPE_STYLE_DEFAULT
		self._active = False
		self._highlight = False
		self.selected = False
		self._start = start
		self._end = end
		self.pen = None
		self.setFlags(
			QtWidgets.QGraphicsItem.ItemIsSelectable
		)

		self.edge = edge


	def setSelected(self, selected):
		self.selected = selected
		if selected:
			self.highlight()
		if not selected:
			self.reset()
		super(Pipe, self).setSelected(selected)

	def paint(self, painter, option, widget):
		color = QtGui.QColor(*self._color)
		pen_style = PIPE_STYLES.get(self.style)
		pen_width = PIPE_WIDTH
		if self._active:
			color = QtGui.QColor(*PIPE_ACTIVE_COLOR)
		elif self._highlight:
			color = QtGui.QColor(*PIPE_HIGHLIGHT_COLOR)
			pen_style = PIPE_STYLES.get(PIPE_STYLE_DEFAULT)

		if self.start and self.end:
			# use later for proper freezing/approval
			pass
			# in_node = self.start.node
			# out_node = self.end.node
			# if in_node.disabled or out_node.disabled:
			# 	color.setAlpha(200)
			# 	pen_width += 0.2
			# 	pen_style = PIPE_STYLES.get(PIPE_STYLE_DOTTED)

		if self.selected:
			#painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
			#colour = QtGui.QColor(200, 200, 100)
			# self._highlight = True
			pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
			pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))

		else:
			pen = QtGui.QPen(color, pen_width)
			pen.setStyle(pen_style)

		pen.setCapStyle(QtCore.Qt.RoundCap)

		painter.setPen(self.pen or pen)
		painter.setRenderHint(painter.Antialiasing, True)
		painter.drawPath(self.path())

	def draw_path(self, start_port, end_port, cursor_pos=None):
		if not start_port:
			return
		offset = (start_port.boundingRect().width() / 2)
		pos1 = start_port.scenePos()
		pos1.setX(pos1.x() + offset)
		pos1.setY(pos1.y() + offset)
		if cursor_pos:
			pos2 = cursor_pos
		elif end_port:
			offset = start_port.boundingRect().width() / 2
			pos2 = end_port.scenePos()
			pos2.setX(pos2.x() + offset)
			pos2.setY(pos2.y() + offset)
		else:
			return

		line = QtCore.QLineF(pos1, pos2)
		path = QtGui.QPainterPath()
		path.moveTo(line.x1(), line.y1())

		# if self.viewer_pipe_layout() == PIPE_LAYOUT_STRAIGHT:
		# 	path.lineTo(pos2)
		# 	self.setPath(path)
		# 	return

		ctr_offset_x1, ctr_offset_x2 = pos1.x(), pos2.x()
		tangent = ctr_offset_x1 - ctr_offset_x2
		tangent = (tangent * -1) if tangent < 0 else tangent

		max_width = start_port.parent.boundingRect().width() / 2
		tangent = max_width if tangent > max_width else tangent

		if start_port.role == "input":
			ctr_offset_x1 -= tangent
			ctr_offset_x2 += tangent
		elif start_port.role == "output":
			ctr_offset_x1 += tangent
			ctr_offset_x2 -= tangent

		ctr_point1 = QtCore.QPointF(ctr_offset_x1, pos1.y())
		ctr_point2 = QtCore.QPointF(ctr_offset_x2, pos2.y())
		path.cubicTo(ctr_point1, ctr_point2, pos2)
		self.setPath(path)

	def redrawPath(self):
		"""updates path shape"""
		self.draw_path(self.start, self.end)

	def activate(self):
		self._active = True
		pen = QtGui.QPen(QtGui.QColor(*PIPE_ACTIVE_COLOR), 2)
		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
		self.setPen(pen)

	def active(self):
		return self._active

	def highlight(self):
		self._highlight = True
		pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
		self.setPen(pen)

	def highlighted(self):
		return self._highlight

	def reset(self):
		self._active = False
		self._highlight = False
		pen = QtGui.QPen(QtGui.QColor(*self.color), 2)
		pen.setStyle(PIPE_STYLES.get(self.style))
		self.setPen(pen)

	@property
	def start(self):
		return self._start

	@start.setter
	def start(self, port):
		if isinstance(port, Knob) or not port:
			self._start = port
		else:
			self._start = None

	@property
	def end(self):
		return self._end

	@end.setter
	def end(self, port):
		if isinstance(port, Knob) or not port:
			self._end = port
		else:
			self._end = None

	@property
	def color(self):
		return self._color

	@color.setter
	def color(self, color):
		self._color = color

	@property
	def style(self):
		return self._style

	@style.setter
	def style(self, style):
		self._style = style

#
	# def setEnd(self, end):
	# 	"""expects objects that have a .scenePos() method
	# 	like graphicsItems and mouse events"""
	# 	self.end = end
	# 	self.updatePath()
	#
	# def updatePath(self):
	# 	startPoint = self.start.scenePos()
	# 	if not self.end:
	# 		return
	# 	endPoint = self.end.scenePos()
	#
	# 	# draw pleasing curve shape varying with distance
	# 	diffPoint = startPoint.__sub__(endPoint)
	# 	length = math.sqrt(pow(diffPoint.x(), 2) + pow(diffPoint.y(), 2))
	#
	# 	# c1 = QtCore.QPointF(startPoint.x() + 2*length, startPoint.y())
	# 	# c2 = QtCore.QPointF(endPoint.x() - 2*length, endPoint.y())
	# 	# self.path.cubicTo(c1, c2, endPoint)
	# 	self.path.lineTo(endPoint)
	# 	self.painter.drawPath(self.path)
	#
	# 	self.setPath(self.path)
	# 	style = QtWidgets.QStyleOptionGraphicsItem(1)
	# 	self.paint(self.painter, style)
	#
	# def makePen(self, style):
	# 	"""eventually modify the appearance of the line based on
	# 	knob characteristics, style etc"""
	# 	return QtGui.QPen()
	#
	def delete(self):
		self.scene().removeItem(self)
		del self







