
""" for working with parametres """
from six import iteritems
from edRig import hou

def parmTemplateForAttrib(attrib, name=None):
	""" given attrib, return suitable parmtemplate to represent its value
	"""
	# discount array elements
	if attrib.isArrayType():
		return None

	name = name or attrib.name()

	# find correct number of elements
	if isinstance(attrib.dataType(), tuple):
		nComponents = len(attrib.dataType())
		parmType = (attrib.dataType[0])
	else:
		nComponents = 1
		parmType = (attrib.dataType())

	default = attrib.defaultValue()
	if not isinstance(default, tuple):
		default = (default, )
	templateTypes = {hou.attribData.Int : hou.IntParmTemplate,
	                 hou.attribData.Float : hou.FloatParmTemplate,
	                 hou.attribData.String : hou.StringParmTemplate}
	temp = templateTypes[parmType](name, name.title(),
	                               nComponents,
	                               default_value=default)
	return temp