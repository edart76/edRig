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

function string[] groupsfromprim( int geo; int primnum){
    // return all groups containing target prim
    string primgrps[] = detailintrinsic( geo, "primitivegroups");
    string result[] = {};
    foreach( string grp; primgrps){
        if( inprimgroup(0, grp, primnum)){
            append(result, grp);
        }
    }
    return result;
}



#define GROUP_H
#endif
