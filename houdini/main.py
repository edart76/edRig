
""" place to put all the random stuff in houdini you need """
from edRig import hou, stateutils
from edRig.houdini import core

def makeCtrl(kwargs):
	""" creates a yellow, circular null named CTRL
	in the current network view,
	or returns existing ctrl """

	yellow = (220, 180, 0)
	pane = stateutils.activePane(kwargs)
	if isinstance(pane, hou.NetworkEditor):

		networkNode = pane.pwd() # node containing panel path

		# check for preexisting control
		if any(i.name() == "CTRL" for i in networkNode.children()):
			ctrl = networkNode.item("CTRL")
			return ctrl

		# create control node
		ctrl = networkNode.createNode("null", node_name="CTRL")
		yellowCol = hou.Color(yellow)
		ctrl.setUserData("nodeshape", "circle")
		ctrl.setColor(yellowCol)

		# hide default parametres
		ptg = ctrl.parmTemplateGroup()
		for i in ("copyinput", "cacheinput"):
			ptg.hide( i, True)
		ctrl.setParmTemplateGroup(ptg)

		# set position
		pos = pane.cursorPosition()
		ctrl.setPosition(pos)

	else:
		# print("click and drag this tool to the network editor")
		pass


def makeComponentBase(kwargs):
	""" creates a template geometry node for a "component" HDA,
	containing common attributes and enabling domain lookup
	these can then be turned into HDAs """

	pane = stateutils.activePane(kwargs)
	if not isinstance(pane, hou.NetworkEditor):
		return None
	networkNode = pane.pwd()  # node containing panel path

	geo = networkNode.createNode("geometry", node_name="componentBase")

	# create component attribute tab
	ptg = geo.parmTemplateGroup()

	path = hou.StringParmTemplate("domainGeo", "domainGeo", 1,
	            string_type=hou.stringParmType.NodeReference)

	folder = hou.folderParmTemplate("component", "component",
	            parm_templates=(path, ))
	ptg.insertBefore(0, folder)
	geo.setParmTemplateGroup(ptg)





# all possible network node shapes
nodeShapes = ('rect', 'bone', 'bulge', 'bulge_down', 'burst', 'camera',
              'chevron_down', 'chevron_up', 'cigar', 'circle', 'clipped_left',
              'clipped_right', 'cloud', 'diamond', 'ensign', 'gurgle',
              'light', 'null', 'oval', 'peanut', 'pointy', 'slash', 'squared',
              'star', 'tabbed_left', 'tabbed_right', 'task', 'tilted',
              'trapezoid_down', 'trapezoid_up', 'wave')