
"""run patching operations on cmds modules"""

from edRig.maya.core.wrap import (
	patchCmdsGetAttr, wrapListFns,
	CmdsDescriptor, patchMObjectWeakrefs,
)

# wrap list functions to return lists
# implement lazy lookup cache to flatten suitable arguments to strings
from edRig import cmds
import edRig
import edRig.dcc
descriptor = CmdsDescriptor(cmds)
setattr(edRig, "cmds", descriptor)
setattr(edRig.dcc, "cmds", descriptor)
#wrapListFns()
patchMObjectWeakrefs()

print("edrig maya init complete")
from edRig import cmds

import inspect

from edRig.maya.core.node import ECA, ECN, EdNode