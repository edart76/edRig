
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


function vector vectortoline(
    vector linestart; vector lineend;
    vector point; float t;
){
    // parametric vector to line
    return (1.0 - t) * linestart + t * lineend - point;
}

function vector nearestpointonline(
    vector linestart; vector lineend;
    vector point;
){
    // snap point to closest position on line between 2 other positions
    // from John Hughes on maths stackexchange
    vector nul = {0, 0, 0};
    vector v = lineend - linestart;
    vector u = linestart - point;
    float t = - dot(v, u) / dot(v, v);
    if((0.0 <= t) && (t <= 1.0)){
        return vectortoline(linestart, lineend, nul, t);
    }
    float lena = length(vectortoline(linestart, lineend, point, 0.0));
    float lenb = length(vectortoline(linestart, lineend, point, 1.0));
    if(lena < lenb){
        return linestart;    }
    else{
        return lineend;    }
}


function void skewlinepoints(
    vector origa; vector dira;
    vector origb; vector dirb;
    // outputs
    vector pointa; vector pointb;
){

    // don't return point parametres,
    // they can be recovered trivially if needed
    vector normal = normalize(cross(dira, dirb));
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
    vector normala = cross(dira, normal);
    pointb = origb + dirb * dot(origa - origb, normala) / dot(dirb, normala);
    return;
}



#endif
