
/*
main body of slicer shader
*/

//#include <GL/glew.h>
//#include <GL/glut.h>
// nope

#if OGSFX

#if !HIDE_OGSFX_UNIFORMS

#endif

#if !HIDE_OGSFX_STREAMS
attribute fragmentInput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;
    //vec3 UvEyeVec : TEXCOORD4;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;
    vec4 corneaInfo : COLOR2;
    vec3 refractOut : COLOR3;
    vec3 posOut: COLOR4;
    vec3 normalOut : COLOR5;
};

attribute fragmentOutput {
    vec4 colourOut : COLOR0;
};
#endif


#else // not ogsfx, only beautiful glsl

#version 440

// inputs
in vec3 WorldNormal;
in vec3 WorldEyeVec;
in vec4 DCol;
in vec2 UVout;
in vec3 posOut;
in vec3 normalOut;

// gl-supplied
in vec4 gl_FragCoord;

//uniform float testRayStep;
uniform float focalLength;


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// ray settings
#define MAX_RAY_STEPS 16


// main shader function
void main()
{
    vec3 colour = vec3(0.0, 0.0, 0.0);
    float alpha = 1.0;

    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);
    //float focalLength = 10.0;
    // set z component for ray origin - this should be drawn
    // from view matrix to align with main camera
    float rayZ = -4.0;
    //rayZ = focalLength;


    // find ray info
    vec3 ro = vec3( screenUV.xy, rayZ);
    vec3 rayDir = normalize(rayDirFromUv( screenUV, focalLength ));
    // mult to worldspace
    rayDir = vec4( inverse( gWorldViewProjection ) * normalize(vec4(rayDir, 1.0))).xyz; // almost works

    // final output
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
