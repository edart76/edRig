// misc functions for glsl

#ifndef SHADER_UTILS
#define SHADER_UTILS 1
#endif
// preprocessor include guard doesn't seem to work properly


#define EPS 0.00001
#define PI 3.14159265
#define TAU 6.2831853

float fit( float value, float min1, float max1, float min2, float max2){
    // input as percentage of range1
    float perc = (value - min1) / (max1 - min1);
    // Do the same operation backwards with min2 and max2
    float result = perc * (max2 - min2) + min2;
    return result;
}

vec2 cartesianToPolar( vec2 xy, vec2 centrePoint){
    //
    vec2 x = xy - centrePoint;
    float radius = length(x);
    float angle = atan(x.y, x.x);
    return vec2( radius, angle );
}

vec2 polarToCartesian( float radius, float angle, vec2 centrePoint){
    float x = radius * cos( angle ) + centrePoint.x;
    float y = radius * sin( angle ) + centrePoint.y;
    return vec2(x, y);
}

// don't know how to define gentype functions
vec3 projectInto( vec3 vector, vec3 space){
    return vec3( ( dot( vector, space) /
        exp2( length( space ) ) ) * space );
}

vec2 uvFromFragCoordNormalised( vec2 fragCoord, vec2 iResolution){
    // returns uvs from -1 t 1 in both axes
    vec2 uv = (-1.0 + 2.0*fragCoord.xy / iResolution.xy) *
		vec2(iResolution.x/iResolution.y, 1.0);
    return uv;
}

vec2 uvFromFragCoord( vec2 fragCoord, vec2 iResolution){
    // uvs from 0 to 1, (0,0) being in top left
    return fragCoord.xy / iResolution.xy;
}



// wholesale raid of inigo quilez' resources
// praise be to gpu jesus

// cubic pulse
float isolate( float centre, float radius, float x){
    x = abs( x - centre );
    if( x > radius ) return 0.0;
    x /= radius;
    return 1.0 - x * x * (3.0 - 2.0 * x);
}


// SDF stuff
// some of these will be centred at origin, more complex may not
float sphere( vec3 point, vec3 centre, float rad){
    return length( point - centre ) - rad;
}

// raytracing stuff
vec3 rayDirFromPos( vec2 uv ){
    // finds direction of ray from normalised screen coords
    // assuming normal frustum projection
    return normalize( vec3( uv, 1.0 ) ); }

vec3 rayDirFromPos( vec2 uv, float focalLength ){
    return normalize( vec3( uv, focalLength ) );
    // focal length may weight ray direction differently
}



//#endif