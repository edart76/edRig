
/*
main body of slicer shader
*/

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
uniform float isovalue;
uniform vec3 volumeOffset;

// volume slice texture variables
uniform int nSlices;
uniform int nRaySteps;


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// ray settings
#define MAX_RAY_STEPS 16


float mapIsovalue(float sampledValue){
    // maps a sampled value in 0, 1 to -1, 1
    // with specified isovalue as midpoint
    if( sampledValue < isovalue ){
        return fit(sampledValue, 0.0, isovalue, -1.0, 0.0);
    }
    else{
        return fit(sampledValue, isovalue, 1.0, 0.0, 1.0);
    }
}

// main shader function
void main()
{
    vec3 colour = vec3(0.0, 0.0, 0.0);
    float alpha = 1.0;
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);

    // initialise ray params
    /* as this is not global ray tracing, rays need only start at the
    point that they first intersect the container geometry volume
    this means we must reconstruct ray direction at point of impact,
    and cannot rely on screenspace coordinates for it
    */

    float rayStep = testRayStep * globalScale;
    vec3 ro, rayDir; // rayOrigin, rayDirection
    vec4 focalView = vec4(0.0, 0.0, 0.0, focalLength);

    // object orient matrix
    mat3 objOrient = mat3(gObjToWorld); // extract upper 3x3 matrix

    // worldspace position of original hit
    vec4 worldOrigin = ( (gObjToWorld) * vec4(posOut, 1.0) );

    // worldspace direction of ray, from camera to worldOrigin
    vec3 worldRayDir = normalize( worldOrigin.xyz - ( (gViewToWorld) * focalView ).xyz );

    // worldspace object centre
    vec3 worldObjOrigin = (((gObjToWorld)) * vec4(0, 0, 0, 1)).xyz;

    // usually we want
    rayDir = inverse(objOrient) * worldRayDir;
    ro = inverse(objOrient) * (worldOrigin.xyz - worldObjOrigin) - volumeOffset;


    /* the above system limits content to within the 3d confines of the volume proxy
    could be very entertaining to reconstruct a screenspace approach, to display content
    anywhere between the camera and the volume cage
    */


    // transform everything to layer frame
    vec3 aimUp = vec3(0.0, 0.0, 1.0);
    mat3 layerAim = inverse(aimMatrix( layerDir, aimUp, true));

    // transform positions - X axis is direction of layers
    vec3 layerPos = layerAim * posOut;


    int i = 0;
    ivec2 sliceRes = textureSize(PrintVolumeSampler, 0);
    // lod0 gives base resolution
    int nSlicesRow = int(sqrt(nSlices));

    alpha = 0.0;


    colour = vec3(0.01);

    // raytracing loop
    // starting position
    vec3 t = ro;

    for( i; i < nRaySteps; i++){

        if(alpha > 1.0){
            break;
        }


        // get local ray position
        //vec3 rayLocalPos = t - worldObjOrigin;

        vec3 rayPos = t / globalScale;

        // if( length(rayPos) > 2){
        //     // allow rays outside volume only on hemisphere facing camera
        //     if( dot(rayPos, rayDir) > 0.0){
        //         continue;
        //     }
        //
        // }



        // get ray position in relation to slice textures
        // find nearest slice

        // remap local pos from -1 1 to 1 0
        rayPos = (rayPos + vec3(1.0)) / 2.0;


        int sliceIndex = int( (rayPos.z) * nSlices );


        // local position in slice
        vec2 localPos = vec2(1.0) - rayPos.xy;
        localPos.x = 1.0 - localPos.x;
        //localPos = rayPos.xy;

        if( !inRange(localPos.x, 0.0, 1.0) || !inRange(localPos.y, 0.0, 1.0)){
            continue;
        }

        vec2 samplePos = localTileCoordsToGlobal( localPos, sliceIndex, nSlicesRow);

        // sample next tile to interpolate
        vec2 posZSamplePos = localTileCoordsToGlobal( localPos, sliceIndex + 1, nSlicesRow);

        // first determine intersection
        vec4 sampleResult = texture2D(PrintVolumeSampler, samplePos);
        vec4 posZSampleResult = texture2D(PrintVolumeSampler, posZSamplePos);

        float sampleMix = fract(rayPos.y / float(nSlices));
        float sampleValue = mix(sampleResult.x, posZSampleResult.x, 0.5 );

        sampleValue = smoothMinCubic(sampleResult.x, posZSampleResult.x, 0.2);
        sampleValue = smoothMin(sampleResult.x, posZSampleResult.x, 0.2);


        if(sampleValue < isovalue)
        {
            //alpha += 0.5;
            //alpha += 0.5 - abs(sampleResult.x);
            //colour +=0.1;
            alpha += 0.1;
            //alpha = 1.01;
            //break;
        }

        float stepLength = rayStep * abs(sampleValue);



        t = t + normalize(rayDir) * stepLength;


        //alpha += sampleResult.x;

        // if no intersection, ray passes through
        //alpha = 0.0;
        //colour.xyz = vec3(0.0);

    }

    //alpha = 1.0;

    // debug
    screenUV = screenUV * 75;
    //colour.x = float( printMat4( screenUV, gObjToWorld, 2));
    //colour.x = float( printFloat( gl_FragCoord.xy / 5 , 0.01, 2));

    // final output
    //alpha +=0.1;
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
