### just get it done son
import edRig.core as core
from edRig.core import con, ECN, EdPar
import maya.cmds as cmds
import edRig.curve as curve

##### SO OLD ####
class Spine():
    #
    #
    # pass hip and chest inputs and drawn spine crv)
    #ssssSS
    def buildTechSpine(self, hipIn, chestIn, spineCrv):
        # builds end tech: curve rebuild, dynamics, output curve
        # sort limits beforehand
        # squash stretch will also go here if necessary

        # rebuild to cartoon to dynamics
        spineShp = cmds.listRelatives(spineCrv)

        # make base group for spinespace
        spineGrp = cmds.group(hipIn, chestIn, spineCrv, n="spine_base_grp")
        hipPos = cmds.xform(hipIn, q=True, ws=True, t=True)
        chestPos = cmds.xform(chestIn, q=True, ws=True, t=True)
        spineVec = []
        for i in range(3):
            spineVec.append(chestPos[i] - hipPos[i])
            #print spineVec
        #print "chestPos is {}".format(chestPos)
        #print chestPos[1]
        #spineVec[0] = chestPos[0] - hipPos[0]
        spineVecMag = core.mag(spineVec)


        # make sparse linear curve for overall control
        sparseCrv = cmds.curve(degree=1, point=[hipPos, [0,0,0], [0,0,0],
            chestPos], n="spine_sparse_crv")
        sparseShp = cmds.listRelatives(sparseCrv, shapes=True)
        sparseShp = cmds.rename(sparseShp, sparseCrv+"shape")

        #spine ctrl point matrix mults
        chestPmm = ECN("pmm", "chestIn_pmm")
        hipPmm = ECN("pmm", "hipIn_pmm")
        for i, x in enumerate([hipIn, chestIn]):
            cmds.addAttr(x, ln="inf", at="double", min=0,
                dv=spineVecMag/3.0, k=True)
            pmm = ECN("pmm", x+"_pmm")
            con(x+".matrix", pmm+".inMatrix")
            if i == 1:
                inverse = ECN("mdl", "chestInf_neg")
                cmds.setAttr(inverse+".input1", -1)
                con(x+".inf", inverse+".input2")
                con(inverse+".output", pmm+".inPointY")
            else:
                con(x+".inf", pmm+".inPointY")
            con(pmm+".output", "{}.controlPoints[{}]".format(sparseShp, i+1))
            con(x+".translate", "{}.controlPoints[{}]".format(sparseShp, i*3))
            # might be better to decompose matrix here but we'll see

        # rebuild curve
        spineInfo = {}
        curveInfo = curve.getCurveInfo(spineShp)
        print "curveInfo is {}".format(curveInfo)
        # :(

        spineRbld = ECN("rebuildCrv", "spine_sparse_rebuild")
        matchedCrv = cmds.duplicate(sparseCrv, n="spine_rebuilt_crv")[0]
        matchedShp = cmds.listRelatives(matchedCrv, shapes=True)
        matchedShp = cmds.rename(matchedShp, matchedCrv+"shape")

        con(sparseShp+".local", spineRbld+".inputCurve")
        con(spineRbld+".outputCurve", matchedShp+".create")
        cmds.setAttr(spineRbld+".spans", spineInfo["spans"])
        cmds.setAttr(spineRbld+".degree", spineInfo["degree"])
        curve.matchCurve(matchedShp, spineShp)
