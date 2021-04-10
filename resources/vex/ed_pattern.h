
#ifndef _ED_PATTERN_H

#define _ED_PATTERN_H
#include "array.h"
#include "ed_poly.h"

/*
Higher level functions for creating patterns, arrangements etc
*/


function int sPattern(){
    vector points[] = {
        {0, 0, 0}, {1, 0, 0},
        {1, 1, 0}, {0, 1, 0},
        {0, 2, 0}, {1, 2, 0}
    };
    for( int i=0; i < len(points); i++){
        int newpt = addpoint(0, points[i]);
    }
    return 1;
};



// nifty dimensional coordinate system I worked out for tet points
function int[] tetrahedralpoints(int seedpts[];
    vector4 existing[]; vector poses[];
    int skimvalue;
    int denseconnections){
        /* tetrahedron points treated as 4d coordinates -
        each axis corresponding to each vertex direction
        iteration is sum of all values in vector -
        space vectors reverse every second iteration
        returns array of all created points
        skimvalue is optimisation, to be removed
        from point indices
        */

        vector tetax0 = {1, 1, 1};
        vector tetax1 = {-1, -1, 1};
        vector tetax3 = {-1, 1, -1};
        vector tetax2 = {1, -1, -1};

        vector axes[] = array(tetax0, tetax1, tetax2, tetax3);

        int result[];
        foreach(int pt; seedpts){
            // vector4 coord = point(0, "coord", pt);
            pt = pt - skimvalue;
            vector4 coord = existing[pt];
            //vector pos = point(0, "P", pt);
            vector pos = poses[pt];
            int iter = int(sum(coord));

            // iterate through axes
            for (size_t i = 0; i < 4; i++) {
                // get new coord
                vector4 newptcoord = coord;
                vector dir = axes[i];
                int inc = 1;
                if ((iter % 2) == 1){
                    dir = -dir;
                    inc = -1;
                }

                newptcoord[i] = newptcoord[i] + inc;
                // check if it's already been passed
                int lookup = (find(existing, newptcoord));
                if (lookup > -1){
                    if(denseconnections){
                        int nprim = addprim(
                            0, "polyline",
                            lookup, pt);
                    }
                    continue;
                }


                int newpt = addpointline(0, pos + dir, pt )[0];
                setpointattrib(0, "coord", newpt, newptcoord);
                append(poses, pos + dir);
                append(existing, newptcoord);
                append(result, newpt);
                //setpointattrib(0, "result", newpt, result);
                setpointattrib(0, "seedpts", newpt, seedpts);
            }
        }
        return result;
    }

function int[] gentetrahedralpoints(int iterations; int denseconnections){
    // creates tet pattern from nothing
    int seed = addpoint(0, {0, 0, 0});
    vector4 existing[] = array({0, 0, 0, 0});
    vector poses[] = array({0, 0, 0});
    int seedpts[] = array(seed);
    int skimvalue = 0;
    for (size_t i = 0; i < iterations; i++) {
        int nprevseeds = len(seedpts);
        seedpts = tetrahedralpoints(seedpts, existing, poses,
            skimvalue,
            denseconnections);
        // remove the previous existing points
        // not necessary for the next iteration
        // existing = existing[nprevseeds-1:];
        // poses = poses[nprevseeds-1:];
        // skimvalue = nprevseeds -1;
    }
    return seedpts;
}

#endif
