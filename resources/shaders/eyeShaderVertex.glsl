

/* we shouldn't need to define vertex transformations,
but in case we do
also need to do the magic peace dance to get this to work in maya
*/


#if !HIDE_OGSFX_UNIFORMS

#if OGSFX

// look upon the menagerie of parametres we can have
// transform object vertices to world-space:
uniform mat4 gObjToWorld : World < string UIWidget="None"; >;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf : WorldInverseTranspose < string UIWidget="None"; >;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWorldViewProjection : WorldViewProjection < string UIWidget="None"; >;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewToWorld : ViewInverse < string UIWidget="None"; >;

// view matrix:
uniform mat4 gView : View < string UIWidget="None"; >;

// projection matrix:
uniform mat4 gProjection : Projection < string UIWidget="None"; >;

// !!!!!!!!!!!!!
uniform vec2 iResolution : ViewportPixelSize < string UIWidget="None"; >;

uniform vec2 currentTime : Time < string UIWidget="None"; >;

uniform int currentFrame : Frame < string UIWidget="None"; >;



#else

//#version 440
// transform object vertices to world-space:
uniform mat4 gObjToWorld;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWorldViewProjection;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewToWorld;

// !!!!!!!!!
uniform vec2 iResolution;

uniform float iorRange;

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
    //vec3 UvEyeVec : TEXCOORD4;

    vec4 DCol : COLOR0;
    vec2 UVout : COLOR1;
    vec4 corneaInfo : COLOR2;
    vec3 refractOut : COLOR3;
    vec3 posOut: COLOR4;
    vec3 normalOut   : COLOR5;

};

#else // not OGSFX

in vec3 Position;
in vec2 UV;
in vec3 Normal;
in vec3 Tangent;
in vec3 Binormal;



out vec3 WorldNormal;
out vec3 WorldEyeVec;
out vec4 ObjPos;
out vec3 UvEyeVec;
out vec4 DCol; // lighting term, not used here
out vec2 UVout; // uv space coords
out vec4 corneaInfo;
out vec3 posOut;
out vec3 normalOut;

#endif
#endif

#if !HIDE_OGSFX_CODE // can we actually run the thing?

// main body of code

// if uv coord is more than 0.5 radius from centre,
// it's the back of the eye

#include "shaderUtils.glsl"

void main()
{
    // transform normal, binormal and tangent to world
    vec3 worldBinormal = normalize( (gWorldITXf * vec4(Binormal, 0.0)).xyz );
    vec3 worldTangent = normalize( (gWorldITXf * vec4(Tangent, 0.0)).xyz );
    vec3 WorldNormal = normalize((gWorldITXf * vec4(Normal,0.0)).xyz);
    WorldNormal = Normal;

    DCol = vec4(0.5, 0.5, 0.5, 1);

    vec3 newPos = normalize(Position);


    // we assume starting from spherical mesh - create corneal bulge
    float uvDist = length( vec2( 0.5 - UV.x, 0.5 - UV.y) );
    float eyeParam = ( irisWidth - uvDist ) / irisWidth;
    // 1 is centre of pupil, 0 is edge of iris

    // limbal param
    float limbalParam = clamp( fit( eyeParam, -limbalWidth, limbalWidth, 0.0, 1.0) / 1.3,
        0.0, 1.0 );
    // 1 is inner edge AND EVERYTHING WITHIN IT, 0 is outer AND BEYOND, 0.5 is midpoint


    // cap off eyeParam to form irisParam
    float irisParam = clamp( eyeParam, 0.0, 1.0);

    // naive displacement for cornea gives sharp point - soften tip values
    float tipSoftenFactor = pow( smoothstep( 0.8, 1.0, irisParam ), 2.0) ;
    float tipSoften = cornealHeight * mix( 1.0, 0.9, tipSoftenFactor );

    float displaceParam = irisParam ;
    float mainDsp = tipSoften * displaceParam;

    // soften limbal ring with a quadratic ramp
    float limbalMaxDsp = cornealHeight * 0.2; // tune as needed, 0.2 feels good
    float limbalDsp = limbalMaxDsp * pow(limbalParam, 2);

    float fullDsp = max(limbalDsp, mainDsp);
    // fullDsp = mainDsp;


    vec3 corneaDisplacement = (Normal * fullDsp );
    // naive fix is only valid for certain profiles
    // need a solution that is aware of irisWidth and height

    vec4 Po = vec4(newPos.xyz + corneaDisplacement, 1); // local space position

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

    //tangentToObjectMat = localMat;

    mat3 objectToTangentMat = inverse( tangentToObjectMat );
    objectToTangentMat = transpose( tangentToObjectMat );

//    // outputs
    vec3 Pw = (gObjToWorld * hpos).xyz; // world space position
    WorldEyeVec = normalize(gViewToWorld[3].xyz - Pw);

    vec4 testPos = vec4(Pw, 0.0);
    testPos = vec4(normalize(newPos), iorRange);

    vec4 viewPos = inverse(gWorldViewProjection) * testPos; // very cool but not useful
    viewPos = gWorldViewProjection * testPos; // works but gives oval distortion

//    vec4 viewPos = vec4( testPos.x / -testPos.z, testPos.y / -testPos.z, testPos.z, iorRange);
//    viewPos =  viewPos * transpose( inverse(gViewToWorld) );

    WorldEyeVec = viewPos.xyz;

//
//    // compute refraction
    vec3 refractVec = refract( WorldEyeVec, WorldNormal, 1 / iorBase);
//
    //vec3 localEye = tangentToObjectMat * WorldEyeVec;
//
//
    vec3 tangentRefract = normalize(tangentToObjectMat * refractVec);
    tangentRefract = refractVec;

    normalOut = Normal;
    posOut = newPos;


    //ObjPos = vec4(UV.y, UV.x, hpos.zw);
    ObjPos = vec4( newPos, 0.0 );
    gl_Position = hpos; // final vertex position
    //gl_Position = vec4(-WorldEyeVec.xyz, 0.5); // final vertex position
    UVout = UV;
    corneaInfo = vec4(fullDsp, irisWidth, 0.0, 0.0);
    refractOut = tangentRefract;
}

#endif
 /* notes
in future consider tessellating sclera around veins in sclera map -
derive the "vein map" from the blue channel of the normal sclera

currently screenpos is distorted by resolution - which is good, but
we need the inverse of it,


*/
