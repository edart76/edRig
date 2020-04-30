#ifndef MATHS_H
// general maths things

function float mix(float x; float y; float a){
    // blend values x and y via a
    // straight port from opengl
    return x * (1.0 - a) + y * a;
}




#define MATHS_H 1
#endif
