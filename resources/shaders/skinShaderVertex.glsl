

/*
basic vertex template
*/


#if !HIDE_OGSFX_UNIFORMS

#if OGSFX

// look upon the menagerie of parametres we can have
// transform object vertices to world-space:
uniform mat4 gWorld : World < string UIWidget="None"; >;
uniform mat4 gObjToWorld : World < string UIWidget="None"; >;

// view matrix:
uniform mat4 gView : View < string UIWidget="None"; >;
/* evidently rotation is applied before translation -
gView gives translate values in the frame of the camera's orientation
*/

uniform mat4 gWorldView : WorldView < string UIWidget="None"; >;


// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf : WorldInverseTranspose < string UIWidget="None"; >;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWorldViewProjection : WorldViewProjection < string UIWidget="None"; >;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewToWorld : ViewInverse < string UIWidget="None"; >;


// projection matrix:
uniform mat4 gProjection : Projection < string UIWidget="None"; >;

// !!!!!!!!!!!!!
uniform vec2 iResolution : ViewportPixelSize < string UIWidget="None"; >;

uniform vec2 currentTime : Time < string UIWidget="None"; >;

uniform int currentFrame : Frame < string UIWidget="None"; >;



#else

// transform object vertices to world-space:
uniform mat4 gWorld;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWorldViewProjection;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewToWorld;


uniform vec2 iResolution;

#endif // OGSFX

#endif // HIDE_OGSFX_UNIFORMS



#if !HIDE_OGSFX_STREAMS

//**********
//	Input stream handling:

#if OGSFX

/************* DATA STRUCTS **************/

/* data from application vertex buffer */
attribute appdata {
    vec3 Position    : POSITION;
    vec2 UV        : TEXCOORD0;
    vec3 Normal    : NORMAL;
    vec3 Tangent   : TANGENT;
    vec3 Binormal  : BINORMAL;
};

/* data passed from vertex shader to pixel shader */
attribute vertexOutput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;
    vec3 posOut: COLOR4;
    vec3 normalOut   : COLOR5;

};

#else // not OGSFX

in vec3 Position;
in vec2 UV;
in vec3 Normal;
in vec3 Tangent;
in vec3 Binormal;

uniform vec3 baseDiffuse;

uniform int nStrokes;
uniform int nGridCells;
uniform int strokeSize;

out vec3 WorldNormal;
out vec3 WorldEyeVec;
out vec4 ObjPos;
out vec3 UvEyeVec;
out vec4 DCol; // lighting term, not used here
out vec2 UVout; // uv space coords

out vec3 posOut;
out vec3 normalOut;

#endif
#endif

#if !HIDE_OGSFX_CODE // can we actually run the thing?

// main body of code

// !!!!!!!!!!!!!
layout(r16f, binding=4) uniform image1D test;
// imageLoad(image img, int/ivec2/ivec3 P)
// imageStore(image img, int/ivec2/ivec3 P, gvec4 sample)

buffer StrokeBuffer{
    int i;
} bufferInstance;

// !!!!!!!!!!!!!!

#include "shaderUtils.glsl"


// stroke stuff

#define MAX_POSSIBLE_STROKES 1000

struct Stroke {
    int id;
    vec2 pos;
    float rotation;
};

// define array as theoretical max size
Stroke strokes[ MAX_POSSIBLE_STROKES ];


vec2 strokeRect = vec2(1.0); // vary later maybe
float gridRatio = 1.0 / 1.0; // height by width
float normalizedRatio = gridRatio * (strokeRect.y / strokeRect.x);

float gridHeight = sqrt(nStrokes * normalizedRatio);
float gridWidth = sqrt(nStrokes / normalizedRatio);


vec2 getStrokePosition(int id){
    // can't call rng for every stroke for every vertex
    // instead we use regular spacing with random distortion later
    return vec2( mod(float(id), gridWidth), floor(float(id) / gridHeight));
}
/* consider instead sampling blue noise texture at even intervals,
then using sampled values positions
*/



void main()
{
    // strokes
    if(nStrokes > MAX_POSSIBLE_STROKES){
        //#error
    }

    for(int i=0; i < nStrokes; i++){
        vec2 pos = getStrokePosition(i);
        strokes[i].pos = pos;
        vec2 dPos = abs(UV - pos);

        if( (dPos.x > strokeSize * 2) || (dPos.y > strokeSize * 2)){
            // stroke cannot affect vertex
            continue;
        }

        strokes[i].id = i;

        Stroke test = strokes[i];

    }


    // transform normal, binormal and tangent to world
    vec3 worldBinormal = normalize( (gWorldITXf * vec4(Binormal, 0.0)).xyz );
    vec3 worldTangent = normalize( (gWorldITXf * vec4(Tangent, 0.0)).xyz );
    vec3 WorldNormal = normalize((gWorldITXf * vec4(Normal,0.0)).xyz);
    WorldNormal = Normal;

    DCol = vec4(0.5, 0.5, 0.5, 1);

    vec3 newPos = Position;

    // calculate displacement
    float displacement = 0.0;
    vec4 Po = vec4(newPos.xyz + displacement, 1); // local space position
    vec4 hpos = gWorldViewProjection * Po;


    // tangent matrix to find surface-space view
    // T B N matrix

    mat3 tangentToObjectMat = mat3(
        worldTangent.x, worldBinormal.y, WorldNormal.z,
        worldTangent.x, worldBinormal.y, WorldNormal.z,
        worldTangent.x, worldBinormal.y, WorldNormal.z
    );

     //local version
    mat3 localMat = mat3(
        Tangent.x, Binormal.x, Normal.x,
        Tangent.y, Binormal.y, Normal.y,
        Tangent.z, Binormal.z, Normal.z    );


    mat3 objectToTangentMat = transpose( tangentToObjectMat );

//    // outputs
    vec3 Pw = (gWorld * hpos).xyz; // world space position
    WorldEyeVec = normalize(gViewToWorld[3].xyz - Pw);


    normalOut = Normal;
    posOut = newPos;

    ObjPos = vec4( newPos, 0.0 );
    gl_Position = hpos; // final vertex position
    UVout = UV;
}

#endif
 /* notes

this is going to be a bit mad

due to strokes being oriented, scaled, moved etc based on flow map and vertex attributes,
I don't see an elegant way to find their inverse transform, to shade directly -
this means a brute force scattering and search approach.

I don't see a way to precompute the strokes entirely (maybe it's possible with a
multipass, with first pass geometry shader emitting 1 vertex per stroke or something);
thus, strokes must be done within the vertex shader

ONLY BASE POSITIONS are computed for all strokes NS, for all vertices NV, only enough
to find grid membership. From then, cull strokes and do full computation on only those
within locality of vertex, writing back to strokes[] array.

There will still be a very, very great deal of redundant work, but it's the best I can
think of at this time.


*/
