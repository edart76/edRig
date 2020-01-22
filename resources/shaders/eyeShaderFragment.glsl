
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


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"

// known values
float limbalHeight = cos( irisWidth * PI * 0.5);
float pupilWidth = pupilBaseWidth + pupilDilation;


float irisHeight( float rad ){
    // defines depth of iris as function of radius
    // radius should be NORMALISED within iris
    // height is offset from base iris depth
    return -smoothstep(0.0, irisDepth, rad);
    //return -irisDepth;
    // simple linear for now
    // later sample iris height texture here
}

// set up sdf geometry, centred at origin
float map( in vec3 pos ){
    float d = 1e10;

    // sclera
    d = min( d, sphere( pos, vec3(0.0), 1.0) );

    //cornea
    d = d;
    return d;
}

vec3 pupilDilate( vec2 coord ){
    /* compresses a lookup coordinate on the iris
    according to pupil dilation
    also packs bool if the NEW coord falls within the pupil
    */
    vec3 result = vec3(0.0);

    vec2 centrePoint = vec2(0.5);
    vec2 polar = cartesianToPolar( coord, centrePoint);
//
    // remap main uv coord into iris-centric map
    float irisRadius = max(fit( polar.x, 0.0, irisWidth,
        -pupilDilation, 0.5), 0) ;

    // prevent radius from exceeding 0.5 with soft limit
    irisRadius = ( irisRadius < 0.25 ) ? irisRadius : softClamp( irisRadius, 0.0, 0.48);


    // find initial uvs for iris colour lookup
    vec2 irisPolar = vec2(irisRadius, polar.y);
    vec2 irisCoord = polarToCartesian(irisPolar.x, irisPolar.y,
        centrePoint);

    // check if point falls on pupil
    float pupilWeight = step(pupilWidth, polar.x);
    // unsure if this is the right place

    result = vec3( irisCoord.xy, pupilWeight);
    return result;

}


/*
four possible treatments of the pixel:
 - sclera
 - limbal ring
 - iris
 - pupil

discount pupil for now as iris is enough

pupil dilation affects everything - function to retrieve distorted
iris coords from normalised?

*/

// ray settings
#define MAX_RAY_STEPS 64


vec4 getScleraColour( vec3 pos, vec3 rayOrigin, vec3 rayDir,
        vec2 scleraCoord, vec2 scleraPolar ){

    vec4 col = vec4( texture2D(ScleraDiffuseSampler, scleraCoord, 1.0));
    return col;

}

vec4 getIrisColour( vec3 pos, vec3 rayDir, vec3 normal,
        vec2 irisCoord, vec2 irisPolar, float ior){
    // this is all still in full eye-space

    // move pos to be in iris-space

    vec4 col = vec4( 0.0, 0.0, 0.0, 1.0 );

    // cast rays into cornea
    vec3 rayOrigin = pos;

    //normal = vec3( 0.5, 0.5, 1.0);
    normal = normalize(pos);

    // compare to centre of iris
    vec3 centre = vec3( 0.0, limbalHeight, 0.0 );

    // REFRACT
    vec3 refractDir = rayDir;
    rayDir = (refract( normalize(rayDir), (normal), ior));
    // dumb refract alternative, inspired by gravity lensing
    // rayDir = normalize(rayDir + normal * ior);

    float rayStep = 0.01;
    float t = rayStep;
    int i = 0;
    for( i; i < MAX_RAY_STEPS; i++ )
    {
        pos = rayOrigin + t * rayDir; // ray

        // we don't use a full SDF here, just Y-comparison
        float radius = length( pos.xz );
        float normRad = radius / irisWidth;
        normRad = radius; // literally no difference yet
        float height = pos.y - ( limbalHeight + irisHeight( normRad ) );
        //height = pos.y - limbalHeight + irisDepth;
        // NB IF THIS SHOULD BE IRIS-NORMALISED OR NOT

        // check exit conditions
        if ( height < rayStep )
        {
            // look up colours
            // check magnitude of intersection, and nudge ray back or forwards
            pos += rayDir * height;

            vec2 rayLookup = pos.xz;

            // remap coordinates centred at iris to 0 - 1 uv space
            vec2 coord = fit( vec4( rayLookup, 0.0, 0.0),
                -1.0, 1.0, 0.0, 1.0 ).xy;

            vec3 pupilInfo = pupilDilate( coord );
            coord = pupilInfo.xy;


            col = vec4( texture2D( IrisDiffuseSampler, coord, 1.0 ) );
            break;
        }

        // adaptive sampling
        t = t + height * 0.9;
        // we don't do it, so as not to distort participation, diffusion etc
        t = t + rayStep;
    }

    //col = vec4( texture2D( IrisDiffuseSampler, rayOrigin.xz, 0.5 ) );

    return col;
}

vec4 getPupilColour( vec3 pos, vec3 rayOrigin, vec3 rayDir ){

    vec4 col = vec4( 0.0, 0.0, 0.0, 1.0);
    return col;
}

vec4 getLimbalColour(){

    vec4 col = vec4( 17, 40, 50, 256) / 256.0;
    return col;
}


// main shader function
void main()
{
    vec4 colour = vec4(0.0, 0.0, 0.0, 0.0);

    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);
    float focalLength = 10000.0;
    // set z component for ray origin - this should be drawn
    // from view matrix to align with main camera
    float rayZ = -4.0;

    // find ray info
    vec3 ro = vec3( screenUV.xy, rayZ);
    vec3 rayDir = normalize(rayDirFromUv( screenUV, focalLength ));
    // mult to worldspace
    rayDir = vec4( inverse( gWorldViewProjection )* normalize(vec4(rayDir, 1.0))).xyz; // almost works
    // -----NB------
    // getting too close to eye gives weird results without refraction,
    // I am likely missing a trick here.

    // unpack vertex info
    float cornealDsp = corneaInfo.x;
    vec2 UV = UVout;
    vec3 pos = ObjPos.xyz;

    // uvs in polar space
    vec2 centrePoint = vec2( 0.5, 0.5 );
    vec2 polar = cartesianToPolar( UV, centrePoint );
    float radius = polar.x;
    float angle = polar.y;

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

    float limbalBool = smoothstep(0.1, 1.0, limbalParam);

    // initialise output colour
    vec4 mainColour = vec4(0,0,0,0.5);

    float pupilWidth = pupilBaseWidth + pupilDilation;

    // remap main uv coord into iris-centric map
    float irisRadius = max(fit(radius, 0.0, irisWidth,
        -pupilDilation, 0.5), 0) ;


    // find initial uvs for iris colour lookup
    vec2 irisPolar = vec2(irisRadius, polar.y);
    vec2 irisCoord = polarToCartesian(irisPolar.x, irisPolar.y,
        centrePoint);

    // find pupil switches
    float pupilBaseBool = step(irisRadius, pupilBaseWidth);
    float pupilDilationBool = step(irisRadius, pupilBaseWidth);

    vec2 scleraUV = UV;
    vec2 scleraPolar = polar;


    // ------- execute separate colour functions -------

    // sclera
    if ( irisBool <= 0.001 ){
        vec4 scleraColour = getScleraColour(
        pos, ro, rayDir, scleraUV, scleraPolar
        );
        mainColour = scleraColour;
    }

    // iris
    if ( irisBool > 0.0 ){
        vec4 irisColour = getIrisColour(
            pos, rayDir, normalOut, irisCoord, irisPolar,
            iorBase
        );
        mainColour = mix(mainColour, irisColour, irisBool);
    }

    // pupil
    if ( pupilDilationBool > 0.0 ){
        vec4 pupilColour = getPupilColour(
            pos, ro, rayDir
        );
        //mainColour = mix( mainColour, pupilColour, pupilDilationBool);
    }

    // limbal ring
    if (limbalRad > 0.0 ){
        vec4 limbalColour = getLimbalColour();
        mainColour = mix( mainColour, limbalColour, limbalRad);
    }



    // debug colours
    // check iris height is detected properly
    float yHeight = float( limbalHeight > ObjPos.y );
    vec4 debugOut = vec4(yHeight, irisBool, limbalBool, 1.0);
    //debugOut = vec4(pupilDilationBool, irisBool, 0, 0);
    debugOut = debugOut * float(debugColours);
    // mix debug
    mainColour = mix(mainColour, debugOut, debugColours);
//
//
    colourOut = mainColour;

/* ray stuff
    // initial raycast
    float t = 1.0;
    float exit = 10.0;
    vec3 pos = vec3(0.0);
    int i = 0;
    for( i; i < MAX_RAY_STEPS; i++ )
    {
        pos = ro + t * rayDir; // ray
        float d = map( pos ); // test ray position against scene sdf
        // check exit conditions
        //if ( abs(d) < 0.01 || t > exit )
        if ( abs(d) < 0.01  )
        {
            break;
        }
        t += d;
    }

    //if ( t < exit )
    if ( i < MAX_RAY_STEPS )
    {
        colour = vec4( 1.0, 0.0, 0.0, 1.0 );
    }

    else {
        colour = vec4( 0.0, 0.0, 0.0, 1.0);
    }


    colourOut = colour;
    //colourOut = vec4( 0.0, 0.0, 0.0, 0.0);
*/


}
#endif

/* notes
at the centre of the eye, the pupil should be black for now -
the base material extending as far as the iris width is pupil
however, in future some blade runner mirror eyes would be sweet
within this material in high light, trace back into the eyeball

*/


