# base machinery for all visual nodes in TilePile
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tilepile.abstractnode import AbstractNode
from edRig.structures import SafeDict
from edRig.tilepile.ui2 import tilewidgets
from edRig.tilepile.ui2.style import *
#import math


PIPE_STYLES = {
    PIPE_STYLE_DEFAULT: QtCore.Qt.PenStyle.SolidLine,
    PIPE_STYLE_DASHED: QtCore.Qt.PenStyle.DashDotDotLine,
    PIPE_STYLE_DOTTED: QtCore.Qt.PenStyle.DotLine
}

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
		self.extras = SafeDict(kwargs)
		self._inputs, self._outputs = {}, {} # attrname : TileEntry
		self.entries = {} # attrname : TileEntry

		self._width = 30
		self._height = 30

		# widgets
		self.nameTag = tilewidgets.NameTagWidget(self, abstractNode.nodeName)
		self.classTag = QtWidgets.QGraphicsTextItem(
			self.abstract.__class__.__name__, self)

		# flags?
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable) # ????
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable) # ????
		#self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, False)

		print "abstract inputs are {}".format(self.abstract.inputs)

		# entries
		for i in self.abstract.inputs:
			entry = TileEntry(parent=self, attrItem=i, scene=self.scene)
			#print "entry is {}".format(entry)
			self.addEntry(entry, role="input")
			entry.arrange()
		for i in self.abstract.outputs:
			entry = TileEntry(parent=self, attrItem=i, scene=self.scene)
			self.addEntry(entry, role="output")
			entry.arrange()
			#self.entries[i.name] = entry

		self.selected = False
		self.colour = self.abstract.colour
		self.borderColour = (200,200,250)

		# resizing
		self.width, self.height = self.calc_size()
		self.entryHeight = 20
		for i in self.entries.values():
			i.setRect(0,0, self.width, self.entryHeight)



		# width, height = self.calc_size()
		# self.setRect(0,0, width, height)
		self.calc_size()

		# arrange items
		self.arrangeText()
		self.arrangeEntries()

		self.setTextColour((200, 200, 200))

		# signals
		self.nameTag.value_changed.connect(self._onNameChange)
		self.actions = {}
		self.abstract.sync.connect(self.sync)

	def sync(self):
		"""verify number of tileEntries is in sync with abstractNode"""
		self.abstract.log("")
		self.abstract.log("begin abstractTile sync")
		self.abstract.log("abstract attrs are {}, {}".format(
			self.abstract.inputs, self.abstract.outputs))
		for n in (self.abstract.inputs, self.inputs, "input"), \
			(self.abstract.outputs, self.outputs, "output"):

			# check if we need to add entries
			for i in n[0]:
				if i.name not in n[1].keys():
					entry = TileEntry(parent=self, attrItem=i)
					self.addEntry(entry, role=n[2])
				entry = self.entries[i.name]
				entry.attr = i

			# check if we need to remove entries
			for i in n[1].keys():
				if not any(i in k.name for k in n[0]):
					self.removeEntry(n[1][i], role=n[2])
		self.arrangeEntries()

	def getActions(self):
		return self.abstract.getAllActions()

	@property
	def inputs(self):
		#return sorted(self._inputs)
		return self._inputs

	@property
	def outputs(self):
		#return sorted(self._outputs)
		return self._outputs
	#
	# @property
	# def entries(self):
	# 	return self.inputs.update(self.outputs)

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

	# child elements
	def addEntry(self, entry, role="input"):
		"""add tile entry item to tile"""
		roles = {"input" : self.inputs,
				 "output" : self.outputs}
		if entry.name in roles[role].keys():
			# raise RuntimeError("entry name {} is already an {}".format(
			# 	entry.name, role))
			# need a more sensitive solution to account for child entries -
			# if parents add children recursively, this may not be cause for error
			print "entry name {} is already an {}".format(entry.name, role)
			return
		roles[role][entry.name] = entry
		self.entries[entry.name] = entry
		#self.scene.addItem(entry) #unparents item

	def removeEntry(self, entry, role="input"):
		"""remove tile entry item from tile"""
		roles = {"input": self.inputs,
				 "output": self.outputs}
		roles[role].pop(entry.name)
		self.entries.pop(entry.name)
		self.scene.removeItem(entry)


	# visuals
	def boundingRect(self):
		width, height = self.calc_size()
		return QtCore.QRectF(0.0, 0.0, width, height)

	def arrangeText(self):
		self.classTag.setPos(self.boundingRect().width(), 0)

	def arrangeEntries(self):
		y = 10 # height of name and class tag
		for i in self.entries.values():
			i.arrange()
			# print ""
			# print "entryPos is {}".format(i.pos())
			height = i.rect().height()+7
			y += height
			# i.setPos(self.scene.mapToScene(10, y))
			i.setPos(0, y)
			#print "newPos is {}".format(i.pos())



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

	def calc_size(self):
		"""
		calculate minimum node size.
		"""
		width = 0.0
		min = self.nameTag.boundingRect()
		minWidth = min.x() + 150
		minHeight = min.y() + 20
		for i in self.entries.values():
			minHeight += 33
			minWidth = max(minWidth, i.boundingRect().width())


		height = 0
		width = 10

		height += 10
		#self.prepareGeometryChange()
		self.width = minWidth
		self.height = minHeight
		self.update()
		return minWidth, minHeight

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
		#w, h = self.calc_size()
		#self._width = width if width > w else w
		#width = width if width > w else w
		#self._width = width
		self._width = width

	@property
	def height(self):
		return self._height

	@height.setter
	def height(self, height=0.0):
		# w, h = self.calc_size()
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

	# def focusInEvent(self, event): # fucking help me
	# 	event.ignore()

class TileEntry(QtWidgets.QGraphicsRectItem):
	"""individual shelf for knob and associated widget
	this sadly locks us into left-to-right rectangular widgets...for now..."""
	def __init__(self, parent=None, attrItem=None, rect=None, scene=None):
		if not attrItem:
			raise RuntimeError("no attrItem supplied!")
		super(TileEntry, self).__init__(parent)
		self.parent = parent
		self.scene = scene
		self.attr = attrItem
		self.name = attrItem.name
		self.dataType = attrItem.dataType
		self.children = []
		self.extras = self.attr.extras
		self.role = attrItem.role
		self.widg = None
		self.label = None
		self.knob = None
		self.setRect(0,0,self.parent.width-5,20)
		if attrItem.isConnectable():
			self.knob = Knob(self, attr=self.attr)
		else:
			self.knob = None
		if attrItem.isSimple() and self.role == "input":
			self.widg = self.makeWidg()
			self.widg.setToolTip(self.attr.desc)
			self.widg.value_changed.connect(self.setAttrValue)
		else:
			if self.role == "output":
				#self.widg = tilewidgets.NodeLabel(self.attr.desc, self)
				self.label = QtWidgets.QGraphicsTextItem("output", self)
				self.label.adjustSize()
			elif not attrItem.isSimple():
				self.label = QtWidgets.QGraphicsTextItem("dimensional", self)
				self.label.adjustSize()
		self.setToolTip(self.attr.desc)

		self.text = QtWidgets.QGraphicsTextItem(self.attr.name, self)
		self.text.adjustSize()

		self.pen = QtGui.QPen()
		self.brush = QtGui.QBrush()
		self.setPen(self.pen)
		self.setBrush(self.brush)

		self.width = self.rect().width()
		self.height = self.rect().height()

		self.arrange()


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
		print "setting attr {} value to {}".format(self.name, val)
		self.attr.value = val

	def sync(self):
		"""disable widget if connected, update widget value etc"""

	def arrange(self):
		"""place widget and port properly according to role
		AND PLACE CHILDREN eventually"""
		midHeight = self.height / 2.0
		midWidth = self.width / 2.0
		mainWidth = self.rect().width()
		if self.widg:
			widgetRect = self.widg.rect()
			widgY = midHeight - widgetRect.height() / 2.0
			#widgX = mainWidth / 2.0# + widgetRect.width() / 2.0
			widgX = 0
			#self.widg.setPos(self.scene.mapToScene(widgX, widgY))
			self.widg.setPos(widgX, widgY)

		if self.label:
			labelRect = self.label.boundingRect()
			self.label.setPos(0, 0)

		# place text outside node
		textBox = self.text.boundingRect()
		textWidth = textBox.width() + 30

		if self.role == "output":
			x = mainWidth
			textX = mainWidth + 30
		else:
			# position knob on left
			x = -20
			textX = textWidth * -1
		if self.knob:
			knobY = self.height /2.0 - self.knob.boundingRect().height() / 2.0
			self.knob.setPos(x, knobY)
		self.text.setPos(textX, 1)


	def makeWidg(self):
		name = self.attr.name
		value = self.attr.value
		print ""
		print "widg attr is {}, value is {}".format(self.attr, self.attr.value)
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
		self.extras = SafeDict(extras)
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

	# matchIndex = re.match(
	# 	r'([a-zA-Z0-9]+)\.weightList\[([0-9]+)\]\.weights', weightAttr
	# )
	# ?????

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
			print ""
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







