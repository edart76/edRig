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
