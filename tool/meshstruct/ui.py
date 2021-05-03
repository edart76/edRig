
from importlib import reload
import json, os, sys
from PySide2 import QtWidgets, QtCore, QtGui
from edRig import cmds, om, mel
from edRig import meshstruct
reload(meshstruct)


def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)

class MeshStructUI(QtWidgets.QWidget):
	def __init__(self, parent=None):
		super(MeshStructUI, self).__init__(parent)
		self.chooseFolderBtn = QtWidgets.QPushButton("Folder", self)
		self.folderLbl = QtWidgets.QLabel(self)
		self._folder = ""
		self.chooseFolderBtn.clicked.connect(self.onFolderBtnPress)

		self.exportBtn = QtWidgets.QPushButton("Export selected", self)
		self.exportBtn.clicked.connect(self.onExportBtnPress)
		self.importBtn = QtWidgets.QPushButton(
			"Import mesh or attribute", self)
		self.importBtn.clicked.connect(self.onImportBtnPress)


		hl = QtWidgets.QHBoxLayout()
		vl = QtWidgets.QVBoxLayout()
		hl.addWidget(self.chooseFolderBtn)
		hl.addWidget(self.folderLbl)
		vl.addLayout(hl)
		vl.addWidget(self.exportBtn)
		vl.addWidget(self.importBtn)
		self.setLayout(vl)

	@property
	def folder(self):
		return self._folder
	@folder.setter
	def folder(self, val):
		self._folder = val
		self.folderLbl.setText(val)

	def onFolderBtnPress(self):
		name = cmds.file(q=1, sceneName=1) #type: str
		folderPath = "/".join(name.split("/")[:-1])
		print("folderPath", folderPath)
		path = QtWidgets.QFileDialog.getExistingDirectory(
			parent=self, dir=folderPath
		)
		if path:
			self.folder = path

	def onExportBtnPress(self):
		selMesh = cmds.ls(sl=1)
		if not selMesh:
			return
		if not selMesh[0].endswith("Shape"):
			shape = selMesh[0] + "Shape"
		else: shape = selMesh[0]
		struct = meshstruct.MeshStruct.fromShape(shape)
		data = struct.serialiseToComponents()
		struct.saveComponentsToFiles(self.folder, data)

	def onImportBtnPress(self):
		"""let user select mesh components to apply """
		sel = cmds.ls(sl=1)
		mfn = None
		if not sel:
			return
		name = cmds.file(q=1, sceneName=1)  # type: str
		folderPath = "/".join(name.split("/")[:-1])
		comps = QtWidgets.QFileDialog.getOpenFileNames(
			parent=self, dir=folderPath)[0]
		if not comps:
			return
		shape = sel[0]
		if not sel[0].endswith("Shape"):
			shape = sel[0] + "Shape"
		struct = meshstruct.MeshStruct.fromShape(shape)

		# set components
		print("components", comps)
		for comp in comps:
			data = json.load(open(comp, "r"))
			name = comp.split("/")[-1].split(".")[0]
			attrType = name.split("_")[0]
			attrName = "_".join(name.split("_")[1:])

			attrs = getattr(struct, attrType + "Attrs", None)
			if not attrs:
				print(name + "Attrs", "not found")
				continue
			attrs[attrName] = data

		# reapply mesh struct to mfn
		struct.toMFnMesh( struct.mfn )







def main():
	w = MeshStructUI()
	w.show()
	return w

		