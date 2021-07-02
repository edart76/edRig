
""" maya-specific graph functions"""
from edRig import cmds, EdNode, scene

def listOpNodes():
    """ returns list of all nodes created by tesserae """
    allNodes = cmds.ls("::*")
    return scene.listTaggedNodes(allNodes, searchTag="opTag")

def clearAllOpNodes():
    """ to be called on reset all as failsafe way of clearing scene """
    cmds.delete( listOpNodes() )




