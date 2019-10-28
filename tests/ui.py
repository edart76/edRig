

from edRig.tesserae.ui2 import tilesettings
from edRig.lib.python import AbstractTree
from edRig.tests import test


testTree = AbstractTree(name="testRoot", val=100)
testTree["firstChild"].value = "eyy"
testTree["secondChild", "secondSecondChild"].value = "wat"

@test
def testSettings():
	testWidget = tilesettings.TileSettings(None, tree=testTree)
	testWidget.show()

