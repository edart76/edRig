
""" for working with parametres """
from six import iteritems
from edRig import hou

def allParmTemplates(group_or_folder):
	for parm_template in group_or_folder.parmTemplates():
		yield parm_template

	# Note that we don't want to return parm templates inside multiparm
	# blocks, so we verify that the folder parm template is actually
	# for a folder.
		if (parm_template.type() == hou.parmTemplateType.Folder and
		parm_template.isActualFolder()):
			for sub_parm_template in allParmTemplates(parm_template):
				yield sub_parm_template


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