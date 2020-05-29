
/*

skin fragment

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


// inputs
in vec3 WorldNormal;
in vec3 WorldEyeVec;
in vec4 DCol;
in vec2 UVout;
in vec3 posOut;
in vec3 normalOut;

// gl-supplied
in vec4 gl_FragCoord;

uniform int nStrokes;
uniform int nGridCells;

uniform float strokeSize;
uniform float strokeRotation;
uniform float strokeWidth;

uniform float flowWeight;

uniform float jitterPosition;
uniform float jitterScale;
uniform float jitterRotation;



uniform float minStrokeScale;

// shape settings
uniform float strokeTipWeight;

uniform float testRayStep;
uniform float focalLength;


//outputs
out vec4 colourOut;

#endif

#if !HIDE_OGSFX_CODE
// shader tools
#include "shaderUtils.glsl"


// ray settings
#define MAX_RAY_STEPS 16


/* we assume for now that every grid cell can host only 1 stroke point
this will likely not be enough, so define a maximum of 4 strokes that can originate
in any cell, and block out that much space in the strokeBuffer storage
*/

int cellIndexFromCoord(vec2 originCoord){
    return int( originCoord.x + originCoord.y * nGridCells );
}

vec2 getStrokeGridPosition(vec2 seedVec){
    // return the stroke position for a given cell
    vec2 jitterPoint = (randomVec(seedVec) * 2) - vec2(1.0) ;
    vec2 point = vec2(0.5) + jitterPoint * jitterPosition;
    return point;
}

float strokeSDF(vec2 p, vec2 seedVec){
    // test position against stroke sdf
    // don't know where we check the flow map

    float rand = randSin(seedVec);

    // sample flow map
    vec4 flowInfo = texture2D( SkinFlowSampler, seedVec / (nGridCells), 1.0);
    vec2 flowDir = normalize(flowInfo.xy);

    float flowAngle = dot(vec2(1.0, 0.0), flowDir) + dot(vec2(0.0, 1.0), flowDir);

    mat2 flowMat = mat2(flowDir.x, flowDir.y,
        flowDir.y, flowDir.x );


    float theta = mix(strokeRotation + flowAngle * flowWeight / 2,
        rand * (strokeRotation + flowAngle * flowWeight),
        jitterRotation);
    mat2 rot = rotate2d(theta);

    mat2 rotMat = (matrixCompMult(flowMat * flowWeight, mat2(1.0)));

    rotMat = flowMat;
    rotMat = rot;
    p *= rotMat;

    // compress to ellipse
    p.x *= strokeWidth;

    float scaledStroke = mix(strokeSize,
        fit(rand * strokeSize, 0, 1, minStrokeScale, 1),
        jitterScale);

    // vertical ramp in [0:1]
    float rampY = clamp( scaledStroke / ((p.y + 1) / 2.0) ,
        0.0, 1.0);

    rampY = clamp(
        pow( abs(( p.y + scaledStroke) / scaledStroke*0.7), 2),
        0.0, 1.0);

    //rampY = clamp(p.y, -1.0, 1.0);

    //p.y -=  strokeTipWeight * smoothstep(0.0, strokeTipWeight, abs(p.y*p.y));
    // weight towards front
    p.y = -mix(p.y, p.y * (1.0 - strokeTipWeight), rampY);


    float d = (length(p) - scaledStroke);
    d = - step(d, 0.0);
    return d * rampY;
}


// main shader function
void main()
{
    vec3 colour = vec3(0.0, 0.0, 0.0);
    float alpha = 1.0;

    // strokes
    // find positin in grid
    vec2 scaledUv = UVout * nGridCells;
    vec2 originCoord = floor(scaledUv);
    vec2 localCoord = fract(scaledUv);

    // originCoord is consistent across all fragments in cell

    int index = cellIndexFromCoord(originCoord);
    //Stroke origStroke;
    //origStroke = strokes[ index ];


    // test voronoi system:
    vec2 point = getStrokeGridPosition(originCoord);
    // vec2 jitterPoint = randomVec(originCoord);
    // vec2 point = vec2(0.5) + jitterPoint * jitterPosition;
    //point = randSinVec(originCoord);
    //float d = length( point - localCoord);

    vec2 col = vec2(0.0);


    // get and test stroke data for this cell
    //float sdf = strokeSDF( localCoord - point, originCoord );

    float d = 10000.0;
    float sdf = 10000.0;

    // run over 3x3 cell area
    int cellRange = 1;
    for( int dX = -cellRange; dX <= cellRange; dX++){
        for( int dY = -cellRange; dY <= cellRange; dY++){
            // I don't think this is separable
            vec2 dCell = vec2(float(dX), float(dY));
            vec2 neighbourPoint = getStrokeGridPosition( dCell + originCoord );
            //vec2 neighbourPoint = randomVec( dCell + originCoord);
            //neighbourPoint = randSinVec( dCell + originCoord );
            vec2 relativePoint = vec2(dCell + neighbourPoint) - localCoord;
            float newD = length(relativePoint);

            vec2 neighbourColour = randomVec( dCell + originCoord);

            // col = mix(col, neighbourPoint, step(d, newD));
            //col = mix(col, neighbourColour, int(newD < d));

            d = min(d, newD);

            relativePoint = localCoord - vec2(dCell + neighbourPoint);

            float newSdf = strokeSDF( relativePoint, dCell + originCoord);
            sdf = min( sdf, newSdf);

        }
    }

    col.y = step(sdf, 0.0) * abs(sdf);
    // maximum range that a stroke point can affect is
    // +- (jitterDistance + strokeSize)

    colour = col.xyx;

    //colour = texture2D( SkinFlowSampler, UVout, 1.0).xyz;


    //colour.yz = mix(vec2(1.0), vec2(0.0), d);


    // initialise ray params
    vec2 screenUV = uvFromFragCoordNormalised(gl_FragCoord.xy, iResolution);
    //float focalLength = 10.0;
    // set z component for ray origin - this should be drawn
    // from view matrix to align with main camera
    float rayZ = -4.0;
    //rayZ = focalLength;


    // find ray info
    vec3 ro = vec3( screenUV.xy, rayZ);
    vec3 rayDir = normalize(rayDirFromUv( screenUV, focalLength ));
    // mult to worldspace
    rayDir = vec4( inverse( gWorldViewProjection ) * normalize(vec4(rayDir, 1.0))).xyz; // almost works

    // final output
    colourOut = vec4(colour.xyz, alpha);


}
#endif

/* notes


*/
