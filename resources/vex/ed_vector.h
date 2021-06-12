
#ifndef _ED_VECTOR_H

#define _ED_VECTOR_H
#include "array.h"

#define EPS 0.00001

// lib file for pure vector operations


function vector projectpostoplane(
    vector normalpos;
    vector normaldir;
    vector projectpos;
){
    // project given position to plane formed by normalpos and normaldir
    return (dot(normaldir, normalpos - projectpos) * normaldir) + projectpos;
}

function void skewlinepoints(
    vector origa; vector dira;
    vector origb; vector dirb;
    // outputs
    vector pointa; vector pointb;
){

    // don't return point parametres,
    // they can be recovered trivially if needed
    vector normal = cross(dira, dirb);
    //vector normal = cross(dirb, dira);
    // get perpendicular direction between skewlines
    vector normalb = cross(dirb, normal);
    // get perpendicular displacement distance
    float displacement = dot(origb - origa, normalb);
    // get slant of dira into perpendicular direction
    float dirslant = dot(dira, normalb);
    //float dirslant = dot(normalb, dira);

    pointa = origa +  dira * displacement / dirslant;

    // same for other line
    vector normal1 = cross(dira, normal);
    pointb = origb + dirb * dot(origa - origb, normal1) / dot(dirb, normal1);
    return;
}



#endif
