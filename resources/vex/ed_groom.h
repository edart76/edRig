#ifndef __ED_GROOM_H

// modifications and extensions to existing groom tools

#include "groom.h"
#include "array.h"


void advect_points(int skin_file; vector positions[]; vector vel[];
    const int points[]; int lockpoints[]; vector guideorigin){
        // extending base advect_points to allow array of points to lock,
        // removing check for "visible" attribute
        vector rests[] = positions[0:-1];
        foreach( int i; int pt; points){
            if( index( lockpoints, pt) > -1 ){ // point in points to lock
                continue;
            }
            positions[i] += vel[i];

            if(i==0){ // snap origin to nearest point on skin geo
                // useless for sculpting
                //int prim;
                //vector primuv;
                //xyzdist(skin_file, positions[i], prim, primuv);
                //guideorigin = primuv(skin_file, "P", prim, primuv);
            }
            //if( len(lockpoints))
        }
    }


#define __ED_GROOM_H
#endif
