// functions for working with arrays

#ifndef "ARRAY_H"

function int index(int input[]; int item){
    // returns first index of item or -1 if not in array
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

#define "ARRAY_H"
#endif
