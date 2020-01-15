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

// printing text courtesy of P_Malin
// actually courtesy of Fabrice Neyret
int printDigit(vec2 p, float n) {
    // digit bottom left at 0.0, 1.0
    int i=int(p.y), b=int(exp2(floor(30.-p.x-n*3.)));
    i = ( p.x<0.||p.x>3.? 0:
    i==5? 972980223: i==4? 690407533: i==3? 704642687: i==2? 696556137:i==1? 972881535: 0 )/b;
 	return i-i/2*2;
}
// print a decimal point
int printDot(vec2 p ){
    return int( ( -0.1 < p.x && p.x < 0.6) && (1.0 < p.y && p.y < 2.0 ) );
}
// print entire float number to target decimal places
int printFloat( vec2 p, float n, int places, float width ){
    // compress coordinates
    int boundPlaces = max(places, 1);
    //float width = p.x / float(boundPlaces);
    // separate integer and float components
    int i = int(trunc(n));
    float f = fract( n );
    // print integer
    int col = printDigit( p, float(i) );

    // add dot if with decimals
    p.x -= width ;
    col = max( col, int(places > 0) * printDot(p) );
    int place = 1;
    p.x -= width * 0.3;
    for( place; place <= places; place++){

        // shuffle the first digit of f into integers
        f *= 10.0;
        i = int(trunc( f ));
        f = fract( f );
        col = max( col, printDigit( p, float(i) ) );
        p.x -= width;
    }
    return col;
}


//
//// don't know how to define gentype functions
//vec3 projectInto( vec3 vector, vec3 space){
//    return vec3( ( dot( vector, space) /
//        exp2( length( space ) ) ) * space );
//}




// screenspace coords
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
vec3 rayDirFromUv( vec2 uv ){
    // finds direction of ray from normalised screen coords
    // assuming normal frustum projection
    return normalize( vec3( uv, 1.0 ) ); }

vec3 rayDirFromUv( vec2 uv, float focalLength ){
    return normalize( vec3( uv, focalLength ) );
    // focal length may weight ray direction differently
}

// can you do inheritance in glsl?
// well yes but actually  y e s
float f( in vec3 pos);
// function f is overall general function for scalar fields, override if you want

float map( in vec3 pos);

vec3 calcNormal( in vec3 pos )
// central "tetrahedral" differences
{
    const float h = 0.0001; // tiny dPos
    const vec2 k = vec2(1,-1);
    return normalize( k.xyy * map( pos + k.xyy*h ) +
                      k.yyx * map( pos + k.yyx*h ) +
                      k.yxy * map( pos + k.yxy*h ) +
                      k.xxx * map( pos + k.xxx*h ) );
    // evaluate field at vertices of tetrahedron
}
//#endif