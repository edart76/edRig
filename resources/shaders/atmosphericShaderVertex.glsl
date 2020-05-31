

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

#version 430
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

#include "shaderUtils.glsl"

void main()
{
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
    // set normal to direct eye vector for flat shading
    //normalOut = -WorldEyeVec;

    posOut = newPos;

    ObjPos = vec4( newPos, 0.0 );
    gl_Position = hpos; // final vertex position
    UVout = UV;
}

#endif
 /* notes


*/
