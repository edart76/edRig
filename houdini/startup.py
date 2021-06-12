import sys, os
""" script run on houdini startup and scene open 
on version update remember to copy 123.py and 456.py into new
programFiles/houdini.xx.xx/houdini/scripts

also compose the houdini.env


"""

defaultEntry = r"""
#
# Houdini Environment Settings
#
# The contents of this file are read into the environment
# at startup.  They will override any existing entries in
# the environment.
#
# The syntax is one entry per line as follows:
#    VAR = VALUE
#
# Values may be quoted
#    VAR = "VALUE"
#
# Values may be empty
#    VAR = 
#

# Example:
#
# HOUDINI_NO_SPLASH = 1

"""


#qlibPath = "F:/all_projects_desktop/houdini/qlib/otls"
qlibPath = "F:/all_projects_desktop/houdini/qlib"

qlibEntry = """QLIB=""" + qlibPath + """\n
HOUDINI_OTLSCAN_PATH=@/otls;$QLIB/base;$QLIB/future;$QLIB/experimental\n"""

qlibEntry += """echo $HOUDINI_OTLSCAN_PATH"""

houdiniDocDir = """C:/Users/Ed/Documents/houdini18.5"""
envFile = houdiniDocDir + "/houdini.env"

#print("a")

def composeEnvFile():
	""" add entries to env file """
	lines = [
		defaultEntry,
		qlibEntry
	]
	with open(envFile, "w") as f:
		f.writelines(lines)

	import  hou
	hou.putenv("HOUDINI_OTLSCAN_PATH", "\n".join(lines))


def onHoudiniStartup(*args, **kwargs):
	""" append environment variables,
	could never get houdini.env to work properly """
	import hou

	#composeEnvFile()


	#print(hou.getenv("HOUDINI_OTLSCAN_PATH"))

	hInstall = hou.getenv("HFS") # C:/PROGRA~1/SIDEEF~1/HOUDIN~1.287
	#pathAdd = r"F:/all_projects_desktop/common/edCode/edRig/resources/;"
	# fullVar = "F:/all_projects_desktop/common/edCode/edRig/resources/vex;C:\Program Files\Side Effects Software\Houdini 18.0.287\houdini\vex;C:\Program Files\Side Effects Software\Houdini 18.0.287\houdini\vex\include"
	#
	vexPaths = ["F:/all_projects_desktop/common/edCode/edRig/resources/vex",
	            ]

	vexPath = ";".join([
		vexPaths[0], hInstall + "/houdini/vex/", hInstall + "/houdini/vex/include"])
	hou.putenv("HOUDINI_VEX_PATH", vexPath)

	baseScan = hou.getenv("HOUDINI_OTLSCAN_PATH")
	#print(baseScan)




def onSceneOpen(*args, **kwargs):
	""" run whenever houdini scene is loaded """

