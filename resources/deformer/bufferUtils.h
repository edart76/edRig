#ifndef bufferutils
#define bufferutils

// utilities for dealing with raw buffers

/*
consider the classic method of mapping connectivity in a mesh:

array 1: valence values [3, 4, 4, 4, 3, 4, 4] etc
array 2: connected indices [ (2, 4, 7), (4, 3, 5, 6), ] etc
array 3: [ (x, y , z, w), (x, y , z, w), (x, y , z, w), ] etc

with higher datatypes this is cool, but with buffers there's a problem
without iterating through both arrays, we have no way of knowing where
the indices of the point's valence start and end

consider instead:
shader is passed a number of arrays equal to the maximum valence of the
entire mesh (assume a maximum of 6)

these slice horizontally across the indices:
[ 2, 4, ]
[ 4, 3, ]
[ 7, 5, ]
[-1, 6, ]
[-1,-1, ]

with -1 meaning no more connections. in this way we can reconstruct all
connectivity from only the single index of the queried vertex

*/
