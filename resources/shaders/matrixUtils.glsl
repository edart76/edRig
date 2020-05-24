
/* matrix functions running on 1d arrays
all efforts to pin down the rules on row-major vs column-major
have only deepened my confusion
these functions will be consistent
if your stuff doesn't work with them, try transposing it :)
*/

struct SparseMatrix{
    // holds sparse matrix as arrays of indices and values
    int rows;
    int columns;


};




// buffer Adaptive{
//     float test[];
//
// };

SparseMatrix testMult( SparseMatrix a){
    SparseMatrix result;

    return result;
}




// float arrays row-major - one row of matrix, then the next, so on
// multiply two matrices together
// COLUMNS OF FIRST MUST EQUAL ROWS OF SECOND
// float[] matrix_multB(float A[]; float B[];
//     int m; int n; int l)
// { //
//     // A, B - input matrix arrays
//     // m - rows of A
//     // n - columns of A
//     // l - columns of B
//     // we return a matrix of row length n
//     float C[]; // initialise output matrix
//     for(int i=0; i<m; i++)
//       { //
//           int count=0;
//           for(int j=0; j<n; j++)
//             { // n is number entries in A row / number columns in A
//                 float r = A[i*n+j]; // r is current matrix value
//                 if(r != 0)
//                   { // A entry has value
//                       for(int k=0; k<l; k++)
//                       { // l must be number columns in output matrix
//                           C[i*l+k] += r*B[j*l+k];
//                       }
//                   }
//                 else
//                   {
//                       count++;
//                   }
//
//                 if(count == n-1)
//                   { // if entire row of A is blank
//                       for(int k=0; k<l; k++)
//                       { // entire column of C is blank
//                           C[i*l+k] = 0;
//                       }
//                   }
//             }
//       }
//     return C;
// }
