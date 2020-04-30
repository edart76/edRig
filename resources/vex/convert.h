
#ifndef CONVERT_H

// functions for converting between data structures in vex

// convert vector3 array to sequence of floats
function float[] varray_to_farray(vector input[]){
    float output[];
    foreach(vector i; input){
        float fl[] = set(i);
        push(output, fl);
        }
    return output;
    }

// convert float array to vector3
function vector[] farray_to_varray(float input[]){
    vector output[];
    int ln = len(input);
    for(int i = 0; i < ln; i + 3){
        int y = i + 1;
        int z = i + 2;
        vector unit = set(
            input[i], input[y], input[z]);
        push(output, unit);
        }
    return output;
    }

function string ftoa(float in){
        return sprintf("%g", in);
    }




#define CONVERT_H 1
#endif
