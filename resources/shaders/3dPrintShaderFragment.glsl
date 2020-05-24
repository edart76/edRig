
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
uniform float tetDifferencesRange;

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

// image data
ivec2 sliceRes = textureSize(PrintVolumeSampler, 0);
// lod0 gives base resolution
int nSlicesRow = int(sqrt(nSlices));

struct VolumeSample
{
    /* data describing the sdf at a certain point */
    //vec3 pos;
    float value;
    vec3 normal;
};

vec2 samplePointFromPosition( vec3 rayPos){
    // convert 3d ray position to image coords
    int sliceIndex = int( (rayPos.z) * nSlices );
    // local position in slice
    vec2 localPos = vec2(1.0) - rayPos.xy;
    localPos.x = 1.0 - localPos.x;
    if( !inRange(localPos.x, 0.0, 1.0) || !inRange(localPos.y, 0.0, 1.0)){
        return vec2(-1.0); // outside of image
    }
    vec2 samplePos = localTileCoordsToGlobal( localPos, sliceIndex, nSlicesRow);
    return samplePos;
}

vec4 sampleVolumeSimple(vec3 rayPos){
    // less expensive way to sample scalar field value
    // no smoothing
    // use for secondary effects like depth
    vec2 samplePos = samplePointFromPosition(rayPos);
    return texture2D(PrintVolumeSampler, samplePos );
}


mat4 tet = tetrahedronVertices();


// ignore optimisation for now
VolumeSample sampleVolumeAtPosition(vec3 rayPos, vec3 rayDir){
    // sample volume at and around ray position, return VolumeSample struct
    VolumeSample output;

    // scale and orient tetrahedron vertices
    mat4 sampleTet = tet * tetDifferencesRange * 0.01;
    vec3 up = normalize(cross(rayDir, cross(rayPos, rayDir)));
    up = vec3(1.0, 0.0, 0.0);
    mat3 tetAim = aimZMatrix(rayDir, up, true);
    tetAim = aimMatrix(rayDir, up, true);
    mat4 tetTransform = mat4(tetAim );
    //tetTransform[3] = vec4(rayPos, 1.0);

    //sampleTet = sampleTet * tetTransform ;

    mat4 sampleResults;
    // load sampled values into matrix
    for( int i = 0; i < 4; i++){
        vec3 tetPoint = tetAim * sampleTet[i].xyz;
        //tetPoint = (tetAim) * sampleTet[i].xyz;
        tetPoint = sampleTet[i].xyz;
        sampleResults[i] = sampleVolumeSimple( tetPoint + rayPos);
    }

    // interpolate
    // linear for now, maybe try 3/3/1 subdivision later on
    vec4 interpolated = (sampleResults[0] + sampleResults[1] + sampleResults[2] + sampleResults[3]) / 4;

    // calculate normal with iquilez' tetrahedal differences
    const vec2 k = vec2(1,-1);
    vec3 normal = normalize(
        k.xyy * sampleResults[0].xyz +
        k.yyx * sampleResults[1].xyz +
        k.yxy * sampleResults[2].xyz +
        k.xxx * sampleResults[3].xyz ).zxy;

    // set results
    output.value = interpolated.x;
    output.normal = normal;

    return output;
}

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

    alpha = 0.0;


    colour = vec3(0.0);

    // raytracing loop
    // starting position
    vec3 t = ro;

    float depth = 0.0;
    float rayWeight = 0.0; // tracks total depth of ray

    for( i; i < nRaySteps; i++){

        if(alpha > 1.0){
            break;
        }

        vec3 rayPos = t / globalScale;

        // // remap local pos from -1 1 to 1 0
        rayPos = (rayPos + vec3(1.0)) / 2.0;

        vec2 localPos = samplePointFromPosition(rayPos);

        if( localPos.x == -1.0){ // position not valid
            continue;
        }

        // ignore optimisation for now
        VolumeSample raySample = sampleVolumeAtPosition(rayPos, rayDir);

        float sampleValue = raySample.value;


        if(sampleValue < isovalue)
        {
            //alpha += 0.5;
            //alpha += 0.5 - abs(sampleResult.x);
            //colour +=0.1;
            //alpha += 0.1;

            //colour.x = (dot(raySample.normal, rayDir));
            //colour.x = abs(dot(raySample.normal, vec3(0.0, 1.0, 0.0)));
            // break;

            rayWeight += abs(sampleValue - isovalue) * 3;
            //rayWeight += 0.21;

        }

        if(rayWeight > 1.0){
            alpha = 1.01;
            colour.x = depth * (( 1 + dot( raySample.normal, rayDir))/2);
            colour.x = (( 1 + dot( raySample.normal, rayDir))/2);
            break;
        }

        float stepLength = rayStep * (abs(sampleValue - isovalue) + 0.01);




        t = t + normalize(rayDir) * stepLength;
        depth += stepLength;


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
