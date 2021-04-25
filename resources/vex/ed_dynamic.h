
#ifndef _ED_DYNAMIC_H

#define _ED_DYNAMIC_H
#include "array.h"
#include "ed_poly.h"
#include "ed_group.h"

function matrix3 tangentmatrix(int geo;
    int face){
        // return orientation matrix for polygon face
        // oriented to face gradient
        vector2 samplepos = set(0.5, 0.5);
        vector grad = normalize(primduv(geo, face, samplepos, 1, 1));
        vector N = normalize(prim(geo, "N", face));
        vector bitan = cross(grad, N);

        return matrix3(grad, N, bitan);
    }


#define SS_FLATTENLENGTH = 0
#define SS_PRESERVELENGTH = 1

function vector projectsurfacespace(int geo;
    vector origin; vector dir; int face;
    int mode;
    // output references
    int escapehedge;
    vector escapepos;
    vector escapedir
)
    {
    /* given face and vector to project,
    flatten it into surface space and project it out

    mode: either squash a high-angle vector
    to its direct projection,
    or restore its length in surface space

    escapehedge: returns the prim hedge index crossed by the
    flattened vector, or -1 if vector terminates in this prim
    escapepos: position at which vector escapes
    escapedir: portion of vector lying outside prim
    */


    }




#endif
