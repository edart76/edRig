#ifndef _ED_ALIGN_H

#define _ED_ALIGN_H
#include "array.h"
// functions to align geometry and components

function vector bboxalign(vector alignDir; float padding;
    vector alignMin; vector alignMax;
    vector refMin; vector refMax)
    {
    // align two bounding boxes
    alignDirection.x = int(alignDirection.x);
    alignDirection.y = int(alignDirection.y);
    alignDirection.z = int(alignDirection.z);

    // length of padding
    vector padVec = -alignDirection * padding;

    // check sign of direction
    float dirSign = sign( sum(alignDirection) );
    if (dirSign < 0){
        bMin = bMax;
        refMax = refMin;
        }

    // align
    vector t = -dirSign * (bMin * alignDirection +
        refMax * -alignDirection + padVec);
    return t;
}


function int[] convex2Dpointorder(vector centre;
    vector pointpositions[]; vector normal)
    {
    /* assuming a convex arrangement of points, orders them
    sequentially based on angle to centre
    returns array of new indices : array[oldN] = newN
    */
    int n = len(pointpositions);
    int out[];

    float angles[];
    float allAngles[];
    float thetas[];
    vector base = normalize(set(1, 0, 1));
    // gather angle info
    for( int i = 0; i < n; i++){
        vector t = normalize(pointpositions[i] - centre);
        float theta = acos(dot( t, base));
        vector N = cross( t, base);
        float y = N.y;

        //float val = dot(t, base) / (length(t) * length(base))
        // correct singularity at inline points
        if(y == 0){
            if ( theta > 0){
                y = 0.00001;
            }
            else{
                y = -0.00001;
            }
        }

        //append(angles, y); // order by height of cross y component
        append(angles, theta);
        append(allAngles, theta);
        append(thetas, theta);
        // dot and cross together let us check sign across whole range
        append(out, i); // temp value to create entry
    }

    float m;
    int id;

    // sort by maximum
    for( int i = 0; i < n; i++){
        m = min(angles);
        id = floatIndex(allAngles, m);
        if( id < 0){
            id = 10000000;
        }
        // remove found value
        //removeindex(angles, id-1 );
        removevalue(angles, m);
        // set output entry
        out[i] = id;
    }
    return out;

}
#endif
