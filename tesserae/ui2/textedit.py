# widget incorporating better editing of python code callbacks
# translated from qt docs

from PySide2 import QtCore, QtWidgets, QtGui

class TextEditWidget(QtWidgets.QWidget):
	"""holds line numbers and text edit"""
	def __init__(self, parent=None):
		super(TextEditWidget, self).__init__(parent)



class LineNumberArea(QtWidgets.QWidget):
	""""""
	def __init__(self, editor):
		super(LineNumberArea, self).__init__(editor)
		self.editor = editor

	def sizeHint(self):
		return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

	def paintEvent(self, event):
		self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
	""""""
	def __init__(self, parent=None):
		super(CodeEditor, self).__init__(parent)
		self.lineNumberArea = LineNumberArea(self)

		self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
		self.updateRequest.connect(self.updateLineNumberAreaWidth)
		self.cursorPositionChanged.connect(self.highlightCurrentLine)

		# immediate updates
		self.textChanged.connect(self.updateLineNumberAreaWidth)

		self.updateLineNumberAreaWidth(0)
		self.highlightCurrentLine()

	def lineNumberAreaWith(self):
		digits = 1
		limit = self.blockCount() or 1
		while limit >= 10:
			limit /= 10
			digits += 1

		#space = 3 + self.fontMetrics().horizontalAdvance(QtCore.QLatin1Char("9")) * digits
		# horizontalAdvance doesn't exist
		space = 3 + 12 * digits
		return space

	def updateLineNumberAreaWidth(self, *args, **kwargs):
		# (int /* newBlockCount */) # what does this mean?
		self.setViewportMargins(self.lineNumberAreaWith(), 0, 0, 0)

	# def proxyUpdateLineNumberAreaWidth(self, *args, **kwargs):
	# 	#?????
	# 	self.setViewportMargins(self.lineNumberAreaWith(), 0, 0, 0)

	def updateLineNumberArea(self, rect=None, dy=None):
		if dy:
			self.lineNumberArea.scroll(0, dy)
		else:
			self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(),
			                           rect.height())

		if rect.contains(self.viewport().rect()):
			self.updateLineNumberAreaWidth(0)

	def resizeEvent(self, event):
		super(CodeEditor, self).resizeEvent(event)
		cr = self.contentsRect()
		self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
		                                             self.lineNumberAreaWith(),
		                                             cr.height()))

	def lineNumberAreaPaintEvent(self, event):
		painter = QtGui.QPainter(self.lineNumberArea)
		painter.fillRect(event.rect(), QtCore.Qt.darkGray) # lol they can't spell

		block = self.firstVisibleBlock()
		blockNumber = block.blockNumber()
		top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
		bottom = top + int(self.blockBoundingRect(block).height())

		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(blockNumber+1)
				painter.setPen(QtCore.Qt.white)
				painter.drawText(0, top, self.lineNumberArea.width(),
				                 self.fontMetrics().height(),
				                 QtCore.Qt.AlignRight, number)
			block = block.next()
			top = bottom # cats and dogs
			bottom = top + int(self.blockBoundingRect(block).height())
			blockNumber += 1

	def highlightCurrentLine(self): # later
		pass
