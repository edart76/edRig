// reference vex stuff


// by animatrix, finding edge loop from initial edge

int Contains ( string collection [ ]; string item )
{
    for ( int i = 0; i < arraylength ( collection ); ++i )
        if ( collection [ i ] == item )
            return 1;
    return 0;
}


int Contains ( int collection [ ]; int item )
{
    for ( int i = 0; i < arraylength ( collection ); ++i )
        if ( collection [ i ] == item )
            return 1;
    return 0;
}


//  VEX grammar doesn't support functions that return arrays.
//  So we are using a dash separated string that represents a collection.

string GetPrimsFromEdge ( int input; int pt0; int pt1 )
{
    string prims;
    int hedge = pointedge ( input, pt0, pt1 );
    if ( hedge != -1 )
    {
        int count = hedge_equivcount ( input, hedge );
        for ( int i = 0; i < count; ++i )
        {
            int pr = hedge_prim ( input, hedge );
            if ( pr != -1 )
            {
                prims += itoa ( pr ) + "-";
                hedge = hedge_nextequiv ( input, hedge );
            }
        }
    }
    return prims;
}


int GetNextPoint ( int input; int edgept0; int edgept1; int currentpt )
{
    int pointNeighbors [ ] = neighbours ( input, currentpt );

    string sprims = GetPrimsFromEdge ( input, edgept0, edgept1 );
    string aprims [ ] = split ( sprims, "-" );
    int prims [ ];
    foreach ( string s; aprims )
        push ( prims, atoi ( s ) );

    int primPoints [ ];
    for ( int i = 0; i < arraylength ( prims ); ++i )
    {
        int count = primvertexcount ( input, prims [ i ] );
        for ( int f = 0; f < count; ++f )
        {
            int vertIndex = vertexindex ( input, prims [ i ], f );
            int pointIndex = vertexpoint ( input, vertIndex );
            push ( primPoints, pointIndex );
        }
    }

    int uniquePoints [ ];
    for ( int i = 0; i < arraylength ( pointNeighbors ); ++i )
    {
        if ( !Contains ( primPoints, pointNeighbors [ i ] ) )
            push ( uniquePoints, pointNeighbors [ i ] );
    }

    if ( arraylength ( uniquePoints ) == 1 )
        return uniquePoints [ 0 ];

    return -1;
}


//  Traverse Edges

string BuildEdgeList ( int input; string edgeCollection )
{
    if ( edgeCollection == "" )
        return "!*";

    string edges [ ];
    string sedges [ ] = split ( edgeCollection, " " );

    int traverseCount = 0;
    int totalCount = arraylength ( sedges );

    while ( arraylength ( sedges ) > 0 )
    {
        string sedge;
        pop ( sedge, sedges );
        string edgePoints [ ] = split ( sedge, "-" );

        if ( !Contains ( edges, sedge ) )
        {
            ++traverseCount;
            for ( int c = 0; c < 2; ++c )
            {
                int points [ ];
                int pt0 = atoi ( edgePoints [ c ] );
                int pt1 = atoi ( edgePoints [ 1 - c ] );
                int currentpt = pt0;
                int lastPoint = pt0;
                push ( points, currentpt );
                int nextPoint = GetNextPoint ( input, pt0, pt1, currentpt );
                //printf( "nextpt: %s\n", nextPoint );
                while ( nextPoint != -1 && nextPoint != lastPoint )
                {
                    pt0 = currentpt;
                    pt1 = nextPoint;
                    currentpt = pt1;
                    push ( points, currentpt );
                    nextPoint = GetNextPoint ( input, pt0, pt1, currentpt );
                    //printf( "nextpt: %s\n", nextPoint );
                }

                for ( int i = 0; i < arraylength ( points ) - 1; ++i )
                {
                    int p0 = min ( points [ i ], points [ i + 1 ] );
                    int p1 = max ( points [ i ], points [ i + 1 ] );
                    push ( edges, sprintf ( "%s-%s", p0, p1 ) );
                    //printf( "edge: %s\n", sprintf ( "%s-%s", p0, p1 ) );
                }
                //printf( "points: %s\n", points );
            }
            push ( edges, sedge );
        }
        //else
            //printf( "BYPASS: %s\n", sedge );
    }

    string edgelist = "";
    foreach ( string s; edges )
        edgelist += "p" + s + " ";

    //printf( "Traversed: %s edges out of %s edges\n", traverseCount, totalCount );
    return edgelist;
}

s@edgelist = BuildEdgeList ( 0, chs("edges") );
