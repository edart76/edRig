
/* main core for WePresent eye shader - using various maps
realised from geometry and colour, we will ensoul each inhabitant
of our new world.

unfortunately this file currently needs to support revolting ogsfx code
as well - please forgive

*/

#if OGSFX

#if !HIDE_OGSFX_UNIFORMS
// uniform parametres

// various colour maps


#endif

#if !HIDE_OGSFX_STREAMS
attribute fragmentInput {
    vec3 WorldNormal    : TEXCOORD1;
    vec3 WorldEyeVec    : TEXCOORD2;
    vec4 ObjPos    : TEXCOORD3;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;
    vec4 corneaInfo : COLOR2;


};

attribute fragmentOutput {
    vec4 colourOut : COLOR0;
};
#endif


#else // not ogsfx, only beautiful glsl

#version 330
// inputs
in vec3 WorldNormal;
in vec3 WorldEyeVec;

//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools

// main shader function
void main()
{

    // unpack cornea parametres
    float cornealHeight = corneaInfo.x;
    float irisWidth = corneaInfo.y;

    vec2 UV = UVout;

    // reconstruct iris info
    float uvDist = length( vec2( 0.5 - UV.x, 0.5 - UV.y) );
    float irisParam = max(irisWidth - uvDist, 0);




    // debug colours
    float irisBool = step(0.01, irisParam);
    float pupilBaseBool = step(uvDist, pupilBaseWidth);
    float pupilDilationBool = step(uvDist, pupilBaseWidth + pupilDilation);

    // final output
    vec4 debugOut = vec4(pupilDilationBool, irisBool, pupilBaseBool, 1);
    debugOut = debugOut * float(debugColours);
    vec4 mainColour = vec4(0.0, irisBool, 0.0, 1);
    mainColour = mainColour * 1.0 - float(debugColours);
    colourOut = mainColour + debugOut;

}
#endif

/* notes
at the centre of the eye, the pupil should be black for now -
the base material extending as far as the iris width is pupil
however, in future some blade runner mirror eyes would be sweet
within this material in high light, trace back into the eyeball

*/
