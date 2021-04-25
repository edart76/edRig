
#ifndef _ED_POLY_H

#define _ED_POLY_H
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

function int initpointattrs(int geo){
    // just set some useful attributes on to the points
    // to be run in detail for now
    addattrib(0, "point", "relpos", vector(set(1, 1, 1)));
    for (size_t i = 0; i < npoints(0); i++) {
        setpointattrib(geo, "id", i, i);
        if (i < 1){
            vector relpos = set(0, 0, 0);
            setpointattrib(geo, "relpos", i, relpos);
            continue;
        }
        vector relpos = point(geo, "P", i)
            - point(geo, "P", i-1);
        setpointattrib(geo, "relpos", i, relpos);
    }
    return 1;
}

function vector[] pointpositions(int geo;){
    // return point positions as vector array
    vector result[];
    for(int i=0; i < npoints(geo); i++){
        append(result, vector(point(geo, "P", i)));
    }
    return result;
}

function int setpointpositionsfromarray(int geo; vector poses[]){
    // given array of vectors, set all point positions
    for( int i = 0; i < len(poses); i++){
        setpointattrib(geo, "P", poses[i]);
    }
    return 1;
}

// ---- lines ----
function int[] addpointline(int geo; vector pos; int parentpt){
    // addpoint, but automatically adds a polyline from parent
    int npt = addpoint(0, pos);
    int nprim = addprim(0, "polyline", parentpt, npt);
    int result[] = array(npt, nprim);
    return result;
}


int connectpointsbyattr( int geo; int ptnum; float range; string attr){
    vector pos = point(geo, "P", ptnum);
    int neighbours[] = nearpoints(geo, pos, range, 30 );
        foreach( int pt; neighbours){
            //if( pt > i@ptnum ){
            // if( pt > point(geo, "ptnum", ptnum) ){
            if( pt > ptnum ){
                int id = point(0, "id", pt);
                if( id == id){
                    int line = addprim(0, "polyline", ptnum, pt);
                    return line;
                    //break;
                    }
                }
            }
    return -1;
}

function int[] insertpoint(int outerprim; int pt){
    // given one primitive and one point,
    // insert point in primitive and triangulate
    // for each half
    int pts[] = primpoints(0, outerprim);
    removeprim(0, outerprim, 1);
    int newprims[];

    for (size_t i = 0; i < len(pts); i++)
    {
        int prev = (i + -1) % len(pts);
        int newprim = addprim(0, "poly",  pts[i], pt, pts[prev]);
        append(newprims, newprim);
    }

    return newprims;
}



function int[] insertpoints(string weldpts; string collisionprims;
    string newgrp; int mode){
    // inserts new points into collision prim faces,
    // corresponding to weld pts
    // mode - 0 : nearest point, 1 : normal project
    int pts[] = expandpointgroup(1, weldpts);
    int addedpts[];
    foreach(int pt; pts){
        // nearest point
        vector pos = point(1, "P", pt);
        vector uvw;
        vector hitpos;
        int hitprim;
        if (mode == 0){
            xyzdist(0, collisionprims, pos, hitprim, uvw);
        }
        if (mode == 1){
            vector dir = -point(1, "N", pt);
            intersect(0, collisionprims, pos, dir, hitpos, uvw);
            xyzdist(0, collisionprims, hitpos, hitprim, uvw);
            // intersect(0, pos, dir, hitpos, uvw);
            // xyzdist(0, hitpos, hitprim, uvw);
        }
        hitpos = primuv(0, "P", hitprim, uvw);
        int newpt = addpoint(0, hitpos);

        int newprims[] = insertpoint(hitprim, newpt);
        //removeprim(0, hitprim, 0);
        foreach(int newprim; newprims){
            setprimgroup(0, collisionprims, newprim, 1);
        }
        append(addedpts, newpt);
    }
    return addedpts;
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

function int hedgepointopposite( int geo; int hedge; int pt ){
    // return the opposite point in hedge
    int pts[] = hedgepoints(geo, hedge);
    removevalue(pts, pt);
    return pts[0];
}

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
    foreach( int remove; allhedgeequivalents( geo, except )){
        removevalue( edges, remove);
    }
    return edges;
}

function int[] hedgeprims( int geo; int hedge ){
    // returns all primitives containing this half edge or equivalents
    int out[];
    foreach( int h; allhedgeequivalents(geo, hedge)){
        append( out, hedge_prim(geo, h));
    }
    return out;
}

function int primpointshedge( int geo; int prim; int pointa, pointb){
    // return half edge on prim between given points
    return intersect(primhalfedges(geo, prim), allhedgeequivalents(
        geo, pointedge(geo, pointa, pointb)))[0];
}

// higher topo functions

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
        foreach( int newhedge; primhalfedgesexcept(geo, newprim, testhedge)){
            //newhedge = hedge_primary(geo, newhedge);

            // check that edge is not equivalent to edge we just came from
            if( hedge_isequiv( geo, newhedge, testhedge)){
                continue;
                //break;
            }
            // // check edge isn't already in found edges
            // if( index(foundhedges, newhedge) > -1){
            //     //break;
            //     //continue;
            // }

            // check if edge src or dest is in original points
            int newhedgepts[] = hedgepoints( geo, newhedge);
            int crossover[] = intersect( newhedgepts, points);
            if( len(crossover) > 0){
                // check for pole vertices
                if( neighbourcount(geo, crossover[0] ) != 4){
                    continue;
                }
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


/* next edge is INTERSECTION of connected point edges and primitive edges,
SUBTRACT previous edge(s)
*/


function int[] crawlmesh2(int geo;
     int activehedge; int activepoint; int ptidx;
        int foundpoints[]; int foundprims[]){

    int newedges[]; // edges for next iteration
    int currentprim = hedge_prim(geo, activehedge);

    // check if prim is found
    if( find(foundprims, currentprim) > -1){
        return newedges;
    }
    append(foundprims, currentprim);
    setprimattrib(geo, "found", currentprim, 1);

    // cycle around prim hedges and add adjacents to return
    for (int i = 0; i < len(primpoints(geo, currentprim)); i++) {
        // really not sure about this
        append(foundpoints, activepoint);
        setpointattrib(geo, "twin", activepoint, ptidx++);
        int newpt = subtract(
            intersect(neighbours(geo, activepoint), primpoints(geo, currentprim)),
            hedgepoints(geo, activehedge))[0];
        activehedge = primpointshedge(geo, currentprim, activepoint, newpt);
        int spechedge = hedge_nextequiv(geo, activehedge);
        if( find(foundprims, hedge_prim(geo, spechedge)) < 0 )
        {
            append(newedges, spechedge);
        }
        setpointgroup(geo, "found", newpt, 1);
        activepoint = newpt;
    }
    return newedges;
}


// Higher functions still combining topo with spatial info

function matrix3 tangentmatrix(int geo;
    int face){
        // return orientation matrix for polygon face
        // oriented to face gradient
        string geos = opfullpath(".");
        vector2 samplepos = set(0.5, 0.5);
        vector grad = normalize(primduv(geos, face, samplepos, 1, 1));
        vector N = normalize(prim(geo, "N", face));
        vector bitan = cross(grad, N);

        return matrix3(set(grad, N, bitan));
    }


#define SS_FLATTENLENGTH 0
#define SS_PRESERVELENGTH 1

function vector projectsurfacespace(int geo;
    vector origin; vector dir; int face;
    int mode;
    // output references
    int escapehedge;
    vector escapepos;
    vector escapedir
)
    {
    /* given face and vector to project,
    flatten it into surface space and project it out

    mode: either squash a high-angle vector
    to its direct projection,
    or restore its length in surface space

    escapehedge: returns the prim hedge index crossed by the
    flattened vector, or -1 if vector terminates in this prim
    escapepos: position at which vector escapes
    escapedir: portion of vector lying outside prim
    */

    // matrix to rotate all points to surface space
    matrix orientmat = tangentmatrix(geo, face);

    return dir;


    }



function int[] primsbetweenpoints(int geo;
    int pta; int ptb;
    int activeprim; int visitedprims[];
    int success;
){
    // breadth search from a to b,
    // adding primitives to visited
    int activepts[] = primpoints(geo, activeprim);
    if(IN(activepts, ptb)){
        success = 1;

    }
    return activepts;
}


#endif
