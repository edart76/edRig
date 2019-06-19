#if !OGSFX
#version 330
#endif
/*********************************************************************NVMH3****
*******************************************************************************
$Revision: #1 $

This GLSL sample was converted from HLSL. Here are the original comments:

Copyright NVIDIA Corporation 2008
TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THIS SOFTWARE IS PROVIDED
*AS IS* AND NVIDIA AND ITS SUPPLIERS DISCLAIM ALL WARRANTIES, EITHER EXPRESS
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE.  appdata NO EVENT SHALL NVIDIA OR ITS SUPPLIERS
BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT, OR CONSEQUENTIAL DAMAGES
WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF BUSINESS PROFITS,
BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR ANY OTHER PECUNIARY
LOSS) ARISING OUT OF THE USE OF OR INABILITY TO USE THIS SOFTWARE, EVEN IF
NVIDIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

% Brick pattern, with controls, using texture-based patterning.
% The lighting here is PURELY lambert and from a directional source,
% 	so it's done in the vertex shader.

keywords: material pattern virtual_machine

$Date: 2008/07/21 $

keywords: OpenGL

To learn more about shading, shaders, and to bounce ideas off other shader
    authors and users, visit the NVIDIA Shader Library Forums at:

    http://developer.nvidia.com/forums/

*******************************************************************************
******************************************************************************/

/*****************************************************************/
/*** EFFECT-SPECIFIC CODE BEGINS HERE ****************************/
/*****************************************************************/

//**********
//	Uniform parameter handling:
//
//	The OGSFX specifications provides support for annotations and
//	semantics which are missing in the GLSL specifications. This
//	means that we need to handle two sets of uniforms, one with
//	semantics, for use in OGSFX, another without for when the shader
//	is loaded in raw GLSL. Programmers must remember to update both
//	sections when adding, removing, or editing shader uniforms.
//	
//	For another heavier (but less error prone) approach to uniform
//	parameter handling you can look into the Brix.glslf file.
//

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

/*** TWEAKABLES *********************************************/

// apps should expect this to be normalized
uniform vec3 gLamp0Dir : DIRECTION <
    string Object = "DirectionalLight0";
    string UIName =  "Lamp 0 Direction";
    string Space = "World";
> = {0.7f,-0.7f,-0.7f};

// Ambient Light
uniform vec3 gAmbiColor : AMBIENT <
	string Object = "AmbientLight0";
    string UIName =  "Ambient Light";
    string UIWidget = "Color";
> = {0.17f,0.17f,0.17f};

uniform float gBrickWidth : UNITSSCALE <
    string UNITS = "inches";
    string UIWidget = "slider";
    float UIMin = 0.0;
    float UIMax = 0.35;
    float UIStep = 0.001;
    string UIName = "Brick Width";
> = 0.3;

uniform float gBrickHeight : UNITSSCALE <
    string UNITS = "inches";
    string UIWidget = "slider";
    float UIMin = 0.0;
    float UIMax = 0.35;
    float UIStep = 0.001;
    string UIName = "Brick Height";
> = 0.12;

#else

// transform object vertices to world-space:
uniform mat4 gWorldXf;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWvpXf;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewIXf;

/*** TWEAKABLES *********************************************/

// apps should expect this to be normalized
uniform vec3 gLamp0Dir = vec3(0.7,-0.7,-0.7);

// Ambient Light
uniform vec3 gAmbiColor = vec3(0.17,0.17,0.17);

uniform float gBrickWidth = 0.3;

uniform float gBrickHeight = 0.12;

#endif // OGSFX

#endif // HIDE_OGSFX_UNIFORMS

#if !HIDE_OGSFX_STREAMS

//**********
//	Input stream handling:
//
//	The OGSFX specifications provides support for semantics which is
//	missing in the GLSL specifications. The syntax is sufficiently 
//	different that it becomes easier to simply have two sections
//	for OGSFX and GLSL
//

#if OGSFX

/************* DATA STRUCTS **************/

/* data from application vertex buffer */
attribute appdata {
    vec3 Position    : POSITION;
    vec2 UV        : TEXCOORD0;
    vec3 Normal    : NORMAL;
};

/* data passed from vertex shader to pixel shader */
attribute brixVertexOutput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;
    vec4 DCol : COLOR0;
};

#else

in vec3 Position;
in vec2 UV;
in vec3 Normal;


out vec3 WorldNormal;
out vec3 WorldEyeVec;
out vec4 ObjPos;
out vec4 DCol;

#endif
#endif

//**********
//	Code handling:
//
//	The OGSFX specifications requires code blocks to be defined
//	inside GLSLShader sections. This is handled by the master
//	Brix.ogsfx file, but could also be added here protected between
//	#if OGSFX preprocessor directives.
//

#if !HIDE_OGSFX_CODE

void main() 
{
    vec3 Nw = normalize((gWorldITXf * vec4(Normal,0.0)).xyz);
    WorldNormal = Nw;
    float lamb = clamp(dot(Nw,-gLamp0Dir),0.0,1.0);
    DCol = vec4((vec3(lamb) + gAmbiColor).rgb,1);
    vec4 Po = vec4(Position.xyz,1);
    vec3 Pw = (gWorldXf*Po).xyz;
    WorldEyeVec = normalize(gViewIXf[3].xyz - Pw);
    vec4 hpos = gWvpXf * Po;
    ObjPos = vec4(UV.y/gBrickWidth,UV.x/gBrickHeight,Po.zw);
    gl_Position = hpos;
}

#endif