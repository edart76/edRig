# base machinery for all visual nodes in TilePile
from  __future__ import annotations
from tree import Tree, TreeWidget
from tree.ui.widget import AllEventEater

from typing import List, Dict

from weakref import WeakValueDictionary, WeakSet

from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tesserae.abstractnode import AbstractNode, AbstractAttr
#from edRig.tesserae.ui2 import tilewidgets, tilesettings
from edRig.tesserae.ui2 import tilewidgets

from edRig.tesserae.ui2.style import *


PIPE_STYLES = {
    PIPE_STYLE_DEFAULT: QtCore.Qt.PenStyle.SolidLine,
    PIPE_STYLE_DASHED: QtCore.Qt.PenStyle.DashDotDotLine,
    PIPE_STYLE_DOTTED: QtCore.Qt.PenStyle.DotLine
}

entryHeight = 20
nameBarHeight = 30
settingsPadding = 5

"""
events are gathered from QGraphicsScene and view, 
passed through those objects,
THEN passed to the proxy widgets.

"""

class SettingsProxy(QtWidgets.QGraphicsProxyWidget):
	"""test for event filtering
	STILL doesn't receive events before view and scene"""
	# def sceneEvent(self, event:QtCore.QEvent):
	# 	if isinstance(event, QtWidgets.QGraphicsSceneHoverEvent):
	# 		return super(SettingsProxy, self).sceneEvent(event)
	# 	print("proxy sceneEvent", event)
	#
	# 	return True
	# def mousePressEvent(self,
	#                     event:QtWidgets.QGraphicsSceneMouseEvent):
	# 	print("proxy mousePress")
	# 	return True



class AbstractTile2(QtWidgets.QGraphicsItem):
	""" now DIRECT link between node and tile,
	 sync used to start over entirely

	 """
	def __init__(self, parent=None, abstractNode:AbstractNode=None,
	             widgetParent:QtWidgets.QWidget=None):
		super(AbstractTile2, self).__init__(parent)
		if not isinstance(abstractNode, AbstractNode):
			raise RuntimeError("no abstractNode provided!")
		self.abstract = abstractNode

		self.widgetParent = widgetParent # for settings parenting


		self.attrBlocks = [None, None] #type:List[TileEntry]

		self.nameTag = tilewidgets.NameTagWidget(self, abstractNode.name)
		self.classTag = QtWidgets.QGraphicsTextItem(
			self.abstract.__class__.__name__, self)

		self.abstract.nameChanged.connect(self.onAbstractNameChange)

		self.settingsWidg = self.addSettings(self.abstract.settings,)
		self.settingsWidg.expandAll()

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

		# signals
		self.nameTag.value_changed.connect(self._onNameTagChange)
		self.actions = {}
		self.abstract.sync.connect(self.sync)

		# set reference to this tile on abstractNode???????
		self.abstract.ui = self

		# appearance
		self.width, self.height = self.getSize()
		self.entryHeight = 20
		self.colour = self.abstract.extras.get("colour", (50, 50, 120))
		self.borderColour = (200,200,250)
		textColour = QtGui.QColor(200, 200, 200)
		self.classTag.setDefaultTextColor(textColour)
		self.classTag.setPos(self.boundingRect().width(), 0)

		self.sync()

	@property
	def entries(self)->Dict[str, TileEntry]:
		"""full flat composite string address map of all items"""
		# entries = WeakValueDictionary()
		entries = {}
		for i in self.attrBlocks:
			entries.update(i.getEntryMap())
		return entries

	@property
	def knobs(self)->Dict[str, Knob]:
		"""return flat map of address : Knob object"""
		# knobs = WeakValueDictionary()
		knobs = {}
		for k, v in self.entries.items():
			knobs[k] = v.knob
		return knobs


	def sync(self):
		"""update attrBlocks
		they now update autonomously from tree signals"""

		# check that root objects aren't different
		# print("attrBlocks", self.attrBlocks)
		if not (self.attrBlocks[0] is self.abstract.inputRoot and
			self.attrBlocks[1] is self.abstract.outputRoot):
			self.attrBlocks[0] = TileEntry(parent=self,
			                               tree=self.abstract.inputRoot)
			self.attrBlocks[1] = TileEntry(parent=self,
			                               tree=self.abstract.outputRoot)

		# resizing
		self.width, self.height = self.getSize()
		self.arrange()

	def arrange(self):
		for i in self.attrBlocks:
			i.arrange()
		y = nameBarHeight # height of name and class tag

		self.attrBlocks[0].setPos(0, y)
		y += self.attrBlocks[0].boundingRect().height() + 7

		self.attrBlocks[1].setPos(0, y)
		y += self.attrBlocks[1].boundingRect().height() + 7

		#y += 30
		self.settingsWidg.resizeToTree()
		self.settingsProxy.setGeometry( QtCore.QRect(
			settingsPadding, y,
		    max(self.settingsWidg.width(), self.width) - settingsPadding * 2 ,
		    self.settingsWidg.height() ) )


		self.getSize()

	def dragMoveEvent(self, event:QtWidgets.QGraphicsSceneDragDropEvent):
		"""test"""
		print("tile dragMoveEvent")
		return super(AbstractTile2, self).dragMoveEvent(event)


	def _onNameTagChange(self, widget, name):
		self.abstract.rename(name)

	def onAbstractNameChange(self, branch, name):
		self.nameTag.value = name


	def getSize(self):
		"""
		calculate minimum node size.
		"""
		minRect = self.nameTag.boundingRect()
		minWidth = minRect.x() + 150
		#minWidth = minRect.x()
		minHeight = minRect.y() + 20

		for i in self.attrBlocks:
			if not i:
				continue
			minHeight += i.boundingRect().height() + 10

		minHeight += self.settingsProxy.rect().height()
		minHeight += settingsPadding * 2

		self.width = minWidth
		self.height = minHeight
		return minWidth, minHeight

	def boundingRect(self):
		minWidth, minHeight = self.getSize()
		return QtCore.QRect(0, 0, minWidth, minHeight)

	def paint(self, painter, option, widget):
		"""Paint the main background shape of the node"""
		painter.save()
		self.getSize()

		baseBorder = 1.0
		rect = QtCore.QRectF(0.5 - (baseBorder / 2),
							 0.5 - (baseBorder / 2),
							 self.width + baseBorder,
							 self.height + baseBorder)
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

		if self.isSelected():
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
		if self.isSelected():
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
		painter.restore()

	def addSettings(self, tree):
		"""create a new abstractTree widget and add it to the bottom of node"""
		# self.settingsProxy = QtWidgets.QGraphicsProxyWidget(self)
		self.settingsProxy = SettingsProxy(self)

		topWidg = QtWidgets.QApplication.topLevelWidgets()[0]
		print("addSettings topWidg", topWidg)

		parent = self.widgetParent

		self.settingsWidg = TreeWidget(
			#parent=self.scene().views()[0],
			#parent=topWidg,
			parent=parent,
			# parent=None,
		                               tree=tree)
		self.settingsProxy.setWidget(self.settingsWidg)
		# self.scene().addItem(self.settingsProxy)

		# connect collapse and expand signals to update size properly
		# self.settingsWidg.collapsed.connect( self._resizeSettings )
		# self.settingsWidg.expanded.connect( self._resizeSettings )

		return self.settingsWidg

	def getActions(self):
		return self.abstract.getAllActions()

	def serialise(self):
		"""save position in view"""
		return {
			"pos" :	(self.pos().x(), self.pos().y()),
			}

AbstractTile = AbstractTile2

class TileEntry(QtWidgets.QGraphicsRectItem):
	"""testing live autonomous tracking of tree object
	feels very weird not to have a master sync function
	 """

	treeKeys = ("name", "dataType", "extras", "role")

	def __init__(self, parent=None, tree:AbstractAttr=None,
	             text=True, depth=0, recurse=True):
		if not tree:
			raise RuntimeError("no attrItem supplied!")
		super(TileEntry, self).__init__(parent)

		# lambdas to lookup on tree, to make live
		self.tree = tree
		for key in self.treeKeys:
			setattr(self, key, None)
		self.syncKeys()
		for i in tree.signals:
			i.connect(self.syncKeys)
		tree.structureChanged.connect(self.onStructureChanged)

		# widget support if it ever comes back
		self.widg = None
		self.label = None
		self.knob = None

		# overridden later by arrange()
		if tree.isConnectable():
			self.knob = Knob(self, tree=self.tree)

		# appearance
		# base visual dimensions
		self.edgePad = 5
		self.unitHeight = entryHeight

		self.setRect(0,0,
		             self.parentItem().boundingRect().width() - self.edgePad,
		             self.unitHeight)

		self.setToolTip(self.tree.desc)
		self.text = QtWidgets.QGraphicsTextItem(self.tree.name, self)
		self.text.adjustSize()
		if not text:
			self.text.setVisible( False )

		self.pen = QtGui.QPen()
		self.brush = QtGui.QBrush()
		self.setPen(self.pen)
		self.setBrush(self.brush)

		self.children = {}

		if recurse:
			self.children = {i : TileEntry(
				parent=self, tree=i,
			)
					for i in tree.branches }

	def boundingRect(self):
		base = super(TileEntry, self).boundingRect()
		height = base.height() + sum(
			i.boundingRect().height() for i in self.children.values())
		return QtCore.QRect(base.left(), base.top(),
		                    base.width(), height)

	@property
	def width(self):
		return self.boundingRect().width()
	@property
	def height(self):
		return self.boundingRect().height()
	@property
	def depth(self):
		return self.tree.depth

	def syncKeys(self, *args, **kwargs):
		"""update attributes from tree"""
		for key in self.treeKeys:
			setattr(self, key, getattr(self.tree, key, None))

	def onStructureChanged(self, branch, parent, code:Tree.StructureEvents ):
		"""test for autonomous distributed tracking
		of tree structure instead of in
		master sync method """
		# print("entry onStructureChanged")
		# print("branch", branch, "parent", parent, code)
		if not parent is self.tree:
			return
		if code == Tree.StructureEvents.branchAdded:
			self.addChild(branch)
		elif code == Tree.StructureEvents.branchRemoved:
			self.removeChild(branch)
		self.arrange()


	def addChild(self, branch:Tree):
		"""bit weird to accept a tree object
		but I don't care anymore"""
		entry = TileEntry(
			parent=self, tree=branch,
			depth=self.depth + 1
		)
		self.children[branch] = entry
		return entry

	def removeChild(self, branch:Tree):
		entry = self.children[branch]
		self.scene().removeItem(entry)
		self.children.pop(branch)


	def onConnectionMade(self):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.disable()

	def onConnectionBroken(self, dest):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.enable()


	def getEntryMap(self):
		""" returns FLAT map of {address : entry} for all child entries """
		# entryMap = {self.attr.stringAddress() : self}
		entryMap = {}
		entryMap[self.tree.stringAddress()] = self
		for i in self.children.values():
			entryMap.update(i.getEntryMap())
		return entryMap


	def arrange(self, parentWidth=None, depth=0, n=0, d=0):
		"""recursively lay out tree structure
		 """
		depth = self.tree.depth
		f = 1 if self.role == "output" else -1
		y = (self.tree.index() + 1) * self.unitHeight
		x = (depth - 1) * 10 * f

		self.setPos(x, y)

		childEntries = list(self.children.values())

		for i in childEntries:
			i.arrange()

		height = sum([i.rect().height() for i in childEntries])
		# remove input and output
		if self.tree.name in ("inputRoot", "outputRoot"):
			#self.text.setVisible(False)
			pass
		else:
			height = height + self.unitHeight

		mainWidth = self.rect().width()
		parentWidth = parentWidth or self.parentItem().width

		if self.label:
			labelRect = self.label.boundingRect()
			self.label.setPos(0, 0)

		# place text outside node
		textBox = self.text.boundingRect()
		textWidth = textBox.width() + 30
		#
		if self.role == "output":
			x = mainWidth
			textX = mainWidth - textWidth
			# if self.knob:
			# 	textX = mainWidth + 30
			# else: textX = mainWidth + 5
		else:
			# position knob on left
			x = x - 20
			textX = x
			if self.knob:
				textX += self.knob.boundingRect().width()
			#textX = textWidth * -1
			#textX = 20
		if self.knob:
			knobY = self.height /2.0 - self.knob.boundingRect().height() / 2.0
			self.knob.setPos(x, 0)
		self.text.setPos(textX, 1)



	def makeWidg(self):
		name = self.tree.name
		value = self.tree.value
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
		if self.tree.role != "input":
			raise RuntimeError("passthrough tileEntry called incorrectly,"
			                   "first attr must be input")
		self.extraAttr = extraAttr
		self.role = "passthrough"

		self.extraText = QtWidgets.QGraphicsTextItem(self.extraAttr.name, self)
		self.extraText.adjustSize()

		self.extraKnob = Knob(self, tree=self.extraAttr)

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
	def __init__(self, parent=None, tree:AbstractAttr=None, extras={}):
		super(Knob, self).__init__(parent)
		self.extras = dict(extras)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not tree:
			raise RuntimeError("no attrItem supplied")
		#self.attr = attr
		self.role = self.tree.role
		self.name = self.tree.name + "Knob"
		self.colour = self.tree.colour
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
	def tree(self):
		return self.parentItem().tree

	def __repr__(self):
		return self.name

	# visuals
	def hoverEnterEvent(self, event):
		"""tweak to allow knobs to expand pleasingly when you touch them"""
		self.setTumescent()

	def hoverLeaveEvent(self, event):
		"""return knobs to normal flaccid state"""
		self.setFlaccid()

	def setTumescent(self):
		scale = 1.3
		new = int(self.baseSize * scale)
		newOrigin = (new - self.baseSize) / 2
		self.setRect(-newOrigin, -newOrigin, new, new)

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
		self._start = start
		self._end = end
		self.pen = None
		self.setFlags(
			QtWidgets.QGraphicsItem.ItemIsSelectable
		)

		self.edge = edge


	def setSelected(self, selected):
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

		if self.isSelected():
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

	def drawPath(self, startPort, endPort, cursorPos=None):
		if not startPort:
			return
		offset = (startPort.boundingRect().width() / 2)
		pos1 = startPort.scenePos()
		pos1.setX(pos1.x() + offset)
		pos1.setY(pos1.y() + offset)
		if cursorPos:
			pos2 = cursorPos
		elif endPort:
			offset = startPort.boundingRect().width() / 2
			pos2 = endPort.scenePos()
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

		ctrOffsetX1, ctrOffsetX2 = pos1.x(), pos2.x()
		tangent = ctrOffsetX1 - ctrOffsetX2
		tangent = (tangent * -1) if tangent < 0 else tangent

		maxWidth = startPort.parentItem().boundingRect().width() / 2
		tangent = maxWidth if tangent > maxWidth else tangent

		if startPort.role == "input":
			ctrOffsetX1 -= tangent
			ctrOffsetX2 += tangent
		elif startPort.role == "output":
			ctrOffsetX1 += tangent
			ctrOffsetX2 -= tangent

		ctrPoint1 = QtCore.QPointF(ctrOffsetX1, pos1.y())
		ctrPoint2 = QtCore.QPointF(ctrOffsetX2, pos2.y())
		path.cubicTo(ctrPoint1, ctrPoint2, pos2)
		self.setPath(path)

	def redrawPath(self):
		"""updates path shape"""
		self.drawPath(self.start, self.end)

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

	def delete(self):
		pass

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







