/* act of desperation to derive screen coordinates reliably
on any hardware, in any environment, using the view matrix
*/

#if OGSFX

#if !HIDE_OGSFX_UNIFORMS

#endif

#if !HIDE_OGSFX_STREAMS


attribute screenUVInput {
//    vec3 WorldNormal    : TEXCOORD1;
//    vec3 WorldEyeVec    : TEXCOORD2;
//    vec4 ObjPos    : TEXCOORD3;
//    //vec3 UvEyeVec : TEXCOORD4;
//
//    vec4 DCol : COLOR0;
//    vec2 UVout : COLOR1;
//    vec4 corneaInfo : COLOR2;
//    vec3 refractOut : COLOR3;
//    vec3 binormalOut: COLOR4;
//    vec3 UvEyeVec : COLOR5;
};

attribute screenUVOutput {
    vec4 colourOut : COLOR0;
};

#endif


#else // not ogsfx, only beautiful glsl

#version 440

// gl-supplied
in vec4 gl_FragCoord;


//outputs
out vec4 colourOut;

#endif


#if !HIDE_OGSFX_CODE

// main shader function
void main()
{

    colourOut = normalize(vec4( gl_FragCoord ) );
    //colourOut = vec4( 1.0 );
}

#endif