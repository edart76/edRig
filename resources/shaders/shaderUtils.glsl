// misc functions for glsl

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

// wholesale raid of inigo quilez' resources

// cubic pulse
float isolate( float centre, float radius, float x){
    x = abs( x - centre );
    if( x > radius ) return 0.0;
    x /= radius;
    return 1.0 - x * x * (3.0 - 2.0 * x);
}
