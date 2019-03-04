# info on the node graph field
from PySide2 import QtGui, QtCore, QtWidgets
from edRig.tilepile.jchan2 import NodeGraph, Node
from edRig.tilepile.jchan2.base import actions
from edRig.layers.jointlayers import JointCurveOp
from edRig.layers.curvelayers import VariableFkOp
from edRig.layers import base
from edRig.tilepile.jchan2.base.vendor import NodeVendor  # i hate it
from edRig.tilepile.oplist import ValidList
from edRig.layers.action import ActionList, ActionItem

import uuid
import types
import inspect
from edRig import core, attrio
import PySide2


class GraphViewWidget(NodeGraph):
	"""holds node graph view and interacts with
	rig controller"""

	# experimental signals
	tilesConnectionChanged = QtCore.Signal(list, list)
	controller = None

	def __init__(self, parent=None):
		NodeGraph.__init__(self, parent=parent)
		# clear out all registered nodes
		self.clearRegister()

		self.controller = base.RIG_CONTROLLER()
		# self.register_node(TileOpMasterNode)
		# self.createTile(opClass=JointCurveOp)
		# self.createTile(opClass=VariableFkOp)

		self.registerOpClasses(ValidList.ops)
		self.patch_context_menu()
		actions.setup_actions(self)

		# signals
		self.viewer().node_delete_called.connect(self.onNodeDelete)

	def registerOpClasses(self, opClassList):
		for i in opClassList:
			opDict = {
				"opClass": i
			}
			# tileName = str(i)
			tileName = i.__name__
			print "tileName is {}".format(tileName)

			TileOpNode = type(tileName, (TileOpMasterNode,), opDict)
			TileOpNode.NODE_NAME = tileName + "Tile"
			self.register_node(TileOpNode, alias=tileName)
			opDict.clear()

	def buildRigToStep(self, step=None):
		self.controller.indexFromStepName(step)
		print "step is " + step
		print "let's build this heckin rig boyos"
		self.controller.rigItLikeYouDigIt()

	def clearRegister(self):
		"""clears registered nodes"""
		NodeVendor.clearRegister()

	def refreshRegisteredOps(self):
		"""re-casts present tiles"""
		for i in self.all_nodes():
			print "op to update is {}".format(i.opInstance)
			self.controller.updateOp(i.opInstance)
		pass

	def updateController(self):
		"""updates internal controller graph"""
		if not self.controller:
			print "no controller"
			return

	def create_node(self, node_type, name=None, selected=True, color=None, pos=None,
	                updateController=True):
		# augments base create_node method
		node = super(GraphViewWidget, self).create_node(node_type, name=None, selected=True, color=None, pos=None)
		if self.controller and node.opInstance and updateController:
			self.controller.addOp(node.opInstance)
			node.set_name(node.opInstance.opName)
		return node

	def create_tile(self, node_type="whatevs", opClass=None,
	                updateController=True):
		# augments base create_node method
		print "creating tile"
		if opClass:
			newTile = self.create_node("eyyyyy.TileOpMasterNode",
			                           updateController=updateController)
			# for duplication, don't forget to check if tile has op attached
			# carting round one special case isn't too bad
			print "new tile is {} with op {}".format(newTile, opClass)
		else:
			newTile = self.create_node(node_type,
			                           updateController=updateController)
		if self.controller and updateController:
			self.controller.addOp(newTile.opInstance)
			# print "controller opGraph is {}".format(self.controller.opGraph)
		return newTile

	def delete_node(self, node):
		"""unregister and destroy op before deleting node"""
		# unregister stuff
		print "deleting node from graphViewWidget"
		super(GraphViewWidget, self).delete_node(node)
		if isinstance(node, TileOpMasterNode):
			self.controller.removeOp(op=node.opInstance)



	def _on_connection_changed(self, disconnected, connected,
	                           updateController=True):
		"""
		overriding base implementation to add op functionality
		"""
		super(GraphViewWidget, self)._on_connection_changed(disconnected, connected)
		# print "connection_changed"
		# print "connected is {}".format(connected)
		# need more info
		if disconnected:
			type = "disconnect"
			ports = disconnected
		elif connected:
			type = "connect"
			ports = connected
		else:
			return
		if not updateController:
			return
		sourcePort = ports[0][0]

		# string of edRig.tilepile.jchan2.widgets.port.PortItem("jc")
		sourceAttrName = sourcePort.name
		# print "sourceName is {}".format(sourceAttrName)
		sourceNode = self._model.nodes[sourcePort.node.id]
		sourceOp = sourceNode.opInstance
		# sourceOpAttr = sourceOp.outputs[sourceAttrName]

		print ""
		print "on_connect_changed"
		destPort = ports[0][1]  # assume no swaggy substance multi connections
		destAttrName = destPort.name
		print "destAttrName is {}".format(destAttrName)
		destNode = self._model.nodes[destPort.node.id]
		destOp = destNode.opInstance
		print "dest inputs is {}".format(destOp.connectableInputs())
		# destOpAttr = destOp.inputs[destAttrName]
		# works

		if connected:
			self.controller.connectOutputObjectToInput(
				outOp=sourceOp, outAttrName=sourceAttrName,
				inOp=destOp, inAttrName=destAttrName)
		elif disconnected:
			self.controller.disconnectOutputObjectFromInput(
				outOp=sourceOp, outAttrName=sourceAttrName,
				inOp=destOp, inAttrName=destAttrName)
		pass

	def serialiseGraphAndRig(self):
		"""save position and misc tile data to same dict
		used by rig"""
		print "serialiseGraphAndRig"
		saveData = {}
		opDictList = self.controller.serialiseRig()
		print "opDictList is {}".format(opDictList)

		tileList = self.all_nodes()
		for i in tileList:
			# make safe for serialisation
			#i.opClassName = i.opClass.__name__
			i.opInstanceName = i.opInstance.opName
			i.opInstanceTrueName = i.opInstance.__name__
			i.opClass = None
			i.opInstance = None

		serialisedTiles = self._serialize(self.all_nodes())

		for i in tileList:
			i.opInstance = self.controller.opGraph[i.opInstanceName]["op"]

		saveData["ops"] = opDictList
		saveData["tiles"] = serialisedTiles

		return saveData

	def loadGraphFromRig(self, rigData):
		"""apply premade controller and graph methods for deserialisation
		rigData - {"ops" : opDictList, "tiles" : serialisedTileList}
		graph connections"""

		tiles = self._deserialize(rigData["tiles"])
		newGraph = self.controller.reconstructRig(rigData["ops"])
		print "tiles and graph recreated, connecting"
		for i in tiles:
			print "i is {}".format(i)
			print "i dict is {}".format(i.__dict__)
			for n in list(newGraph.values()):
				print "n is {}".format(n)
				print "looking up name {}".format(i.opInstance.opName)
				if i.opInstance.opName == n["opName"]:
					print "setting opInstance on tile {}".format(i)
					i.opClass = n["op"].__class__
					i.opInstance = n["op"]  # already works i suppose?
				pass
	#
	# def addOpContextActions(self):
	# 	"""adds right-click options to refresh, reapply or remove
	# 	data from the op's memory
	# 	called dynamically on right-click"""
	# 	if not self.selected_nodes():
	# 		# nothing
	# 		return
	# 	rootMenu = self.context_menu()

	@staticmethod
	def modify_context_menu(graph, viewer, addMenus=None, *args, **kwargs):
		"""patches viewer's method with this one, called on right-click"""
		"""so this has become some hardcore (unnecessary) metaprogramming
		not only do we need to modify the menu, we need to set up
		new actions and signals to get information back out of it"""
		#graph = kwargs["graph"]
		viewer.context_menu().clearCustomEntries()
		print "selected nodes are {}".format([i for i in graph.selected_nodes()])
		nodes = graph.selected_nodes()
		if nodes:
			actionDicts = []
			for i in nodes:
				actions = i.getAllActions()
				#print "i actions are {}".format(actions)
				actionDicts.append(actions)
			#actionDicts = [i.getAllActions() for i in nodes]
			#print "actionDicts are {}".format(actionDicts)
			actionDict = ActionItem.consolidateActionDicts(actionDicts)
			#print "actionDict is {}".format(actionDict)
			viewer.context_menu().buildMenusFromDict(actionDict)
			# works

		pass

	def patch_context_menu(self):
		self._viewer.modify_context_menu = types.MethodType(
			self.modify_context_menu, self, self._viewer,)
		pass

	def onNodeDelete(self):
		for i in self.selected_nodes():
			self.delete_node(i)

class TPNode(Node):
	# extending base Node class for anything appearing in tilepile view
	# eventually add a config path to data or new dict, for custom node appearances
	def __init__(self):
		super(TPNode, self).__init__()
		# options appearing on right click when node is selected
		self.actions = {}

	def getAllActions(self):
		return self.actions



class TileOpMasterNode(TPNode):
	# bridge between rigging and ui
	__identifier__ = "eyyyyy"
	NODE_NAME = "TileOpNode"
	# not a fan of this identifier stuff - may in time remove
	_opClass = None
	_opInstance = None
	opInputs = {"blank": "input"}
	opOutputs = None
	opData = None

	def __init__(self, passedOpClass=None, initTile=True):
		super(TileOpMasterNode, self).__init__()

		if passedOpClass:  # type should do this anyway
			self.opClass = passedOpClass

		# for some things, like refresh, initialisation must be controlled
		if initTile:
			self.instantiateOpWithTile()
			self.makeOpTileIO()
			self.makeWidgets()

	@property
	def opInstance(self):
		return self._opInstance

	@opInstance.setter
	def opInstance(self, val):
		if val:
			self.opInputs = val.inputs
			self.opData = val.data
			self.opOutputs = val.outputs
		self._opInstance = val

	@property
	def opClass(self):
		return self._opInstance.__class__ if self.opInstance else self._opClass

	def instantiateOpWithTile(self, tileOpClass=None):
		if tileOpClass:
			self.opClass = tileOpClass
		print "op class is {}".format(self.opClass)
		self.opInstance = self.opClass()
		print "op instance is {}".format(self._opInstance)
		# add support for renaming ops?

		print "_opInstance inputs are {}".format(self._opInstance.inputs)

		self.opInputs = self.opInstance.connectableInputs()
		print "node opInputs connectable are {}".format(self.opInputs)
		self.opOutputs = self.opInstance.connectableOutputs()
		self.opData = self.opInstance.callData()

	def makeOpTileIO(self, inputs=True, outputs=True):
		# from OP input and output dict, create knobs in gui
		print "making {} io".format(self)
		self.clear_io()
		if inputs:
			print "making inputs"
			print "opInputs is {}".format(self.opInputs)
			for i in self.opInputs:
				print "found input {}, adding".format(i)
				multi = i.isMulti()
				knob = self.add_input(name=i.name, multi_input=multi)
				# knob.datatype = self.opInputs[i]["datatype"]
				print knob

		if outputs:
			print "making outputs"
			for i in self.opOutputs:
				print "opOutputs are {}".format([i.name for i in self.opOutputs])
				knob = self.add_output(name=i.name)
				# knob.datatype = self.opInputs[i]["datatype"]
		#self.update()
		pass

	def makeWidgets(self):
		currentWidgets = self.view.widgets
		inputNames = [i.name for i in self.opInstance.connectableInputs()]
		for i in inputNames:
			if i in currentWidgets.keys():
				continue
			i = self.opInstance.getInput(i)
			if i.dataType == "string":
				self.add_text_input(name=i.name, label=i.name, text=i.value, tooltip=i.desc)
			elif i.dataType == "enum":
				self.add_combo_menu(name=i.name, label=i.name, items=i.extras["options"],
				                    tooltip=i.desc)
			elif i.dataType == "bool":
				self.add_checkbox(name=i.name, label=i.name, text=i.extras["label"],
				                  state=i.value, tooltip=i.desc)
			elif i.dataType == "int":
				self.add_int_spinbox(name=i.name, label=i.name, value=i.value,
				                     tooltip=i.desc, max=i.extras["max"],
				                     min=i.extras["min"])
			elif i.dataType == "float":
				self.add_float_spinbox(name=i.name, label=i.name, value=i.value,
				                       tooltip=i.desc, max=i.extras["max"],
				                       min=i.extras["min"])


	def _on_widget_changed(self, name, value):
		super(TileOpMasterNode, self)._on_widget_changed(name, value)
		attr = self.opInstance.getInput(name)
		attr.value = value
		# inefficient - if speed becomes an issue refactor this

		update = self.opInstance.refreshIo(attrChanged=name)
		if update:
			# let ops dictate what deserves a refresh
			#self.makeOpTileIO()
			self.refreshTile()


	def refreshTile(self):
		"""boom, the end, start over"""
		print "refreshing tile from TPMasterNode"
		#self.update()
		#self.makeOpTileIO()
		newName = self.name()
		newOp = self.opInstance
		# make new tile with type
		newTile = self.__class__(passedOpClass=None, initTile=False)
		#newTile.opClass = self.opClass
		newTile.opInstance = self.opInstance
		newTile.set_pos(*self.pos())
		newTile.set_color(*self.color())
		newTile.set_name(self.name())

		self.graph.delete_node(self)
		self.graph.add_node(newTile)
		#
		#
		# newTile.makeWidgets()
		# newTile.makeOpTileIO()
		# self.graph.delete_node(self)

		pass
		# newTile = self.graph.create_node(node_type=self.type, color=self.color(),
		#                                  pos=self.pos(), name=self.name(),
		#                                  updateController=False)
		# newTile.opInstance = self.opInstance

		# opDict = {
		# 	"opClass": i
		# }
		# # tileName = str(i)
		# tileName = i.__name__
		# print "tileName is {}".format(tileName)
		#
		# TileOpNode = type(tileName, (TileOpMasterNode,), opDict)
		# TileOpNode.NODE_NAME = tileName + "Tile"
		# self.register_node(TileOpNode, alias=tileName)
		# opDict.clear()


	"""nodeGraphQT currently has no capacity to remove knobs - fix this"""

	####### M E T A C L A S S E S #########
	## BOIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII ##

	# op memory functions
	def opRefresh(self, *args, **kwargs):
		self.opInstance.memory.refresh(args, kwargs)

	def opRecall(self, *args, **kwargs):
		self.opInstance.memory.recall(args, kwargs)

	def opRemove(self, *args, **kwargs):
		self.opInstance.memory.remove(args, kwargs)

	def opRenewableMemory(self):
		return self.opInstance.renewableMemory()

	def opActions(self):
		print "tile opActions are {}".format(
			self.opInstance.getAllActions())
		return self.opInstance.getAllActions()

	def getAllActions(self):
		return self.opActions()

