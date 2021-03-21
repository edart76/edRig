import sys, os
""" script run on houdini startup and scene open 
on version update remember to copy 123.py and 456.py into new
programFiles/houdini.xx.xx/scripts


"""


def onHoudiniStartup(*args, **kwargs):
	""" append environment variables,
	could never get houdini.env to work properly """
	import hou
	hInstall = hou.getenv("HFS") # C:/PROGRA~1/SIDEEF~1/HOUDIN~1.287
	#pathAdd = r"F:/all_projects_desktop/common/edCode/edRig/resources/;"
	# fullVar = "F:/all_projects_desktop/common/edCode/edRig/resources/vex;C:\Program Files\Side Effects Software\Houdini 18.0.287\houdini\vex;C:\Program Files\Side Effects Software\Houdini 18.0.287\houdini\vex\include"
	#
	vexPaths = ["F:/all_projects_desktop/common/edCode/edRig/resources/vex",
	            ]

	vexPath = ";".join([
		vexPaths[0], hInstall + "/houdini/vex/", hInstall + "/houdini/vex/include"])
	hou.putenv("HOUDINI_VEX_PATH", vexPath)


def onSceneOpen(*args, **kwargs):
	""" run whenever houdini scene is loaded """

