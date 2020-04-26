
/* functions for helping with the component system
drawing points from pieces, connecting pieces etc
*/
#ifndef COMPONENT_H

#include "array.h"

function int[] pointsfrompiece(int geo; int piece){
    // returns all points contained in target piece
    // string ex = "i\x40piece=="+itoa(piece);
    string ex = "@piece=="+itoa(piece);
    return pointsmatching(geo, ex);
}




#define COMPONENT_H 1
#endif
