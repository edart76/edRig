
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

    float rayStep = testRayStep;
    vec3 ro, rayDir; // rayOrigin, rayDirection

    // worldspace position of original hit
    vec4 worldOrigin = ( (gObjToWorld) * vec4(posOut, 1.0) );

    //worldOrigin = inverse(gObjToWorld) * ( (gObjToWorld) * vec4(posOut, 1.0) );
    //worldOrigin = vec4(posOut, 1.0);

    mat3 objOrient = mat3(gObjToWorld); // extract upper 3x3 matrix
    mat3 viewWorldOrient = mat3(gViewToWorld);
    mat3 viewOrient = mat3(gView);

    // worldspace direction of ray, from camera to worldOrigin
    vec4 focalView = vec4(0.0, 0.0, 0.0, focalLength);
    vec3 worldRayDir = normalize( worldOrigin.xyz - ( (gViewToWorld) * focalView ).xyz );

    //worldRayDir = normalize( worldOrigin.xyz - ( nverse(transpose(gObjToWorld)) * (gViewToWorld) * focalView).xyz );

    // focalLengths other than 1 give strange results at close range
    // I'm sorry that I don't understand the reason

    // usually we want
    //rayDir = normalize( (inverse((gObjToWorld)) * vec4(worldRayDir, 0.0)));
    rayDir = normalize(worldRayDir);
    //rayDir = normalize( transpose(objOrient) * worldRayDir);

    //worldOrigin = (transpose(gObjToWorld) * worldOrigin);


    ro = worldOrigin.xyz;

    //ro = (gProjection * worldOrigin).xyz;
    //ro = posOut;

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

    vec3 worldObjOrigin = (((gObjToWorld)) * vec4(0, 0, 0, 1)).xyz;


    // raytracing loop
    // starting position
    colour = vec3(0.01);
    vec3 t = worldOrigin.xyz - worldObjOrigin;
    t = inverse(objOrient) * t;
    rayDir = inverse(objOrient) * rayDir;
    for( i; i < nRaySteps; i++){

        if(alpha > 1.0){
            break;
        }

        t = t + normalize(rayDir) * rayStep;

        // get local ray position
        //vec3 rayLocalPos = t - worldObjOrigin;

        vec3 rayPos = t / globalScale;

        if(length(rayPos) > 1.0){
            continue;
        }

        // get ray position in relation to slice textures
        // find nearest slice

        // remap local pos from -1 1 to 1 0
        rayPos = (rayPos + vec3(1.0)) / 2.0;


        int sliceIndex = int( rayPos.y * nSlices );

        // local position in slice
        vec2 localPos = (rayPos.xz - vec2(1));
        localPos = rayPos.xz;



        vec2 samplePos = localTileCoordsToGlobal( localPos, sliceIndex, nSlicesRow);

        // check if ray is beyond cage
        if( !inRange(samplePos.x, 0.0, 1.0) || !inRange(samplePos.y, 0.0, 1.0)){
            continue;
        }

        // sample next tile to interpolate
        vec2 nextSamplePos = localTileCoordsToGlobal( localPos, sliceIndex + 1, nSlicesRow);

        vec4 sampleResult = texture2D(PrintVolumeSampler, samplePos);
        vec4 nextSampleResult = texture2D(PrintVolumeSampler, nextSamplePos);

        float sampleValue = mix(sampleResult.x, nextSampleResult.x, fract(rayPos.y * nSlices) );
        sampleValue = sampleResult.x;

        //colour.x += sampleResult.x * 0.01;

        if(sampleValue < isovalue)
        //if( length(t) < 0.5)
        {
            //alpha = 1.0;
            //alpha += 0.5 - abs(sampleResult.x);
            colour *= 1.1;
            alpha += 0.1;
            //break;
        }

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
