


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


function int[] primHalfEdges( int geo; int prim ){
    int edges[];
    int vertices[] = primvertices( geo, prim );
    foreach( int v; vertices ){
        append( edges, vertexhedge( geo, v) );
    }
    return edges;
};

function int[] halfEdgeEquivalents( int geo; int hedge ){
    int edges[];
    int n = hedge;
    do{
        append(edges, n);
        n = hedge_nextequiv(geo, n);
    }while(n != hedge);
    return edges;
};

function vector halfEdgeMidpoint( int geo; int hedge ){
    vector startPos = point( geo, "P", hedge_srcpoint( geo, hedge ) );
    vector endPos = point( geo, "P", hedge_dstpoint( geo, hedge ) );
    return (endPos + startPos) / 2.0 ;
};
