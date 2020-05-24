
/* test geometry shader to lay out strokes
this allows strokes to move based on mesh vertex attributes
*/
#if OGSFX

#if !HIDE_OGSFX_UNIFORMS

#endif

#if !HIDE_OGSFX_STREAMS

// attributes

#endif


#else // not ogsfx, only beautiful glsl

uniform int nStrokes;

#endif

#if !HIDE_OGSFX_CODE

// shader tools
#include "shaderUtils.glsl"



void main(){

    for(int i=0; i < nStrokes; i++){
        int n = 1;
    }

}
#endif
