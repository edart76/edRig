""" tools for loading and reloading plugins """

from maya import cmds

pluginNames = [
	"edPush"
]


def reloadEdPlugin():
	for i in pluginNames:
		reloadPlugin(i)

def reloadPlugin(name):
	cmds.flushUndo()
	cmds.unloadPlugin(name)
	cmds.loadPlugin(name)
