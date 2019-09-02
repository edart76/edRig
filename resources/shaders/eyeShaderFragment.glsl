
/* main core for WePresent eye shader - using various maps
realised from geometry and colour, we will ensoul each inhabitant
of our new world.

unfortunately this file currently needs to support revolting ogsfx code
as well - please forgive

*/

#define PI 3.14159265

#if OGSFX

#if !HIDE_OGSFX_UNIFORMS
// uniform parametres
#endif

#if !HIDE_OGSFX_STREAMS
attribute fragmentInput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;

};

attribute fragmentOutput {
    vec4 colourOut : COLOR0;
};
#endif


#else // not ogsfx, only beautiful glsl

#version 330
// inputs
in vec3 WorldNormal;
in vec3 WorldEyeVec;

//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools

// main shader function
void main()
{
    vec4 test;
    test = vec4(1.0, 0.5, 1.0, 255);
    colourOut = test;

}
#endif
