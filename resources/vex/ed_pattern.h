
#ifndef _ED_PATTERN_H

#define _ED_PATTERN_H
#include "array.h"

/*
Higher level functions for creating patterns, arrangements etc
*/


function int sPattern(){
    vector points[6] = {
        {0, 0, 0}, {1, 0, 0},
        {1, 1, 0}, {0, 1, 0},
        {0, 2, 0}, {1, 2, 0}
    };
    for( int i=0; i < len(points); i++){
        int newpt = addpoint(0, points[i]);
    }
    return 1;
}


#endif
