# build the tilepile window
import PySide2 as ps
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.tilepile.ui.widgets import graphview, tilesettings, dataview, extras
#from edRig.tilepile.ui.widgets import logger
# from edRig.tilepile.jchan import NodeGraph, Node



def show():
    eyy = TilePileUI()
    eyyyyy = eyy.show()
    return eyyyyy


class TilePileUI(QtWidgets.QMainWindow):
    """main TilePile window"""
    def __init__(self):
        super(TilePileUI, self).__init__()
        self.text = "hello :)"
        self.width = 0
        self.height = 0

        self.initUi()

        self.widgets = []
        # anti rubbish collection

        self.setWindowModality(QtCore.Qt.WindowModal)

        print "tp init finished"

    def initUi(self):
        """Ui should be this:
        main is square window, taken up mostly by tile graph
        forms mondrian composition with bands to left and bottom
        for tile user input, and whatever else we need
        left bar should be built dynamically based on which
        tile is selected - treat it as its own layout
        top bar should be overlay triggered by mouse proximity:
        new, open, import, save
        for entire gui, replace checkboxes with edifice square boxes
        """


        parent = self.getMayaWindow()
        parentWindow = QtWidgets.QMainWindow(parent)
        self.text = "hello"

        # set continuous nodegraph as backdrop to whole window
        self.graph = graphview.GraphViewWidget(self)
        self.graphViewer = self.graph.viewer()
        self.tileSettings = tilesettings.TileSettingsWidget(self)
        self.extrasWidg = extras.ExtrasWidget(self, self.graph)
        #self.logger = logger.LoggingWidget(self)


        #self.mainFrame = QtWidgets.QFrame(self.graph.viewer())
        self.mainFrame = QtWidgets.QFrame(self)
        self.mainFrame.setStyleSheet(
            "background-color: rgba(0,0,50,255);"
        )

        #self.graph = graphview.GraphViewWidget(self.mainFrame)


        #self.setCentralWidget(self.graph.viewer())
        self.setCentralWidget(self.mainFrame)
        self.setGeometry(200, 200, 700, 700)
        self.setWindowTitle("testTile")
        self.width, self.height = self.mainDimensions()

        # INVESTIGATE RENDER OPTIONS AND MASK
        testDict = {
            "root" : {
                "how" : "shall",
                "I" : {
                    "sing" : "that",
                    "majesty" : "which",
                    "angles" : 2
                },
                "admire" : "let",
                "dust" : ["dust", "in", "dust"]
            }
        }
        #self.dataView = dataview.ViewTree(testDict)
        #self.dataView = dataview.DictionaryTreeDialog(testDict)



        ############## FOR NOW

        # set out main geometry and layouts
        hLayout = QtWidgets.QHBoxLayout()
        settingsFrame = QtWidgets.QFrame()
        graphFrame = QtWidgets.QFrame()
        hLayout.addWidget(settingsFrame, stretch=1)
        hLayout.addWidget(graphFrame, stretch=3)
        self.setLayout(hLayout)
        self.mainFrame.setLayout(hLayout)
        #self.graph.viewer().setLayout(hLayout)

        # settings panels
        settingsLayout = QtWidgets.QVBoxLayout()
        #settingsProxy = QtWidgets.QGroupBox("Tile Settings")
        loggerProxy = QtWidgets.QLabel("log goes here")
        settingsLayout.addWidget(self.tileSettings, stretch=1)
        settingsLayout.addWidget(loggerProxy, stretch=1)
        #settingsLayout.addWidget(self.dataView)
        #settingsLayout.addWidget(self.logger, stretch=1)
        settingsFrame.setLayout(settingsLayout)



        # graph panels
        graphLayout = QtWidgets.QVBoxLayout()
        #extraProxy = QtWidgets.QLabel("extra stuff goes here")
        graphLayout.addWidget(self.graph.viewer(), stretch=3)
        #graphLayout.addWidget(extraProxy, stretch=1)
        graphLayout.addWidget(self.extrasWidg, stretch=1)
        graphFrame.setLayout(graphLayout)

        ##### SIGNALS ######
        self.graph.node_selected.connect(
            self.tileSettings.refreshTileSettingsUi)
        self.extrasWidg.buildRig.connect(self.graph.buildRigToStep)


        """
        #graphScene = QtWidgets.QGraphicsScene(self)
        #graphView = nodz.Nodz(self)
        graphView = graphview.GraphViewWidget()
        #graphView.setScene(graphScene)
        #graphView.setSceneRect(100, 100, int(self.width*0.8), int(self.height*0.8))

        self.setCentralWidget(graphView)

        # Node A
        nodeA = graphView.createNode(name='nodeA', preset='node_preset_1', position=None)

        graphView.createAttribute(node=nodeA, name='Aattr1', index=-1, preset='attr_preset_1',
                             plug=True, socket=False, dataType=str)
        #self.setLayout(graphView)

        """

    def mousePressEvent(self, event):
        #self.graph.viewer().mousePressEvent(event)
        pass

    def mainDimensions(self):
        print "QtWidgets frame geo is {}".format(self.frameGeometry())
        sizeRect = self.frameGeometry()
        width = sizeRect.width()
        height = sizeRect.height()
        return width, height

    def checkValidTileOps(self):
        # loop through all the places where layer ops might be

        pass

    # def keyPressEvent(self, event):
	 #    """test"""
	 #    print "window level key is {}".format(event.text())


    def getMayaWindow(self):
        pointer = omui.MQtUtil.mainWindow()
        return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)
