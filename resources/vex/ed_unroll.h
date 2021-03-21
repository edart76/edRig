#ifndef _ED_UNROLL_H

#define _ED_UNROLL_H

#include "array.h"
#include "ed_poly.h"

/*
for unfolding or unrolling polygons
*/


function int unrollpoints(int geo; string normalattr){
    // flatten points into straight line
    // gather attributes to add to points
    int ids[];
    float spans[];
    float angles[];
    float totalspans[];
    float totalspan = 0.0;
    // initpointattrs(geo);
    //addattrib(0, "point", "relpos", vector(set(1, 1, 1)));

    // for (size_t i = 0; i < npoints(0); i++) {
    //     setpointattrib(geo, "id", i, i);
    //     if (i < 1){
    //         vector relpos = set(0, 0, 0);
    //         setpointattrib(geo, "relpos", i, relpos);
    //         continue;
    //     }
    //     vector relpos = point(geo, "P", i)
    //         - point(geo, "P", i-1);
    //     setpointattrib(geo, "relpos", i, relpos, "add");
    // }
    for (size_t i = 0; i < npoints(geo); i++) {
        append(ids, i);
        if (i == 0){
            append(spans, 0);
            append(totalspans, 0);
            append(angles, 0);
            continue;
        }  //

        // get distance to previous point
        vector pos = point(geo, "P", i);
        vector ppos = point(geo, "P", i - 1);
        vector rpos = pos - ppos;

        setpointattrib(0, "relpos", i, rpos);

        float span = length(rpos);
        append(spans, span);
        totalspan = totalspan + span;
        setpointattrib(0, "span", i, span);
        setpointattrib(0, "totalspan", i, totalspan);

        append(totalspans, totalspan);

        int id2 = point(0, "id", i);
        setpointattrib(0, "id2", i, id2);

        if (i == 1){ // can't fold first segment
            append(angles, 0);
            continue;
        }

        // vector of previous edge

        vector pppos = point(geo, "P", i - 2);

        vector prevvec = normalize(ppos - pppos);
        vector n = point(geo, normalattr, i);

        // get flattened position as extension of
        //previous edge, by span
        vector flatpos = (prevvec * span );

        // get dot product
        float theta = dot(normalize(rpos), normalize(prevvec)) ;
        // this really powerfully did not work
        // spent a day being totally incompetent, it was fun

        vector signvec = normalize(cross((rpos), prevvec));

        theta = atan2(rpos[1], rpos[0]) -
            atan2(prevvec[1], prevvec[0]);
        if( ( theta < -PI ) ){
            theta = theta + 2*PI ;
        }
        if( ( PI < theta ) ){
            theta = theta - 2*PI ;
        }


        setpointattrib(0, "theta", i, theta);


        // test output
        matrix3 id = ident();
        rotate(id, (theta) , n);

        vector testpos = flatpos * id + ppos;

        setpointattrib(0, "P", i, testpos);

    }
    vector poses[] = pointpositions(geo);
    float length = sumpointdistances(geo, ids);

    return 1;

}


function int rollpoints(int geo; float weights[]){
    // unroll each point sequentially according to weight
    vector baseposes[] = pointpositions(geo);
    vector poses[] = pointpositions(geo);

    for (size_t i = 0; i < npoints(0); i++) {
        if( i < 2){ // not first segment
            continue;
        }

        // reconstruct outer product frame

        vector pos = poses[i];
        vector ppos = poses[i - 1];
        vector pppos = poses[ i - 2];
        vector oldrpos = point(0, "relpos", i);
        vector newrpos = pos - ppos;

        vector prevvec = ppos - pppos;
        vector n = normalize(point(geo, "N", i - 1));
        float span = point(geo, "span", i);
        vector flatpos = (normalize(prevvec)* span );

        // rotate identity around normal by theta * weight
        matrix3 id = ident();
        float theta = point(geo, "theta", i);
        float weight = weights[i];
        rotate(id, (theta) * weight, n);

        vector newpos = flatpos * id + ppos;

        vector result = newpos;
        setpointattrib(geo, "P", i, result);
        poses[i] = result;

    }
    setdetailattrib(geo, "weights", weights);
    return 1;
}

function int rollpoints(int geo; float weight){
    float weights[] = initarray(npoints(geo), weight);
    return rollpoints(geo, weights);
}

function int rollpoints(int geo; string weightattr){
    float weights[] = initarray(npoints(geo), 0.0);
    for (size_t i = 0; i < npoints(geo); i++) {
        float weight = point(geo, weightattr, i);
        weights[i] = weight;
    }
    return rollpoints(geo, weights);
}

#endif
