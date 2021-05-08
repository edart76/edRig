
""" Widget for renaming
This is the first proper cross-dcc python file """


import edRig
import importlib
importlib.reload(edRig)

from edRig import reload
importlib.reload(edRig)

from edRig import cmds, hou, hutil

# try:
# 	from hutil.qt import QtWidgets, QtCore, QtGui
# except:
# 	from PySide2 import QtWidgets, QtCore, QtGui

from PySide2 import QtWidgets, QtCore, QtGui

from edRig.tool.rename import lib
importlib.reload(lib)

class LabelContainer(QtWidgets.QWidget):
	""" for putting text label alongside widget
	 shouldn't be this difficult"""
	def __init__(self, text=None, childCls=None, parent=None):
		super(LabelContainer, self).__init__(parent=parent)
		self.label = QtWidgets.QLabel(text, self)
		self.child = childCls(parent=self)
		hl = QtWidgets.QHBoxLayout()
		hl.addWidget(self.label)
		hl.addWidget(self.child)
		self.setLayout(hl)


# class RenameWidget(QtWidgets.QDialog):
class RenameWidget(QtWidgets.QWidget):
	"""search and replace fields """
	optionsHL = None
	def __init__(self, parent=None):
		super(RenameWidget, self).__init__(parent=parent)
		self.searchLabel = QtWidgets.QLabel("Search", parent=self)
		self.searchLine = QtWidgets.QLineEdit(parent=self)
		self.searchLine.setToolTip(
			"Enter tokens to search for, separated by comma")

		self.replaceLabel = QtWidgets.QLabel("Replace", parent=self)
		self.replaceLine = QtWidgets.QLineEdit(parent=self)
		self.replaceLine.setToolTip(
			"Enter corresponding tokens to replace"
		)
		self.caseCheck = LabelContainer(
			"Preserve case", childCls=QtWidgets.QCheckBox, parent=self)
		self.caseCheck.child.setChecked(True)
		self.digitCheck = LabelContainer(
			"Strip trailing digits", childCls=QtWidgets.QCheckBox, parent=self)
		self.digitCheck.child.setChecked(True)

		self.renameBtn = QtWidgets.QPushButton("Rename", self)
		self.renameBtn.clicked.connect(self.onRenameBtnPress)
		self.dryRunBtn = QtWidgets.QPushButton("Dry run", self)
		self.dryRunBtn.clicked.connect(self.onDryRunBtnPress)

		# layouts
		renameHL = QtWidgets.QHBoxLayout()
		for i in [self.renameBtn, self.dryRunBtn]:
			renameHL.addWidget(i)

		self.optionsHL = QtWidgets.QVBoxLayout()
		for i in [self.caseCheck, self.digitCheck]:
			self.optionsHL.addWidget(i)

		mainVL = QtWidgets.QVBoxLayout()
		for i in [self.searchLabel, self.searchLine,
		          self.replaceLabel, self.replaceLine]:
			mainVL.addWidget(i)
		mainVL.addLayout(self.optionsHL)
		mainVL.addLayout(renameHL)
		self.setLayout(mainVL)

	def onRenameBtnPress(self, *args, **kwargs):
		pass

	def onDryRunBtnPress(self, *args, **kwargs):
		pass



class HRename(RenameWidget):
	"""Houdini front end"""
	def __init__(self, parent=None):
		super(HRename, self).__init__(parent=parent)
		# check if node children should also be renamed
		self.childCheck = LabelContainer(
			"Rename children", QtWidgets.QCheckBox, parent=self)
		self.optionsHL.addWidget(self.childCheck)

	def onRenameBtnPress(self, *args, **kwargs):
		searchTokens = self.searchLine.text().split(",")
		searchTokens = [i.strip() for i in searchTokens]
		replaceTokens = self.replaceLine.text().split(",")
		replaceTokens = [i.strip() for i in replaceTokens]

		strings = [i.name() for i in hou.selectedNodes()]
		renamedStrings = lib.searchReplaceMain(
			strings, searchTokens, replaceTokens
		)
		for node, newName in zip(hou.selectedNodes(), renamedStrings):
			node.setName(newName)




def showHoudini():
	mainWidget = hou.qt.mainWindow()
	#w = HRename(parent=mainWidget)
	w = HRename()
	w.setParent(mainWidget, QtCore.Qt.Window)
	s = w.show()
	return s
