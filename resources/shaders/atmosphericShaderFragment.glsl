
/*
main body of atmos shader

shader has multiple layers :
 - stars (immobile, base reference frame)
 - solar system (sun, inner planets)
 - atmosphere (clouds and stuff)

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

#version 430

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
uniform float focalLength;

uniform float atmosphereHeight;


// star settings
uniform float starBrightness;
uniform float starCutoff;
uniform float starBrightness;



// ray settings
uniform float globalScale;
uniform float rayStep;


uniform vec3 viewPos;
uniform vec3 viewOrientX;
uniform vec3 viewOrientY;
uniform vec3 viewOrientZ;


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// ray settings
#define MAX_RAY_STEPS 32

// define stars
// vec4( theta, omega, radius, apparent magnitude)
// angles are given in degrees, and hours / seconds are ignored for now
// we assume all visible stars share roughly similar colour
vec4 stars[] = {
    vec4(89.0),
    vec4(1.0)

};
// gonna take the easy way out and use a texture for now


float getVerticalCompression(float y){
    // returns angluar remap from initial Y value of ray
    // depth info is separate
    float altitude = viewPos.y / atmosphereHeight;
    y = altitude;
    return y;

}

float map( vec3 p){
    // basic sphere at origin
    vec3 origin = vec3(0, -0.5, 0);
    return length(p - origin) - 1.0;
}


vec3 getStarfieldColour(vec3 sphereCoord){

    // wobble coordinates for twinkle effects
    sphereCoord.xy = sphereCoord.xy + simplexNoise2d(sphereCoord.xy)*starTwinkle;


    // process starfield image to be crisp as possible
    vec4 imageInfo = texture2D(StarImageSampler, sphereCoord.xy);
    imageInfo = imageInfo * imageInfo * imageInfo ;
    imageInfo = imageInfo * smoothstep(0, starCutoff, imageInfo.x);
    imageInfo *= starBrightness;

    return imageInfo.xyz;
}



// main shader function
void main()
{
    vec3 colour = vec3(0.0, 0.0, 0.0);
    float alpha = 0.0;

    /* atmosphere depth can vary from 0 to 1.0, with 0.5 being radius from centre
    at rest, apex should be 0.5; base should be 0;
    at max altitude, apex 1.0; base 0.5;
    */

    vec3 sphereCoord = vec3(1.0, UVout);
    sphereCoord = vec3(UVout, 1.0);

    mat4 viewMat = mat4(
        vec4(viewOrientX, 0.0),
        vec4(viewOrientY, 0.0),
        vec4(viewOrientZ, 0.0),
        vec4(viewPos, 1.0)
        );
    mat3 viewOrient = transpose(mat3(viewMat));

    //sphereCoordCartesian = posOut;
    vec3 initialCartesian = normalize(posOut);

    // treat compression of vertical coords due to altitude
    // initialCartesian.y = initialCartesian.y + altitude / 2;

    vec3 cartesianOrient = viewOrient * initialCartesian;

    float altitude = viewPos.y / atmosphereHeight;
    //cartesianOrient.y = cartesianOrient.y * altitude;
    //cartesianOrient.y = altitude;
    //cartesianOrient.y = getVerticalCompression(cartesianOrient.y);
    //cartesianOrient.y = atmosphereHeight;


    vec3 sphereCoordOrient = cartesianToSpherical(normalize(cartesianOrient));

    //sphereCoordOrient.y = sin(cartesianOrient.y);
    //sphereCoordOrient.y = (cartesianOrient.y);

    sphereCoord = sphereCoordOrient;




    float rayStep = rayStep;
    vec3 ro, rayDir; // rayOrigin, rayDirection
    vec4 focalView = vec4(0.0, 0.0, 0.0, focalLength);

    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);


    // object orient matrix
    mat3 objOrient = mat3( transpose(viewMat) * gObjToWorld); // extract upper 3x3 matrix

    // worldspace position of original hit
    vec4 worldOrigin =((gObjToWorld) * vec4(posOut, 1.0) );
    //worldOrigin =((gObjToWorld) * vec4(cartesianOrient, 1.0) );

    // worldspace direction of ray, from camera to worldOrigin
    vec3 worldRayDir = normalize( worldOrigin.xyz - ( (gViewToWorld) * focalView ).xyz );
    //worldRayDir = worldRayDir * inverse(viewOrient);

    // worldspace object centre
    vec3 worldObjOrigin = (((gObjToWorld)) * vec4(0, 0, 0, 1)).xyz;

    rayDir = viewOrient * normalize(worldRayDir);

    //rayDir = cartesianOrient;
    rayDir = normalize(rayDir);

    ro = viewOrient * posOut;
    ro.y += altitude;

    vec3 t = ro;
    float d;
    float prevD = 100000.0;

    for( int i = 0; i < MAX_RAY_STEPS; i++){
        t = t + rayDir * rayStep;
        d = map( t );
        if( d < 0.1){
            colour.y = 1.0;
            alpha = 1.0;
            break;
        }
        if(d < 0.15){
            colour.y = 0.5;
            alpha = 1.0;
            break;
        }
        if (d > prevD){ // moving out of atmosphere
            break;

        }
        prevD = d;
        rayStep = min(abs(d), 0.99);
        //colour.z += 0.01;

    }


    // sample starfield
    if(alpha < 1.0){
        // layers should blend additively atop each other
        vec3 starCoords = sphereCoord;
        starCoords = vec3(1.0) - cartesianToSpherical(rayDir);
        colour = getStarfieldColour(starCoords) + colour * alpha;
    }



    // debugColours
    float r = mix(0.0, 1.0, sphereCoord.x);
    float b = mix(0.0, 1.0, sphereCoord.y);

    b = 0;
    r*=0.01;
    colour = (mix(colour, vec3(r, 0, b), debugColours));


    // final output
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
