
from edRig.tesserae.ops.layer import LayerOp
from maya import cmds


class ImportOp(LayerOp):
	"""imports items from the live scene and organises them
	in tesserae system. it wouldn't be too hard to make this
	update in real time, but that's not the goal here"""
	def __init__(self, name="ImportDrivenOp"):
		super(ImportOp, self).__init__(name)
		self.actions = {
			"importItem" : {
				"import0D" : None,
				"import1D" : None,
				"import2D" : None,
				"import3D" : "Nope"
				},
			"removeItem" : {}
			}
		self.mode = ""
		self.makeActions()

	def refreshIo(self, controller=None, attrChanged=None):
		"""always redraw to be safe?"""
		# update remove actions
		self.makeRemoveActions()
		self.sync()

	def defineAttrs(self):
		"""nothing created by default, all in actions"""
		pass

	# def makeActions(self, ds="012"):
	# 	"""updates valid actions based on existing inputs"""
	# 	# make inputs efficiently first
	# 	for d in ds:
	# 		action = ActionItem({
	# 			"func" : self.importItem,
	# 			"kwargs" : { "d" : d}}, name="import"+d+"D")
	# 		self.actions["importItem"]["import{}D".format(d)] = action

	def makeRemoveActions(self):
		# always allow attribute deletion
		# for i in self.inputs:
		# 	action = ActionItem({
		# 		"func" : self.removeItem,
		# 		"args" : i.name}, name="remove"+i.name)
		# 	self.actions["removeItem"][i.name] = action
		pass

	def importItem(self, d="0D", attrName=""):
		"""create string attr with user input name"""
		value = self.getSel()[0]
		if not value:
			self.log("no selection specified")
			return
		#attrName = attrName or raw_input("Name this attribute")
		attrName = raw_input("name this attribute")
		if not attrName:
			self.log("no name supplied for new import, skipping")
			return
		elif self.getInput(attrName):
			self.log("name supplied for new import is already an input")
			return
		new = self.addInput(name=attrName, dataType="string", hType="dummy",
		                     desc="imports these items from the scene as tesserae objects",
		                    default=value)
		#new.value = value
		return new

	def removeItem(self, name):
		"""remove existing item from op"""
		self.removeAttr(name, role="input")

	def getSel(self):
		return cmds.ls(sl=True)

	def execute(self):
		"""for each entry in inputs, duplicate and group"""
		for i in self.inputs:
			if "Knob" in i.name:
				continue
			spaceGrp = self.ECA("transform", name=i.name+self.mode+"_import")
			dupes = cmds.duplicate(i.value, name=i.name+"_copy")
			for n in i.value:
				cmds.setAttr(n+".visibility", 0)
			cmds.parent(dupes, spaceGrp)
			cmds.parent(spaceGrp, self.opGrp)


#


class ImportDrivenOp(ImportOp):
	"""only difference is whether an input or output appears"""
	mode = "driven"

	def makeActions(self, ds="0"):
		super(ImportDrivenOp, self).makeActions(ds)
		# only points (transforms) may be driven directly

	# make default input one day

	def importItem(self, d="0D", attrName="default"):
		text = super(ImportDrivenOp, self).importItem(attrName=attrName)
		if not text:
			return
		driven = text.copyAttr()
		driven.name = text.name+"Knob"
		driven.hType = "leaf"
		driven.dataType = d
		self.addInput(attrItem=driven)
		self.refreshIo()


class ImportDriverOp(ImportOp):
	"""only difference is whether an input or output appears"""
	mode = "driver"

	def defineAttrs(self):
		#self.importItem(d="2D")
		pass

	def importItem(self, d="0D", attrName="default"):
		text = super(ImportDriverOp, self).importItem(attrName=attrName)
		if not text:
			return
		driver = text.copyAttr()
		driver.name = text.name + "Knob"
		driver.role = "output"
		driver.hType = "leaf"
		driver.dataType = d
		self.addOutput(attrItem=driver)
		self.refreshIo()

