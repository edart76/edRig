
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

uniform float testRayStep;
uniform float focalLength; // camera focal length
uniform float pixelSize; // size of pixel (small)
uniform float darkSpace; // ratio of dark bordering around pixel
uniform float fadeDistance; // distance at which pattern appears
uniform float fadeEnd; // ratio of fadeDistance at which fade is complete

//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// ray settings
#define MAX_RAY_STEPS 16


vec4 getPixelColour(vec2 uv){
    // retrieve colour for this pixel
    vec4 pixelColour;

    // get local origin of pixel
    vec2 origin = vec2(pixelSize) * trunc( uv / pixelSize );
    // get local normalised position of pixel
    vec2 p = (uv - origin) / pixelSize;

    // sample at bottom left to ensure block colour across entire pixel
    pixelColour = vec4( texture2D( ScreenImageSampler, origin, 1.0 ) );

    // split into colours
    int r = rectangle(p, vec2(0.0), vec2(0.33, 1.0));
    int g = rectangle(p, vec2(0.33, 0.0), vec2(0.66, 1.0));
    int b = rectangle(p, vec2(0.66, 0.0), vec2(1, 1.0));

    // multiply by mask
    pixelColour = pixelColour * vec4(r, g, b, 1.0);

    // pixel borders
    pixelColour *= step( (mod(UVout.x, pixelSize) / pixelSize), darkSpace);
    pixelColour *= step( (mod(UVout.y, pixelSize) / pixelSize), darkSpace * 1.2);

    return pixelColour;
}


// main shader function
void main()
{
    vec3 colour = vec3(0.0, 0.0, 0.0);
    float alpha = 1.0;

    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);
    // set z component for ray origin - this should be drawn
    // from view matrix to align with main camera
    float rayZ = -4.0;



    // find ray info
    vec3 ro = vec3( screenUV.xy, rayZ);
    vec3 rayDir = normalize(rayDirFromUv( screenUV, focalLength ));
    // mult to worldspace
    rayDir = vec4( inverse( gWorldViewProjection ) * normalize(vec4(rayDir, 1.0))).xyz; // almost works



    // get weight of pixel pattern fade
    vec4 eyePos = inverse(gView)[3];
    float pixelWeight = smoothstep( fadeDistance, fadeDistance * fadeEnd, distance(posOut, eyePos.xyz) );

    colour = vec3( texture2D( ScreenImageSampler, UVout, 1.0 ) );

    // only run this if effect is active
    vec4 pixelColour = getPixelColour( UVout);

    colour = mix(colour, pixelColour.xyz, pixelWeight);



    // final output
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
