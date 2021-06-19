
import edRig.core as core
# tesserae is here to save our souls
from edRig.tesserae.ops.layer import LayerOp
from edRig import curve, ECA, con, ECN, transform, cmds, om

""" redo system to use two controls - one as the normal fk 
control, and one parent as the position and bias control
tx is u,
scalex is falloff width, scaley is falloff bias, 
scalez falloff sharpness

also need a visual indicator of bias shape

"""


class VariableFkOp(LayerOp):
	# wahey

	data = {
		"it's" : "dat boi"
	}

	def defineAttrs(self):
		self.addInput(name="varFkCurve", dataType="1D",
		              desc="curve on which to create variable fk")
		self.addOutput(name="varFkCurve", dataType="1D",
		               desc="curve moving under variable fk")

	def defineSettings(self):
		self.addSetting(entryName="number controls", value=3)
		self.addSetting(entryName="curve resolution", value=20,
		                min=4, max=100)





def variableFk(targetCrv, name="varFk", numCtrls=4, numJnts=20 ):
	# you knew it was coming
	inCrv = curve.createCurve(name+"Input")
	inShape = inCrv[0]
	con(targetCrv+".local", inShape+".create")

	out = curve.duplicateCurveTf(inCrv[1])
	outShape = out["shape"]
	#outRebuild = ECn("rebuildCrv", "dfasdg")
	#outRebuild.spans = numJnts
	#con(inShape+".local", outRebuild+".inputCurve")
	#con(outRebuild+".outputCurve", outShape+".create")
	cmds.rebuildCurve(outShape, spans=numJnts-2, ch=False)
	outUp = curve.duplicateCurveTf(out["tf"], name="outUpCrv")
	outUpShape = outUp["shape"]

	parts = {}
	ctrls = {}
	parts["jnts"] = []
	parts["initPcis"] = []
	parts["stretchMags"] = []
	parts["initAims"] = []
	parts["initMatProxies"] = []
	parts["endMatMults"] = []
	parts["jntWorldDecomps"] = []

	#### # TODO: ####
	"""
	add support for init upCurve
	add scaling attribute on control
	duplicate output curve and skin (or connect cvs)
	attach controls on output curve
	pointMults on the joints to get an output upCurve
	"""

	# place joints along curve (???)
	#### NB #####
	# this is vulnerable at build to uneven parameterisation of the input curve
	# after that it should be alright, but feed it straight curves if you can
	for i in range(numJnts+1):
		#with the last joint being an end
		u = 1.0 / numJnts * i
		jnt = ECN("joint", "{}_vFk_{}jnt".format(name, i))
		parts["jnts"].append(jnt)
		jntWorldDecomp = ECN("matDecomp", "jntWorldDecomp")

		cmds.connectAttr(jnt+".worldMatrix[0]", jntWorldDecomp+".inputMatrix")
		cmds.connectAttr(jntWorldDecomp+".outputTranslate",
			outShape+".controlPoints[{}]".format(i))

		# connect output upcurve
		jntWorldPmm = ECA("pmm", "jntWorldUpPmm", "vmOff")
		jntWorldPmm.set("inPoint", (0, 3, 0))
		cmds.connectAttr(jnt+".worldMatrix[0]", jntWorldPmm+".inMatrix")
		cmds.connectAttr(jntWorldPmm+".output",
			outUpShape+".controlPoints[{}]".format(i))


		initPci = curve.pciAtU(inShape, u=u, constantU=True, purpose="initialJointPosition")
		parts["initPcis"].append(initPci)
		initLoc = ECA("locator", "initJntLoc")


		if i != 0:
			aim = transform.liveAimFromTo(
				parts["initPcis"][i-1]+".position", initPci+".position")
			parts["initAims"].append(aim)
			matProxy = ECA("locator", "initMat_proxy_loc")
			con(aim+".constraintRotate", matProxy+".rotate")
			parts["initMatProxies"].append(matProxy)
			endMatMult = ECN("multMatrix", "endMatMult")
			parts["endMatMults"].append(endMatMult)

			stretch = transform.liveDistanceBetweenPoints(
				parts["initPcis"][i-1]+".position", initPci+".position")
			parts["stretchMags"].append(stretch)


		print("jnt is {}".format(jnt))
		print("")
		placeMat = curve.matrixAtU(inShape, u=u)
		transform.matchMatrix(jnt, placeMat)

	for i in range(numJnts):
		# connect
		decomp = ECN("matDecomp", "matDecomp")
		parts["jnts"][i].rotate = parts["initAims"][i].constraintRotate
		cmds.makeIdentity(parts["jnts"][i], rotate=True, apply=True)

		con(parts["endMatMults"][i]+".matrixSum",
			decomp+".inputMatrix")
		con(decomp+".outputRotate", parts["jnts"][i]+".jointOrient")
		cmds.connectAttr(parts["initMatProxies"][i]+".matrix",
			parts["endMatMults"][i]+".matrixIn[0]")
		if i != numJnts-1:
			# all but root need rotations in parent space
			cmds.connectAttr(parts["initMatProxies"][i]+".inverseMatrix",
				parts["endMatMults"][i+1]+".matrixIn[1]")

		jnt = cmds.parent(parts["jnts"][i+1], parts["jnts"][i])[0]
		con(parts["stretchMags"][i]+".distance",
			parts["jnts"][i+1]+".translateX")

		# eyyy
		# up to this point allows continuous joint hierarchy to be riveted
		# on curve, stretching with only translateX and joint orient
		# might be handy in future for muscles

		# cmds.connectAttr(decomp+".outputTranslate",
		#     outShape+".controlPoints[{}]".format(i))

	# making this robust to a non-static input curve will require some
	# improvements, and some serious matrix swag
	# matrix method less modular but more slightly performant
	# still using sin deformer method for falloff - tangibility always wins out
	# incorporate dropoff locators too
	# to ensure no drift matrix method is necessary, otherwise dropoff may not
	# line up between layers
	# will also make true ik far, far easier

	# actually the matrix stuff is getting quite difficult - double layer it is

	# still want to investigate that ik stretch stuff thing
	parts["jnts"][-1].rotate = (0, 0, 0)
	parts["sinInfMults"] = {}
	for i in range(numCtrls):
		# parent controls to init grp so they move
		# then mult rotation of init grp and control to get effect on joints
		u = 1.0 / numCtrls * i
		initLoc = core.loc("ctrl{}_initLoc".format(i))
		#nodule'd
		# refit once I have a proper system for controls
		# fk control
		ctrl = control.FkControl("{}_vFk_ctrl{}".format(name, i))
		ctrlUdiv = ECn("mdl", "{}_vFk_ctrl{}uDiv".format(name, i))
		ctrlSinUMult = ECn("mdl", "{}_vFk_ctrl{}sinUmult".format(name, i))
		addCombine = ECn("pma", "{}_vFk_ctrl{}addCombine".format(name, i))
		ctrlSani = ECn("choice", "{}_vFk_ctrl{}sanitise".format(name, i))
		cmds.addAttr(ctrl.tf, ln="u", dv=u*10, min=0, max=10, k=True)
		cmds.addAttr(ctrl.tf, ln="falloffWidth", dv=10, min=1, k=True)
		cmds.addAttr(ctrl.tf, ln="falloffSharpness", dv=0.5, min=0, max=1, k=True)


		ctrls[i] = ctrl

		cmds.parent(ctrl.tf, initLoc)
		initLoc = curve.curveRivet(initLoc, outShape, u,
			upCrv=outUpShape, rotX=False)

		ctrl.tf.u.connect(ctrlUdiv.input1)
		ctrlUdiv.input2 = 0.1
		ctrlUdiv.output.connect(initLoc.uVal)

		sinCrvPoints = [(x*3, 0, 0) for x in range(numJnts)]
		sinCrv = curve.curveFromCvs(sinCrvPoints,
			name="ctrl{}_sinCrv".format(i))

		ctrlSinUMult.input1 = (numJnts-1)*3
		con(ctrlUdiv+".output", ctrlSinUMult+".input2")

		# convert rotate data to linear without unitConversions
		# more nuanced treatment needed for choice connections
		cmds.connectAttr(ctrl.tf+".rotate", ctrlSani+".input[0]")


		"""replace with softmod, affect sharpness and bias all through 
		ramp if possible 
		bias might have to be rotation-based """

		# set up sin deformer
		# this still gives jagged behaviour at edge of bell curve, which is
		# cool for carpal, but in future a better option should be available
		sin, sinHdl = cmds.nonLinear(sinCrv["shape"], type="sine")
		con(ctrlSinUMult+".output", sinHdl+".translateX")
		con(ctrl.tf+".falloffWidth", sinHdl+".scaleY")
		# sharpening falloff is more tricky - involves changing wavelenth,
		# offset and low and high bound to ensure curve never goes below 0
		# interestingly, this algorithm is totally indifferent to amplitude


		sin = nodule(sin)
		sin.lowBound = -0.5
		sin.highBound = 0.5
		sin.amplitude = 0.1
		sin.wavelength = 2
		sin.offset = 0.5
		cmds.rotate( 0,0,90, sinHdl, relative=True)

		parts["sinLocs"] = []
		#parts["sinPcis"] = []
		#parts["sinPcis"][i] = []

		parts["sinInfMults"][i] = []
		# numpy where you at
		# set points on sin crv
		for n in range(numJnts):
			loc = core.loc("sin{}_{}loc".format(i, n))
			pci = ECn("pci", "sin{}_{}pci".format(i, n))
			ratioDiv = ECn("md", "sin{}_{}ratioDiv".format(i, n), "div")
			infMult = ECn("md", "sin{}_{}influenceMult".format(i, n))
			parts["sinInfMults"][i].append(infMult)
			u2 = 1.0 / numJnts * n
			#print "u2 is {}".format(u2)

			con(sinCrv["shape"]+".local", pci+".inputCurve")
			pci.parameter = u2
			pci.position.connect(loc.translate)
			# cmds.connectAttr(pci+".positionY", addCombine+".input1D[{}]".format(n))
			cmds.connectAttr(loc+".translateY", addCombine+".input1D[{}]".format(n))
			# small price for tactility
			#pci.positionY.connect(ratioDiv.input1X)
			cmds.connectAttr(loc+".translateY", ratioDiv+".input1X")
			addCombine.output1D.connect(ratioDiv.input2X)

			cmds.connectAttr(ctrlSani+".output", infMult+".input1")
			con(ratioDiv+".outputX", infMult+".input2")

			parts["sinLocs"].append(loc)
			#parts["sinPcis"][i].append(pci)



		sinGrp = cmds.group(sinCrv["tf"], parts["sinLocs"], n="ctrl{}_sinGrp".format(i))

		# there's a pretty dope way to do this with sequential abnars but I'm optimising for
		# minimum nodes right now
	print("sinInfMults is {}".format(parts["sinInfMults"]))

	for m in range(numJnts):
		finalAdd = ECN("pma", "finalAdd")
		#finalAim = ECn("aim", "finalAim")
		finalConvert = ECN("choice", "final convert")
		cmds.connectAttr(finalConvert+".output", parts["jnts"][m]+".rotate")
		cmds.connectAttr(finalAdd+".output3D", finalConvert+".input[0]")

		# i'm still not sure this is the best way - having the whole thing be
		# one matrix mult would be sexier, but then we're forced to do everything by
		# either joint orients or rotate attributes

		# doing everything in linear radians is sort of sexy i supppose

		for i in range(numCtrls):
			# head hurt yet?
			cmds.connectAttr(parts["sinInfMults"][i][m]+".output",
				finalAdd+".input3D[{}]".format(i))
		# bitch i wrote this whole thing in mel once leave me alone


