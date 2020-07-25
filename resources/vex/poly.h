
#ifndef _POLY_H
#include "array.h"



// ---- points -----
function int iscornerpoint( int geo; int pointId ){
    // is this point on the corner of a quad mesh?
    return ( neighbourcount(geo, pointId) == 2);
    }

function float sumpointdistances( int geo; int points[]){
    // sums the distance between points, in order of array
    float sum = 0.0;
    for( int i = 1; i < len(points); i++){
        vector a = point(geo, "P", points[i - 1]);
        vector b = point(geo, "P", points[i]);
        sum += distance( a, b );
    }
    return sum;
}

// ---- lines ----
function int connectpointsbyattr( int geo; int ptnum; float range; string attr){
    vector pos = point(geo, "P", ptnum);
    int neighbours[] = nearpoints(geo, pos, range, 30 );
        foreach( int pt; neighbours){
            if( pt > @ptnum){
                int id = point(0, "id", pt);
                if( id == @id){
                    int line = addprim(0, "polyline", @ptnum, pt);
                    return line;
                    //break;
                    }
                }
            }
    return -1;
}



// ---- half-edges ------

// consider
struct HalfEdge {
    int equivalents[];
    int prim;
};

/* is this of any use at all? or are the basic functions enough?
anything to get more high-level control, but I don't think it
plays well with the rest of the ethos we have here
*/

function int[] hedgepoints( int geo; int hedge ){
    // returns points belonging to half edge
    int out[] = array( hedge_srcpoint(geo, hedge),
        hedge_dstpoint(geo, hedge) );
    return out;
}

// WARN
function int[] halfedgeequivalents( int geo; int hedge ){
    // returns the other half edges belonging to same main edge
    int edges[];
    int n = hedge;
    do{
        append(edges, n);
        n = hedge_nextequiv(geo, n); // WARN
    }while(n != hedge);
    return edges;
};

function int hedgeisunshared( int geo; int hedge ){
    // returns 1 if hedge is unshared else 0
    return ( hedge == hedge_nextequiv(geo, hedge));
}

function int[] allhedgeequivalents( int geo; int hedge ){
    // returns input and all equivalents
    int edges[] = halfedgeequivalents( geo, hedge);
    //append( edges, hedge );
    return edges;
};

function int[] primhalfedges( int geo; int prim ){
    // return all halfedges in primitive
    int edges[];
    // int vertices[] = primvertices( geo, prim );
    // foreach( int v; vertices ){
    //     append( edges, vertexhedge( geo, v) );
    // }
    int current = primhedge( geo, prim );
    int start = current;
    do{
        append(edges, current);
        current = hedge_next( geo, current );

    }while(start != current);
    return edges;
};

function int[] primhalfedgesexcept( int geo; int prim; int except){
    // returns all primitive half edges except hedge specified
    // ALSO REMOVE ALL HEDGES EQUIVALENT TO EXCEPT
    int edges[] = primhalfedges( geo, prim );
    //edges = subtract( edges, allhedgeequivalents( geo, except));
    foreach( int remove; allhedgeequivalents( geo, except )){
        removevalue( edges, remove);
    }
    return edges;
}

function int[] edgeprims( int geo; int hedge ){
    // returns all primitives containing this half edge or equivalents
    int out[];
    foreach( int h; allhedgeequivalents(geo, hedge)){
        append( out, hedge_prim(geo, h));
    }
    return out;
}

// time for a diagram

/*

starthedge              targethedge
    \                       \
     \                       \
================== O ===================
    ---->        | I        ---->
                 | I ^
        primA    v I |       primB
                   I |
                   I
*/

function int[] nexthedgesinloop(int geo; int starthedge){
    // selects the next edges in loop on either side

    int points[] = hedgepoints( geo, starthedge );

    int foundhedges[];

    // check primary edges only, to avoid counting duplicates
    //starthedge = hedge_primary(geo, starthedge);
    int seedprim = hedge_prim(geo, starthedge);
    foreach( int testhedge; primhalfedgesexcept(geo, seedprim, starthedge)){

        if( hedgeisunshared( geo, testhedge )){
            continue;
        }

        // check newly adjacent primitive
        int newprim = hedge_prim( geo, hedge_nextequiv( geo, testhedge) );
        //newprim = seedprim;

        // iterate newprim edges
        //foreach( int newhedge; primhalfedges(geo, newprim)){
        foreach( int newhedge; primhalfedgesexcept(geo, newprim, testhedge)){
            //newhedge = hedge_primary(geo, newhedge);

            // check that edge is not equivalent to edge we just came from
            if( hedge_isequiv( geo, newhedge, testhedge)){
                continue;
                //break;
            }
            // check edge isn't already in found edges
            if( index(foundhedges, newhedge) > -1){
                //break;
                //continue;
            }

            // check if edge src or dest is in original points
            int newhedgepts[] = hedgepoints( geo, newhedge);
            int crossover[] = intersect( newhedgepts, points);
            if( len(crossover) > 0){
                append(foundhedges, hedge_primary(geo, newhedge));
                //break;
            }
        }
    }
    return foundhedges;
}


function int[] edgeloop( int geo; int seedhedge ){
    // builds edge loop from a seed halfedge
    int outhedges[];
    //int activehedges[];
    int activehedges[] = array( seedhedge );
    do{
        int foundhedges[];
        foreach( int activehedge; activehedges ){
            foundhedges = union(nexthedgesinloop( geo, activehedge ), foundhedges);
        }
        activehedges = subtract(foundhedges, outhedges);
        outhedges = union(outhedges, foundhedges);

    }while( len(activehedges) > 0);

    return outhedges;
}


function int[] pointsfromhedges( int geo; int hedges[] ){
    // return all points included in halfedge selection
    int out[];
    foreach( int hedge; hedges){
        // out = union(out, hedgepoints(geo, hedge));
        int temppts[] = hedgepoints(geo, hedge);
        //out = union(temppts, tempout);
        out = union(out, temppts);
    }
    return sort(out);
}

function int[] pointloopfrompoints( int geo; int a; int b){
    // returns all points lying on edge loop of a and b
    int columnhedge = pointedge( geo, a, b );
    int columnhedges[] = edgeloop( geo, columnhedge );
    int columnpts[] = pointsfromhedges( geo, columnhedges );
    return columnpts;
}

function int maprowscolumns( int geo; int corner; int columndir ){
    // sets int attributes denoting row and column of each point
    // assumes quad mesh
    // columndir is next point in column, must be neighbour
    if( !iscornerpoint( geo, corner )){
        return -1; // do it right
    }

    // get initial column points
    int columnpts[] = pointloopfrompoints( geo, corner, columndir );
    int rowpts[];
    // iterate columns
    foreach( int i; int columnpt; columnpts){
        // get transverse points
        int transverse[] = subtract( neighbours( geo, columnpt), columnpts );
        rowpts = pointloopfrompoints( geo, columnpt, transverse[0] );

        // iterate rows
        foreach( int n; int rowpt; rowpts){
            setpointattrib( geo, "column", rowpt, i);
            setpointattrib( geo, "row", rowpt, n);
        }
    }
    setdetailattrib( geo, "ncolumns", len(columnpts));
    setdetailattrib( geo, "nrows", len(rowpts));
    return 1;
}



function vector halfedgemidpoint( int geo; int hedge ){
    vector startPos = point( geo, "P", hedge_srcpoint( geo, hedge ) );
    vector endPos = point( geo, "P", hedge_dstpoint( geo, hedge ) );
    return (endPos + startPos) / 2.0 ;
};

#define _POLY_H
#endif
