import hou

# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/rings")

# Code for /obj/rings/attributes_to_params
hou_node = hou_parent.createNode("python", "attributes_to_params", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-18.8638, 7.18183))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(False)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_parm_template_group = hou.ParmTemplateGroup()
# Code for parameter template
hou_parm_template = hou.StringParmTemplate("python", "Python Code", 1, default_value=(["node = hou.pwd()\ngeo = node.geometry()\n\n# Add code to modify contents of geo.\n# Use drop down menu to select examples.\n"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="import pythonscriptmenu\n\nreturn pythonscriptmenu.buildSnippetMenu('Sop/pythonscript/python')", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.StringReplace)
hou_parm_template.setTags({"editor": "1", "editorlang": "python", "editorlines": "20-50"})
hou_parm_template_group.append(hou_parm_template)
# Code for parameter template
hou_parm_template = hou.FolderParmTemplate("paramfolder", "Param Folder", folder_type=hou.folderType.Tabs, default_value=0, ends_tab_group=False)
# Code for parameter template
hou_parm_template2 = hou.IntParmTemplate("iteration", "Iteration", 1, default_value=([0]), min=0, max=10, min_is_strict=False, max_is_strict=False, naming_scheme=hou.parmNamingScheme.Base1, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal, menu_use_token=False)
hou_parm_template.addParmTemplate(hou_parm_template2)
# Code for parameter template
hou_parm_template2 = hou.IntParmTemplate("ivalue", "Ivalue", 1, default_value=([0]), min=0, max=10, min_is_strict=False, max_is_strict=False, naming_scheme=hou.parmNamingScheme.Base1, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal, menu_use_token=False)
hou_parm_template.addParmTemplate(hou_parm_template2)
# Code for parameter template
hou_parm_template2 = hou.IntParmTemplate("numiterations", "Numiterations", 1, default_value=([0]), min=0, max=10, min_is_strict=False, max_is_strict=False, naming_scheme=hou.parmNamingScheme.Base1, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal, menu_use_token=False)
hou_parm_template.addParmTemplate(hou_parm_template2)
# Code for parameter template
hou_parm_template2 = hou.FloatParmTemplate("value", "Value", 1, default_value=([0]), min=0, max=10, min_is_strict=False, max_is_strict=False, look=hou.parmLook.Regular, naming_scheme=hou.parmNamingScheme.Base1)
hou_parm_template.addParmTemplate(hou_parm_template2)
hou_parm_template_group.append(hou_parm_template)
hou_node.setParmTemplateGroup(hou_parm_template_group)
# Code for /obj/rings/attributes_to_params/python parm
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/rings/attributes_to_params")
hou_parm = hou_node.parm("python")
hou_parm.lock(False)
hou_parm.set("node = hou.pwd()\ngeo = node.geometry()\n\nfrom six import iteritems\n\ndef parmTemplateForAttrib(attrib, name=None):\n    \"\"\" given attrib, return suitable parmtemplate to represent its value\n    \"\"\"\n    # discount array elements\n    if attrib.isArrayType():\n            return None\n\n    name = name or attrib.name()\n\n    # find correct number of elements\n    if isinstance(attrib.dataType(), tuple):\n            nComponents = len(attrib.dataType())\n            parmType = (attrib.dataType[0])\n    else:\n            nComponents = 1\n            parmType = (attrib.dataType())\n\n    default = attrib.defaultValue()\n    if not isinstance(default, tuple):\n            default = (default, )\n    templateTypes = {hou.attribData.Int : hou.IntParmTemplate,\n                     hou.attribData.Float : hou.FloatParmTemplate,\n                     hou.attribData.String : hou.StringParmTemplate}\n    temp = templateTypes[parmType](name, name.title(),\n                                   nComponents,\n                                   default_value=default)\n    return temp\nallAttrs = geo.globalAttribs()\n\ndetailMap = {}\nfor i in allAttrs:\n    detailMap[i] = geo.attribValue(i)\n\nfolderName = \"paramfolder\"\nfolderLabel = \"Param Folder\"\n\ngroup = node.parmTemplateGroup()\nfolder = group.findFolder(folderLabel)\nparamNames = [i.name() for i in folder.parmTemplates() ]\n\nfor attrib, value in iteritems(detailMap):\n    if not attrib.name() in paramNames:\n        newParm = parmTemplateForAttrib(attrib) \n        folder.addParmTemplate(newParm)\n        group.appendToFolder(folderLabel, newParm)\nnode.setParmTemplateGroup(group)\nfor attrib, value in iteritems(detailMap):\n    parm = node.parm(attrib.name())\n    parm.set( value )\n        \nprint node.asCode()\n")
hou_parm.setAutoscope(False)


# Code for /obj/rings/attributes_to_params/paramfolder parm
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/rings/attributes_to_params")
hou_parm = hou_node.parm("paramfolder")
hou_parm.lock(False)
hou_parm.set(0)
hou_parm.setAutoscope(False)


hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/rings/attributes_to_params
hou_node = hou_parent.node("attributes_to_params")
if hou_parent.node("foreach_count1") is not None:
    hou_node.setInput(0, hou_parent.node("foreach_count1"), 0)
hou_node.setUserData("___Version___", "18.0.287")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("18.0.287")
