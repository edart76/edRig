
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
    vec3 UvEyeVec : TEXCOORD4;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;
    vec4 corneaInfo : COLOR2;


};

attribute fragmentOutput {
    vec4 colourOut : COLOR0;
};
#endif


#else // not ogsfx, only beautiful glsl

//#version 330
// inputs
in vec3 WorldNormal;
in vec3 WorldEyeVec;
in vec4 DCol;
in vec2 UVout;
in vec4 corneaInfo;

//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// main shader function
void main()
{

//    // unpack cornea parametres
//    float cornealHeight = corneaInfo.x;
//    float irisWidth = corneaInfo.y;
    // useless, all shaders access uniforms, remove when complete

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
    float irisParam = max(irisWidth - uvDist, 0);
    // how deep is point on limbal ring?
    float limbalParam = 0.0;

    // pixel location switches
    float irisBool = step(0.01, irisParam);
    float pupilBaseBool = step(uvDist, pupilBaseWidth);
    float limbalBool = 0.0;
    float pupilDilationBool = step(uvDist, pupilBaseWidth + pupilDilation);




    // initialise output colour
    vec4 mainColour = vec4(0,0,0,1);

    // if pixel lies on sclera
    vec4 scleraColour = vec4( texture2D(ScleraSampler, UV, 1.0));

    // mix in pupil colour
    vec4 pupilColour = vec4( 1, 0.0, 0.0, 1.0);
    mainColour = mix(scleraColour, pupilColour, pupilDilationBool);
    // mainColour = pupilColour;
    float pupilWidth = pupilBaseWidth + pupilDilation;


    // mix in iris colour
    // remap main uv coord into iris-centric map
    float irisRadius = max(fit(radius, 0.0, irisWidth,
        -pupilWidth, 0.5), 0) ;


    // refraction setup
    // first need view vector transformed to uv space
    // project view vector into normal
    vec3 normalView = projectInto( WorldEyeVec, WorldNormal );
    // remove "vertical" component to get eye vec in normal (uv) plane
    vec2 uvView = vec2( normalize( vec2( normalView.y, normalView.x )));

    // simple linear conical height profile for now
    float baseHeight = cornealHeight * irisRadius;
    // find magnitude of deflection based on normal
    float refractionMag = dot(WorldEyeVec, WorldNormal) * iorBase;
    // ior treatment is likely too simple here but whatever
    float refractionDistance = refractionMag * baseHeight;
    // shrug
    uvView *= refractionDistance;

    // find final uvs for iris colour lookup
    vec2 irisPolar = vec2(irisRadius, polar.y);
    vec2 irisCoord = polarToCartesian(irisPolar.x, irisPolar.y,
        centrePoint);
    irisCoord += uvView;
    vec4 irisColour = vec4( texture2D(IrisDiffuseSampler,
        irisCoord, 1.0));
    // vec4 irisColour = vec4( texture2D(IrisDiffuseSampler,
    //     UV, 1.0));
    mainColour = mix(mainColour, irisColour, irisBool);


    // pupil colour sits below iris, blended in based on iris opacity




    // debug colours
    vec4 debugOut = vec4(pupilDilationBool, irisBool, pupilBaseBool, 0);
    debugOut = debugOut * float(debugColours);

    // mix contributions
    mainColour = mix(mainColour, debugOut, debugColours);

    colourOut = mainColour;


}
#endif

/* notes
at the centre of the eye, the pupil should be black for now -
the base material extending as far as the iris width is pupil
however, in future some blade runner mirror eyes would be sweet
within this material in high light, trace back into the eyeball

*/
