"""copy and paste this file to your houdini scripts folder"""

import hou
hou.hscript("source 123.cmd")

from edRig.houdini import startup

startup.onHoudiniStartup()