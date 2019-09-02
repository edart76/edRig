

/* we shouldn't need to define vertex transformations,
but in case we do
also need to do the magic peace dance to get this to work in maya
*/


#if !HIDE_OGSFX_UNIFORMS

#if OGSFX

// transform object vertices to world-space:
uniform mat4 gWorldXf : World < string UIWidget="None"; >;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf : WorldInverseTranspose < string UIWidget="None"; >;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWvpXf : WorldViewProjection < string UIWidget="None"; >;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewIXf : ViewInverse < string UIWidget="None"; >;

// test calibration attriutes for iris and corneal heights
uniform float cornealHeightCalibration = 0.2;
uniform float irisDepthCalibration = 0.1;



#else

#version 330
// transform object vertices to world-space:
uniform mat4 gWorldXf;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWvpXf;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewIXf;

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
};

/* data passed from vertex shader to pixel shader */
attribute vertexOutput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;

};

#else // OGSFX

in vec3 Position;
in vec2 UV;
in vec3 Normal;


out vec3 WorldNormal;
out vec3 WorldEyeVec;
out vec4 ObjPos;
out vec4 DCol; // lighting term, not used here
out vec2 UVout; // uv space coords

#endif
#endif

#if !HIDE_OGSFX_CODE // can we actually run the thing?

void main()
{
    vec3 Nw = normalize((gWorldITXf * vec4(Normal,0.0)).xyz);
    WorldNormal = Nw;
    DCol = vec4(0.5, 0.5, 0.5, 1);
    vec4 Po = vec4(Position.xyz,1); // local space position
    vec3 Pw = (gWorldXf*Po).xyz; // world space position

    WorldEyeVec = normalize(gViewIXf[3].xyz - Pw);
    vec4 hpos = gWvpXf * Po;
    vec4 calibPos = hpos + ((Nw * cornealHeightCalibration), 0.0);
    //vec4 calibPos = hpos;
    //ObjPos = vec4(UV.y, UV.x, Po.zw);
    ObjPos = calibPos; //
    gl_Position = calibPos; // final vertex position
    UVout = UV;
}

#endif
