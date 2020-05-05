
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
in vec4 corneaInfo;
in vec3 UvEyeVec;
in vec3 posOut;
in vec3 normalOut;

// gl-supplied
in vec4 gl_FragCoord;

uniform float globalScale;
uniform vec3 baseDiffuse;
uniform vec3 layerDir;
uniform float layerHeight;
uniform float focalLength;
uniform float testRayStep;


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

    //colour.xyz = baseDiffuse;

    //layerDir = normalize(layerDir);

    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);
    //float focalLength = 10.0;
    // set z component for ray origin - this should be drawn
    // from view matrix to align with main camera
    float rayZ = -4.0;
    //rayZ = focalLength;

    // find required ray resolution from viewDir dot layerDir
    // high angles likely impact layers quicker than shallow
    float rayStep = globalScale / layerHeight;
    rayStep = layerHeight / globalScale;
    rayStep = testRayStep;

    // find ray info
    vec3 ro = vec3( screenUV.xy, rayZ);
    vec3 rayDir = normalize(rayDirFromUv( screenUV, focalLength ));
    // mult to worldspace
    rayDir = vec4( inverse( gWorldViewProjection ) * normalize(vec4(rayDir, 1.0))).xyz; // almost works

    // transform everything to layer frame
    vec3 aimUp = vec3(0.0, 0.0, 1.0);
    mat3 layerAim = inverse(aimMatrix( layerDir, aimUp, true));

    // transform positions - X axis is direction of layers
    vec3 layerPos = layerAim * posOut;

    float layerDisplacement = mod(layerPos.x, layerHeight);
    float layerCeil = ceil(layerPos.x / layerHeight);
    float layerFloor = floor(layerPos.x / layerHeight);

    // try symmetric distance?
    float layerDspSymmetric = abs(layerHeight / 2 - mod(layerPos.x, layerHeight)) / layerHeight * 2;

    // displacement mapped to 0-1
    float layerDspNormalized = layerDisplacement / layerHeight;

    // ray tracing
    // project ray direction to layerdir to find space to work with
    rayDir = inverse(layerAim) * rayDir;

    float rayHeight = layerDisplacement;
    rayStep = rayStep / rayHeight;
    float rayHeightTrunc;
    float rayHeightNorm = rayHeight / layerHeight;

    int i = 0;
    vec3 t = layerPos;
    for( i; i < MAX_RAY_STEPS; i++){

        colour.x = colour.x + 1.0 / MAX_RAY_STEPS;

        t = t + rayDir * rayStep;
        rayHeight = t.x / layerHeight;


        if(rayHeight > layerCeil || rayHeight < layerFloor - layerHeight / 2.0){
        //if(rayHeight < 0.0){
        // if(rayHeightNorm < 0.0 || rayHeightNorm > 1.0){
        //if( distance(t, vec3(0,0,0)) < 1.5){ // test debug sphere
            // colour.z = 1.0;
            // colour.y = 1.0;
            alpha = 1.0;

            break;
        }

        // if no intersection, ray passes through
        alpha = 0.0;
        colour.xyz = vec3(0.0);

    }


    //colour *= layerDspNormalized;
    //colour *= layerDspSymmetric;
    // colour *= rayHeightNorm;
    //colour *= rayDotLayer;

    // final output
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
