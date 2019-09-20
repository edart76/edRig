from __future__ import print_function
from edRig.structures import EnvironmentSettings
import sys, os

from edRig.node import AbsoluteNode, ECA
from edRig.attr import con

sys.dont_write_bytecode = True
ROOT_PATH = "F:" + "/" + "all_projects_desktop"
COMMON_PATH = "F:" + "/" + "all_projects_desktop/common"
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
"""this asset system is designed to work with a central "common" folder,
containing rigging files like control shape libraries, any templates you want,
but also a common material library"""

Env = EnvironmentSettings()

def log(message, **kwargs):
	print(message)
