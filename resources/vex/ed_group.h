#ifndef GROUP_H


function string[] pointgroupsmatching( int geo; string ex){
    string ptgrps[] = detailintrinsic( geo, "pointgroups" );
    string result[] = {};
    foreach( string grp; ptgrps){
        if( match(ex, grp)){
            append(result, grp);
        }
    }
    return result;
}





#define GROUP_H
#endif
