# define base tile classes and auxiliaries
import random

class Tile(object):
    # semi-abstract base class
    def __init__(self):
        print "Tile instantiated"
        self.UUID = None
        pass

    self.name = ""
    self.displayName = ""






class UiTile(Tile, QtStuff):
    # procedural framework to generate
    # UI for any rigOp passed to it

    def __init__(self, Op=None, name="blankTile"):
        super(UiTile, self).__init__()

        self.tileOp = None
        if Op:
            # nothing is instantiated yet
            self.tileOp = Op(name)
            # there we go
            """if an op CLASS is supplied,
            then the tile instantiates an instance
            of the op with the passed name
            the tile is only instantiated when it's created
            in the graph, the available list is just strings
            it may be necessary to do metaclass stuff with this
            to make the available tiles work as base classes for
            their tile op type
            """
        else:
            # add default later
            raise RuntimeError("no op supplied to tile")
            # we need this op to exist
        self.buildUiElements()

    def executeOpPlan(self):
        # execute the plan method of the bound op,
        # passing all available inputs as argument
        self.planData = self.tileOp.plan(self.tileInputs)
        self.updateIO(self.planData)

    def executeOpBuild(self):
        self.buildData = self.tileOp.build(self.tileInputs)
        self.updateIO(self.buildData)

    def executeOpRun(self):
        self.runData = self.tileOp.run(self.tileInputs)
        self.updateIO(self.runData)


    def buildUiElements(self):
        """ builds all node graph visual tourist tat
        procedurally from attributes of tile's Op
        sounds scary """

        self.buildInputs()
        self.buildOutputs()
        self.buildSidebarElements()
        self.buildTileGrpahic()

    def buildInputs(self):
        """iterates over all inputs
        defined in class input dict - for each,
        creates input plug and sidebar parametre
        still no idea how to handle parametre stuff
        """

        pass

    def buildOutputs():
        pass

    def buildKnob(mode="input"):
        # probably getting into lib territory, have
        # this call a base function

    def buildTileGraphic():
        # builds the tile size procedurally depending on knob numbers,
        # OR rebuilds the node from custom data defining shape,
        # knob locations, image etc
