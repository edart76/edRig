
/* main core for WePresent eye shader - using various maps
realised from geometry and colour, we will ensoul each inhabitant
of our new world.

unfortunately this file currently needs to support revolting ogsfx code
as well - please forgive

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
    vec3 binormalOut: COLOR4;
    vec3 UvEyeVec : COLOR5;
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
in vec3 refractOut;
in vec3 binormalOut;

// gl-supplied
in vec4 gl_FragCoord;


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"

// try to get viewport dimensions

//vec4 viewport = glGetIntegerv( GL_VIEWPORT );
//vec4 viewport = glGet( 1 );


// known values
float limbalHeight = cos( irisWidth );

float irisHeight( float rad ){
    // defines depth of iris as function of radius
    // radius should be NORMALISED within iris
    return (1 - rad) * irisDepth;
    // simple linear for now
}


// main shader function
void main()
{

    mat4 test = gObjToWorld;

//    // unpack vertex info
    float cornealDsp = corneaInfo.x;
    //float irisWidth = corneaInfo.y;

    vec2 UV = UVout;

    // uvs in polar space
    vec2 centrePoint = vec2( 0.5, 0.5 );
    vec2 polar = cartesianToPolar( UV, centrePoint );
    float radius = polar.x;
    float angle = polar.y;
    /* linear UV interpolation gives some distortion, but not enough to matter on dense mesh
    */

    // reconstruct iris info
    float uvDist = radius;
    float eyeParam = ( irisWidth - uvDist ) / irisWidth;
    float irisParam = max(eyeParam, 0);
    // reconstruct limbal info
    float limbalParam = clamp( fit( eyeParam, -limbalWidth, limbalWidth, 0.0, 1.0),
    0.0, 1.0 );
    float limbalRad = 1.0 - smoothstep( 0, limbalWidth, abs( eyeParam ) );
    // limbalParam is linear, limbalRad is smooth and meant for aesthetic use

    // pixel location switches
    float irisBool = step(0.01, irisParam);
    float pupilBaseBool = step(uvDist, pupilBaseWidth);

    float pupilDilationBool = step(uvDist, pupilBaseWidth + pupilDilation);
    float limbalBool = step(0.1, limbalParam);
    limbalBool = limbalParam;
    limbalBool = limbalRad;
//    float limbalBool = step( irisWidth - limbalWidth, eyeParam) *
//        step( eyeParam, irisWidth + limbalWidth);




    // initialise output colour
    vec4 mainColour = vec4(0,0,0,0.5);

    // if pixel lies on sclera
    vec4 scleraColour = vec4( texture2D(ScleraSampler, UV, 1.0));

    // mix in pupil colour
    vec4 pupilColour = vec4( 1, 0.0, 0.0, 0.0);
    mainColour = mix(scleraColour, pupilColour, pupilDilationBool);
    mainColour = scleraColour;
    // mainColour = pupilColour;
    float pupilWidth = pupilBaseWidth + pupilDilation;


    // mix in iris colour
    // remap main uv coord into iris-centric map
//    float irisRadius = max(fit(radius, 0.0, irisWidth,
//        -pupilWidth, 0.5), 0) ;
    float irisRadius = max(fit(radius, 0.0, irisWidth,
        -0, 0.5), 0) ;


    // find initial uvs for iris colour lookup
    vec2 irisPolar = vec2(irisRadius, polar.y);
    // one thing at a time, pupil stuff is broken for now
    //irisPolar = vec2(radius, polar.y);
    //irisPolar = vec2(irisRadius, uvView);
    vec2 irisCoord = polarToCartesian(irisPolar.x, irisPolar.y,
        centrePoint);
    //irisCoord += uvView;




    vec4 irisColour = vec4( texture2D(IrisDiffuseSampler,
        irisCoord, 0.5));

    mainColour = mix(mainColour, irisColour, irisBool);

    mainColour *= 1 - irisBool * 0.8;

    // blend in limbal colour
    vec4 limbalColour = vec4( 17, 40, 50, 256) / 256.0;
    // later make limbal colour proper vector parametre
    mainColour = mix( mainColour, limbalColour, limbalRad);


    // debug colours
    //vec4 debugOut = vec4(pupilDilationBool, irisBool, pupilBaseBool, 0);
    vec4 debugOut = vec4(pupilDilationBool, irisBool, limbalBool, 1.0);
    //debugOut = vec4(pupilDilationBool, irisBool, 0, 0);
    debugOut = debugOut * float(debugColours);

    // mix contributions
    mainColour = mix(mainColour, debugOut, debugColours);


    colourOut = mainColour;
    vec4 normalisedCoord = normalize( gl_FragCoord );

    vec2 screenUv = normalize( WorldEyeVec.xy );
    colourOut = normalize( test[3] );

    colourOut = vec4( screenUv, 0.0,  1.0 );

    colourOut = abs(colourOut);

    //colourOut = vec4( normalize(WorldEyeVec), 1.0 );


}
#endif

/* notes
at the centre of the eye, the pupil should be black for now -
the base material extending as far as the iris width is pupil
however, in future some blade runner mirror eyes would be sweet
within this material in high light, trace back into the eyeball

*/


