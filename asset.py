"""
sketches for what you would want out of an atomic asset in a database

"""

"""
consider data encoding / decoding, like animation or model data
encoding / decoding schemes will have their own versions - does this
make them assets?

data encoding method is saved as an asset dependency - any exporter or tool
loads with the associated scheme,
and automatically saves with the latest approved encoding scheme.
all encoded data prepends information about its format within itself - effectively a micro-asset

theoretically the format of an asset and the asset database itself should be
versioned in the same way, but that seems philosophically difficult
"""


from tree import Tree
from collections import namedtuple

class Database(object):

	validTags = ["model", "anim", "character"] # ?

	pass


""" object representing reference to asset somewhere else on 
the database 
version is -1 (latest) or -2 (latest approved) by default - can be set
to specific version by hand

subPath may be left as "" or set to a sub-path to a specific asset output
"""

AssetRef = namedtuple("AssetRef", ["path", "version"])


class Asset(Tree):

	# set of AssetRef objects
	dependencies = set()

	# set of string tags
	meta = set()


	pass
