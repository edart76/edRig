
"""AssetRef object - smallest, lightest, most universal way of referring to an asset

All AssetRefs are fundamentally absolute uid references into the master asset table - name and version are provided for readability only and may not be correct


"""

from __future__ import annotations
import typing as T
import sys, os, pathlib, json, pprint
from functools import partial
from collections import defaultdict

import uuid, json
from collections import namedtuple

from edRig.dev.assetlib import constant


AssetRef = namedtuple("AssetRef", field_names=["uid", "path", "version"])


if __name__ == '__main__':
    a = uuid.uuid1()
