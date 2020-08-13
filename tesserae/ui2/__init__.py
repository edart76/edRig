
#import maya.OpenMayaUI as omui
from edRig import omui
from edRig import QtWidgets
#from sip import wrapInstance
from shiboken2 import wrapInstance

def getMayaWindow():
	ptr = omui.MQtUtil.mainWindow()
	widget = wrapInstance( long( ptr ), QtWidgets.QWidget )
	return widget