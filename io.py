"""interfacing with other dccs?"""


"""the main reason behind this is to work out a consistent
import node
interface is difficult part
consider:
importing geometry composed of multiple parts

ioNode
+ ioGeo
+ freeGeo

ioGeo is the base geometry and transforms contained in the target file - 
this is essentially stored in the interface
freeGeo is a perfect mirror of ioGeo? free to be parented however? idk """