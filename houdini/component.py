
from edRig import hou
from edRig.houdini import core
reload(core)

""" functions supporting component-based modelling """

def getComponentsInNetworkBox(parent, networkBoxName="components"):
	""" returns nodes contained in specified network box
	no checking yet for specific node types
	:type parent : hou.Node /obj """
	box = parent.findNetworkBox( networkBoxName )
	if not box:
		box = core.networkBoxFromComment(parent, networkBoxName)
	return box.nodes(recurse=True)


def objectMergesForComponents( componentNodes, parent, targetMerge,
                               boxName="merge_components"):
	""" for each component obj node, creates a new objMerge under parent,
	sets path, connects to common merge
	:type componentNodes : sequence of hou.Node
	:type parent : hou.Node
	:type targetMerge : hou.Node
	i know you can do this all with one node, but this way is cooler """

	merge = core.returnNode(parent, "merge", "merge_all")

	# find and delete box and nodes if they already exist
	#box = parent.findNetworkBox( boxName )
	box = core.networkBoxFromComment(parent, boxName)
	for i in box.nodes():
		i.destroy()
	#box = parent.createNetworkBox( boxName, boxName)


	merges = []
	for i in componentNodes:
		objMerge = parent.createNode("object_merge", "merge_" + i.name())
		objMerge.setParms( { "objpath1" : i.path(),
		                     "xformtype" : 1} )

		merge.setNextInput( objMerge )
		box.addItem( objMerge )
		merges.append( objMerge )

	# set positions
	for i, val in enumerate(merges):
		#val.setPosition( hou.Vector2(0, 2.0 * i))
		val.moveToGoodPosition( relative_to_inputs=False )
	merge.moveToGoodPosition( relative_to_inputs=False, move_outputs=True )

	box.fitAroundContents()
	"""
	objmerge = geo.createNode('object_merge')
	#for parm in objmerge.parms():
	#    print parmobjmerge.parm('numobj').eval()
	objmerge.setParms({'numobj':len(selNodes_children)})
	for i in range(len(selNodes_children)):
        objmerge.setParms({'objpath%d'%(i + 1) : selNodes_children[i].path()})
    # thanks houdinitips.tumblr
	"""
	return merges




