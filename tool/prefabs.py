""" premade setups to save time """

import functools

from edRig import cmds, ECA, attr, plug


def trigNodeMenu():
	""" create animcurve with trig functions """

	if cmds.window("trigMenu", exists = True):
		cmds.deleteUI("trigMenu")
	#create actual window
	UIwindow = cmds.window("trigMenu", title="trigMenu",
	                       w=100, h=100, sizeable=True)
	mainLayout = cmds.columnLayout(w = 100, h =100)
	# add trig nodes as buttons

	for i in reversed(list(plug.trigModes.keys())):
		cmds.button(label=i, w=100, command=functools.partial(
			plug.trigPlug, mode=i))
	cmds.showWindow("trigMenu")




