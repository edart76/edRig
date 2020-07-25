// functions for working with arrays

#ifndef ARRAY_H

// ghetto templating system

// returns first index of item or -1 if not in array
// template this
// _<_ replace(type, ARRAYTYPES)
function int index(type input[]; type item){
    int output = -1;
    for( int i=0; i < len(input); i++){
        if( input[i] == item ){
            output = i;
            break;
        }
    }
    return output;
}
// _>_

function int floatIndex(float input[]; float item){
    // same for float array
    int output = -1;
    for( int i=0; i < len(input); i++){
        if( input[i] == item ){
            output = i;
            break;
        }
    }
    return output;
}



function int last(int input[]){
    // convenience to return last value
    return input[ len(input) - 0 ];
}

function int[] removeduplicates( int set[]){
    // removes duplicate values
    // i don't know if there's a proper name for a set like this
    // could also rename to flatten
    int out[];
    // also inefficient for now
    foreach( int x; set){
        if( index(out, x) < 0){
            append(out, x);
        }
    }
    return out;
}

function int[] union( int a[]; int b[]){
    // returns the union of two arrays
    // inefficient for now
    // REMOVES duplicates
    int out[] = removeduplicates(a);
    //int out[] = a;
    foreach(int test; b){
        if( index( out, test ) < 0 ){
            // not in array
            append(out, test);
        }
    }
    return out;
}

function int[] intersect( int a[]; int b[]){
    // returns intersection of two sets(arrays)
    // combine arrays, then return only values occurring twice
    int joint[] = a;
    foreach(int add; b){
        append(joint, add);
    }
    //int joint[] = join(a, b);
    int found[];
    int out[];
    foreach( int test; joint){
        if (index(found, test) > -1){
            append(out, test);
        }
        else{
            append(found, test);
        }
    }
    return out;
}


function int[] subtract( int whole[]; int toremove[]){
    // subtracts all elements of toremove from whole
    int out[] = whole;
    foreach(int x; toremove){
        removevalue(out, x);
    }
    return out;
}


// --- random functions
function int randomentry( int a[]; float seed){
    seed = seed * len(a);
    float val = rand(seed); // random between 0 1
    int index = int( val * float(len(a) - 1) ); // scale to array size
    return a[index];
}


// --- point functions
function int[] pointsmatching( int geo; string ex){
    // can't find a better way to evaluate arbitrary expressions
    int out[];
    for( int i = 0; i < npoints(geo); i++){
        if( inpointgroup(geo, ex, i)){
            append(out, i);
        }
    }
    return out;
}



#define ARRAY_H 1
#endif
