
#ifndef _ED_MAGNETISM_H
#include "array.h"

/*
the done thing regarding fields like this is to precompute magnetic force
over a volume and then sample it later

this is hella inefficient as long as you have fewer sample points than there would
be volume cells for the same effective resolution - this is usually a large amount

this approach also lets the field extend infinitely

*/

vector sampleMagneticField(vector pos; int poleGeo; float power;
    int blockingGeo; int doBlocking){
        // retrieve instantaneous magnetic force at point pos
        vector h;
        for(int i = 0; i < npoints(polePointGeo); i++){
            float poleVal = point( poleGeo, "pole", i );
            float polePos = point( poleGeo, "P", i);
            float force = ( polePos - pos) * poleVal /
                (pow( length(polePos - pos), power));
            h += force;
        }
        return h;
    }

#define _ED_MAGNETISM_H 1
#endif
