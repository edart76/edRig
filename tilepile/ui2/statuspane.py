# info about current tilepile environment
from PySide2 import QtWidgets, QtCore
from edRig import pipeline
from edRig.pipeline import FilePathTree
from edRig.tilepile.ui2.tabsearch import AbstractSearchWidget
from edRig.tilepile.ui2.lib import ConfirmDialogue
import os, tempfile

class StatusPane(QtWidgets.QFrame):
	"""current status of tilepile, including pipeline interaction
	may be extended to include data tree"""

	assetChanged = QtCore.Signal(list)

	def __init__(self, parent=None, corePaths=None):
		super(StatusPane, self).__init__(parent)
		self.setFocusPolicy(QtCore.Qt.NoFocus)

		self.corePaths = corePaths or [] # maybe assets all over damn place
		self.currentAsset = ""
		self.currentAssetPath = ""
		self.currentAssetItem = None

		self.vBox = QtWidgets.QVBoxLayout(self)

		self.coreDisplay = QtWidgets.QLineEdit("".join(self.corePaths), None)
		self.coreDisplay.setReadOnly(True)
		self.vBox.addWidget(self.coreDisplay)

		self.currentDisplay = AbstractSearchWidget(parent=None,
		                        items=pipeline.getExistingAssets().keys())
		self.vBox.addWidget(self.currentDisplay)

		self.setLayout(self.vBox)
		self.setAutoFillBackground(True)
		self.setGeometry(0,0,200,100)

		# signals
		self.currentDisplay.search_submitted.connect(self.onAssetChanged)

		self.onStartup()

	# signal responses
	def onAssetChanged(self, newName, force=False):
		"""called whenever user tries to change asset context"""
		change = False # is change successful?
		print ""
		print "current asset is {}".format(self.currentAsset)
		if not newName in pipeline.getExistingAssets().keys():
			print "no asset {} found".format(newName)
			return False
		newPath = pipeline.getExistingAssets()[newName].path
		print "new path is {}".format(newPath)
		if newPath == self.currentAsset:
			return
		if not pipeline.isAsset(newPath):
			print "requested {} is not an asset (has no asset.txt)".format(newPath)
			return False
		if not force:
			if self.currentAssetItem: # don't confirm if there's no danger
				if not ConfirmDialogue.confirm(self, title="Confirm asset change"):
					return False
		self.currentAsset = newName
		self.currentAssetPath = newPath

		if not pipeline.checkAssetStructure(newPath, core=True):
			if ConfirmDialogue.confirm(self, title="Create asset structure",
			                           message="Create core asset files and folders?"):
				pipeline.makeAsset(assetPath=newPath)

		# confirmation dialog to switch
		# check asset has .tp and archive folders
		# confirmation dialogue to create asset structure if not
		change = True

		if not change:
			self.currentDisplay.setText(self.currentAsset)
		elif change:
			self.currentAsset = newName
			self.currentAssetItem = pipeline.AssetItem(newPath)
			self.assetChanged.emit([self.currentAssetItem])
		self.refreshDisplay()
		return self.currentAsset

	def updateCurrentAsset(self, assetItem):
		"""for asset changes sent from different part of ui"""
		self.currentAsset = assetItem.name
		self.currentAssetItem = assetItem
		self.currentDisplay.setText(assetItem.name)
	#
	# def keyPressEvent(self, event):
	# 	print "status keyPress is {}".format(event.text())
	#
	# def focusInEvent(self, event):
	# 	print "status focusIn is {}".format(event.reason())
	#
	# def focusOutEvent(self, event):
	# 	print "status focusOut is {}".format(event.reason())

	def onStartup(self):
		"""later restore previous asset to ui by default"""

	def refreshDisplay(self):
		"""updates displayed asset info: version etc"""
		pass

	def addCorePath(self, path):
		self.corePaths.append(path)







