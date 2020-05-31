// misc functions for glsl

#ifndef SHADER_UTILS
#define SHADER_UTILS 1
#endif
// preprocessor include guard doesn't seem to work properly

#include "matrixUtils.glsl"

#define EPS 0.00001
#define PI 3.14159265
#define TAU 6.2831853

// pure maths functions
float fit( float value, float oldMin, float oldMax, float newMin, float newMax){
    // input as percentage of range1
    float perc = (value - oldMin) / (oldMax - oldMin);
    // Do the same operation backwards with min2 and max2
    float result = perc * (newMax - newMin) + newMin;
    return result;
}

vec4 fit( vec4 v, float min1, float max1, float min2, float max2){
    vec4 result;
    for (int i=0; i < 4; i++){
        result[i] = fit( v[i], min1, max1, min2, max2);
    }
    return result;
}

bool inRange(float x, float low, float high){
    return ( (low < x) && (x < high));
}

// thank you mr jaybird
float smoothClamp(float x, float low, float b)
{
    float t = clamp(x, low, b);
    return t != x ? t : b + (low - b)/(1. + exp((b - low)*(2.*x - low - b)/((x - low)*(b - x))));
}

float softClamp(float x, float low, float b)
{ // smoother approach
 	float mid = (low + b)*0.5;
    return mid + smoothClamp((x - mid)*0.5, low - mid, b - mid);
}

// random hash function, as shown by Spatial on StackOverflow
uint hash( uint x ){
    x += ( x << 10u);
    x ^= ( x >> 6u);
    x += ( x << 3u);
    x ^= ( x >> 11u);
    x += ( x << 15u);
    return x;
}

// return unique hash value for vector
uint hash( uvec2 v ) { return hash( v.x ^ hash(v.y)                         ); }
uint hash( uvec3 v ) { return hash( v.x ^ hash(v.y) ^ hash(v.z)             ); }
uint hash( uvec4 v ) { return hash( v.x ^ hash(v.y) ^ hash(v.z) ^ hash(v.w) ); }

// return corresponding hash vector
uvec2 hashVec( uvec2 v ){
    uint x = hash( v );
    return uvec2(x, x ^ hash(v.y) ); }

float floatConstruct( uint m){
    const uint ieeeMantissa = 0x007FFFFFu; //binary32 ieee mantissa bitmask
    const uint ieeeOne =      0x3F800000u; // 1.0 in ieee binary32

    m &= ieeeMantissa; // keep only mantissa bits
    m |= ieeeOne;
    float f = uintBitsToFloat( m ); // returns range [1:2]
    return f - 1.0; // range [0:1]
}

// main rng functions
float random( float x ) { return floatConstruct(hash(floatBitsToUint(x))); }
float random( vec2  v ) { return floatConstruct(hash(floatBitsToUint(v))); }
float random( vec3  v ) { return floatConstruct(hash(floatBitsToUint(v))); }
float random( vec4  v ) { return floatConstruct(hash(floatBitsToUint(v))); }

vec2 randomVec( vec2 v){
    uvec2 uv = hashVec(floatBitsToUint(v));
    return vec2( floatConstruct(uv.x), floatConstruct(uv.y)); }


// weird option returning random int
int LFSR_rand(int n){
    n = (n << 13) ^ n;
    return (n * (n * n * 15731 + 789221) & 0x7fffffff);
}

// the basic rand function with sin
float randSin(vec2 seed){
    return fract(sin(dot(seed.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

vec2 randSinVec(vec2 seed){
    return vec2( randSin(seed), 0.5);
}

float logToBase( float x, float base ){
    // using change of base formula
    // logB(x) = logC(x) / logC(B)
    return log2(x) / log2(base);
}

vec2 cartesianToPolar( vec2 xy, vec2 centrePoint){
    // returns vec2( radius, angle )
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

vec3 cartesianToSpherical( vec3 p ){
    // assumes sphere centred at origin, pole aligned to Y axis
    // returns UVW parameterisation
    vec3 pN = normalize( - p);
    float u = 0.5 + ( atan( pN.z, pN.x ) / TAU);
    float v = 0.5 - ( asin( pN.y) / PI );
    float w = length( p );
    return vec3( u, v, w);
}

vec3 sphericalToCartesian( vec3 p){
    // sphere at origin, pole at y
    // expects theta, omega, r
    return vec3(
        sin(p.x) * cos(p.y),
        sin(p.x) * cos(p.y),
        cos(p.x) ) * p.z;
    }

mat2 rotate2d( float angle ){
    // actually had to look this up, never say I'm not a total fraud
    float amp = 2 * PI;
    return mat2( cos(angle*amp), -sin(angle*amp),
                 sin(angle*amp), cos(angle*amp) );
}

mat3 aimMatrix(vec3 aim, vec3 up, bool yIsUp){
    // creates matrix to align X to aim, and Y or Z to up
    vec3 normal = cross(aim, up);
    vec3 binormal = cross(aim, normal);
    return transpose( mat3(
        aim, normal, binormal));
}

mat3 aimZMatrix( vec3 aim, vec3 up, bool yIsUp){
    // same as above, but z is aim
    vec3 normal = cross(aim, up);
    vec3 binormal = cross(aim, normal);
    return transpose( mat3( binormal, normal, aim ));
}

// basic shapes
int rectangle( vec2 p, vec2 origin, vec2 size){
    return int(( origin.x < p.x && p.x < size.x) && ( origin.y < p.y && p.y < size.y));
}




// printing text courtesy of P_Malin
// actually courtesy of Fabrice Neyret
float baseWidth = 3.5;
float dotWidth = baseWidth * 0.3;
int printDigit(vec2 p, float n) {
    // digit bottom left at 0.0, 1.0
    // top right at 3.5, 6.0
    int i=int(p.y), b=int(exp2(floor(30.-p.x-n*3.)));
    i = ( p.x<0.||p.x>3.? 0:
    i==5? 972980223: i==4? 690407533: i==3? 704642687: i==2? 696556137:i==1? 972881535: 0 )/b;
 	return i-i/2*2; // what absolute lunatic finds this stuff
    // if you pass this things bigger than 1 digit, cool but useless things happen
}
// print a decimal point
int printDot(vec2 p ){
    return int( ( -0.1 < p.x && p.x < 0.6) && (1.0 < p.y && p.y < 2.0 ) );
}
// print horizontal hyphen
int printHyphen( vec2 p){
    return int( ( -0.1 < p.x && p.x < 1.5) && ( 2.5 < p.y && p.y < 3.5 ) );
}
// print entire float number to target precision places
int printFloat( vec2 p, float n, int places ){
    // compress coordinates
    int boundPlaces = max(places, 1);
    float width = baseWidth;
    int col = 0;

    // print dash if less than 0
    float dashOffset = 2.0;
    p.x += dashOffset;
    col = max(col, int(n < 0.0) * printHyphen(p));
    p.x -= dashOffset;

    // now set to positive
    n = abs(n);

    // separate integer and float components
    float f = fract(n);

    // find number of left digits from log10
    int leftDigits = int(floor(logToBase(n, 10.0)));
    // curtail integers to single digit
    float i = round(n);
    i = i / pow(10.0, (leftDigits + 1 ) );

    // print integers
    int iplace = 0;
    //for (place; place <= places; place++){
    for (iplace; iplace <= leftDigits; iplace++){
        i *= 10.0;
        int d = int( round( i ));
        i = fract( i );
        col = max( col, printDigit( p, d));
        p.x -= width;
    }

    col = max( col, int(places > 0) * printDot(p) );
    int place = 1;
    p.x -= dotWidth;
    for( place; place <= places; place++){

        // shuffle the first digit of f into integers
        f *= 10.0;
        i = trunc( f );
        f = fract( f );
        col = max( col, printDigit( p, i ) );
        p.x -= width;
    }
    return col;
}

// extensions of printing to vectors, matrices
int printVec4( vec2 p, vec4 v, int places){
    // consider instead returning float of percentage through printing?
    // total width includes full display and 1 blank character
    float fullWidth = baseWidth * float(places + 2) + dotWidth;
    int col = 0;
    // is there a way to iterate on this properly in glsl
    col = max( col, printFloat( p, v.x, places) );
    p.x -= fullWidth;
    col = max( col, printFloat( p, v.y, places) );
    p.x -= fullWidth;
    col = max( col, printFloat( p, v.z, places) );
    p.x -= fullWidth;
    col = max( col, printFloat( p, v.w, places) );
    return col;
}

int printMat4( vec2 p, mat4 mat, int places){
    int col = 0;
    float height = 7.0;
    for( int i = 0; i < 4; i++){
        vec4 v = vec4( mat[i] );
        col = max( col, printVec4( p, v, places));
        p.y += height;
    }
    return col;
}

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

// symmetrical cubic pulse
float isolate( float x, float centre, float radius){
    x = abs( x - centre );
    if( x > radius ) return 0.0;
    x /= radius;
    return 1.0 - x * x * (3.0 - 2.0 * x);
}


// SDF stuff
// some of these will be centred at origin, more complex may not
// for reference
// union : min(a, b)
// subtraction : max( -a, b)
// intersection : max( a, b )
float sphere( vec3 point, vec3 centre, float rad){
    return length( point - centre ) - rad;
}

// combination functions
float smoothMin(float a, float b, float k)
{ // polynomial smooth min (k = 0.1);
    float h = max( k-abs(a-b), 0.0 )/k;
    return min( a, b ) - h*h*k*(1.0/4.0);
}

float smoothMinP(float a, float b, float k){
    // alternate power-based method
    a = pow( a, k ); b = pow( b, k );
    return pow( (a*b)/(a+b), 1.0/k );
}

float smoothMinCubic( float a, float b, float k )
{ // allows higher degree of smoothness for derivatives
    float h = max( k-abs(a-b), 0.0 )/k;
    return min( a, b ) - h*h*h*k*(1.0/6.0);
}

float smoothMax( float a, float b, float k ){
    float h = clamp( 0.5 - 0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) + k*h*(1.0-h);
}

// 2d sdf functions
float stripySDF( float d, float freq){
    // returns a modulating value from an sdf
    float f = 1.0 - sign(d);
//	col *= 1.05 - exp(-4.0*abs(d) - 0.5); // darken values towards sdf surface
	f *= 0.8 + 0.2*cos(30.0*d * freq);
	//col = mix( col, vec3(1.0), 1.0-smoothstep(0.0,0.01,abs(d)) );
    f = mix( f, 1.0, 1.0-smoothstep( 0.0, 0.01, abs(d)));
    return f;
}

vec3 colourFromSDF( float d, float freq, vec3 baseCol ){
    vec3 col = vec3(1.0) - sign(d)* baseCol;
	col *= 1.05 - exp(-4.0*abs(d) - 0.5);
	col *= 0.8 + 0.2*cos(110.0*d * freq);
	col = mix( col, vec3(1.0), 1.0-smoothstep(0.0,0.01,abs(d)) );
    return col;
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


mat4 tetrahedronVertices(){
    // return 4 vertices of tetrahedron relative to centre
    // summit aligned to +y, main edge in yz plane
    vec4 v1 = vec4(0.0, 1.0, 0.0, 1.0);
    vec4 v2 = vec4(0.0, -1.0/3, sqrt(8.0/9), 1.0);
    vec4 v3 = vec4(sqrt(2.0/3), -1.0/3, -sqrt(2.0/9), 1.0);
    vec4 v4 = vec4(-sqrt(2.0/3), -1.0/3, -sqrt(2.0/9), 1.0);
    return mat4(v1, v2, v3, v4);
}

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

// tiled texture utils
vec2 localTileCoordsToGlobal( vec2 p, int tileIndex, int nRowLength ){
    /* transform local tile position to global image position
    expects squarely tiled images */
    vec2 result;
    vec2 tileSize = vec2( 1.0 / (nRowLength));

    // multiply out to global image pos
    vec2 sampleOrigin;
    sampleOrigin.y = (tileIndex  / nRowLength) -1;
    sampleOrigin.x = mod(tileIndex, nRowLength) ;

    result = (sampleOrigin + p) * tileSize;
    return result;
}

// simplex noise
// from Direct Computational Noise in GLSL

// in case you're wondering this is what real graphics programming looks like,
// not my trash
vec3 permute(vec3 x){
    return mod(((x*34) + 1)*x, 290.0);}
vec4 permute(vec4 x){
    return mod(((x*34) + 1)*x, 289.0);}
vec3 taylorInvSqrt(vec3 r){
    return 1.79284291400159 - 0.85373472095314 * r;}
vec4 taylorInvSqrt(vec4 r){
    return 1.79284291400159 - 0.85373472095314 * r;}
// 2d simplex noise
float simplexNoise2d(vec2 P){
    // we compute a grid, then shear it into tessellation of triangles
    // aka 2d simplices
    const vec2 c = vec2(
        0.211324865405187134, // (3.0 - sqrt(3.0)) / 6.0;
        0.366025403784438597); // 0.5 * (sqrt(3.0) - 1.0);
    // first corner
    vec2 i = floor(P+ dot(P, c.yy)); // localise to grid cell
    vec2 x0 = P- i + dot(i, c.xx); // no idea
    // other corners
    vec2 i1;
    i1.x = step(x0.y, x0.x); // 1.0 if x0.x > x0.y else 0.0
    i1.y = 1.0 - i1.x;
    vec4 x12 = x0.xyxy + vec4( c.xx, c.xx*2.0 - 1.0);
    x12.xt -= i1;

    i = mod(i, 289.0);
    vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0)) +
        i.x + vec3(0.0, i1.x, 1.0));
    // blend corners into centre
    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy),
        dot(x12.zw, x12.zw)), 0.0);
    m = m*m; // so power
    m = m*m; // much multiply
    // wow
    // gradients from 41 points on a line, mapped on to a diamond (apparently)
    vec3 x = fract(p * (1.0 / 41.0)) * 2.0 - 1.0;
    vec3 gy = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 gx = x - ox;
    // normalise gradients implicitly by scaling m
    m += taylorInvSqrt( gx * gx + gy * gy);
    // compute final noise at p
    vec3 g;
    g.x = gx.x * x0.x + gy.x * x0.y;
    g.yz = gx.yz * x12.xz + gy.yz * x12.yw;
    // scale output to range [-1, 1]
    return 130.0 * dot(m, g);
}
// 3d simplex noise
float simplexNoise3d(vec3 v){
    // we compute a grid, then shear it into tessellation of triangles
    // aka 2d simplices
    const vec2 c = vec2(1.0/6.0, 1.0/3.0);
    const vec4 d = vec4(0.0, 0.5, 1.0, 2.0);
    // first corner
    vec3 i = floor(v + dot(v, c.yyy)); // localise to grid cell
    vec3 x0 = v - i + dot(i, c.xxx); // no idea
    // other corners
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + 1.0 * c.xxx;
    vec3 x2 = x0 - i2 + 2.0 * c.xxx;
    vec3 x3 = x0 - 1 + 3.0 * c.xxx;

    i = mod(i, 289.0);
    vec4 p = permute( permute( permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0)) +
        i.y + vec4(0.0, i1.y, i2.y, 1.0)) +
        i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 1.0 / 7.0;
    vec3 ns = n_ * d.wyz - d.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);

    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4( x.xy, y.xy);
    vec4 b1 = vec4( x.zw, y.zy);

    vec4 s0 = floor( b0 ) * 2.0 + 1.0;
    vec4 s1 = floor( b1 ) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

    // vertices of tetrahedron I assume
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    // normalise gradients
    vec4 norm = taylorInvSqrt(vec4(
        dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
    p0 += norm.x;
    p1 += norm.y;
    p2 += norm.z;
    p3 += norm.w;

    vec4 m = max(0.6 - vec4(
        dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
        m = m * m;
        return 42.0 * dot(m*m, vec4(
            dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3) ));
}

//#endif
