

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



#else

//#version 330
// transform object vertices to world-space:
uniform mat4 gWorldXf;

// transform object normals, tangents, & binormals to world-space:
uniform mat4 gWorldITXf;

// transform object vertices to view space and project them in perspective:
uniform mat4 gWvpXf;

// provide tranform from "view" or "eye" coords back to world-space:
uniform mat4 gViewIXf;

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
    vec3 binormalOut: COLOR4;
    vec3 UvEyeVec   : COLOR5;

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
out vec3 refractOut;
out vec3 binormalOut;

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

    DCol = vec4(0.5, 0.5, 0.5, 1);


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

    vec4 Po = vec4(Position.xyz + corneaDisplacement, 1); // local space position

    vec4 hpos = gWvpXf * Po;


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
    vec3 Pw = (gWorldXf * hpos).xyz; // world space position
    WorldEyeVec = normalize(gViewIXf[3].xyz - Pw);

//
//    // compute refraction
    vec3 refractVec = refract( WorldEyeVec, WorldNormal, 1 / iorBase);
//
    //vec3 localEye = tangentToObjectMat * WorldEyeVec;
//
//
    vec3 tangentRefract = normalize(tangentToObjectMat * refractVec);
    tangentRefract = refractVec;




    // localise before refraction

    UvEyeVec = tangentToObjectMat * WorldEyeVec;


    ObjPos = vec4(UV.y, UV.x, hpos.zw);
    gl_Position = hpos; // final vertex position
    UVout = UV;
    corneaInfo = vec4(fullDsp, irisWidth, 0.0, 0.0);
    refractOut = tangentRefract;
    binormalOut = Binormal;
}

#endif
 /* notes
in future consider tessellating sclera around veins in sclera map -
derive the "vein map" from the blue channel of the normal sclera
*/
