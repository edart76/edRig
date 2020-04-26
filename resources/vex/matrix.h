// functions for multiplying, transposing and inverting matrices

#ifndef MATRIX_H
#define MATRIX_H 1

function float[] M_trans(float A[]; int m; int n)
{
    float temp;
    float At[];
    for(int i=0; i<m; i++)
    {
        for(int j=0; j<n; j++)
        {
            At[j*m+i] = A[i*n+j];
        }
    }
    return At;
}

// now rewritten to be readable by people that aren't robots
function float[] matrix_mult( float A[]; float B[];
    int rowsA; int colsArowsB; int colsB)
{
    float C[];
    for( int i=0; i < rowsA; i++)
      {

        for( int j=0; j < colsB; j++)
          {
            // we now iterate over the rows and columns of the OUTPUT matrix,
            // with rows of A and columns of B
            int Cindex = [ i * rowsA + j];
            int r = 0;
            for( int k=0; k < colsArowsB; k++)
              {
                float Aval = A[ i * colsArowsB + k];
                float Bval = A[ colsArowsB * j + k];

                r += Aval * Bval;
            }

            C[Cindex] = r;
        }
    }
  return C;
}

/*
A = [ 0, 1, 2,      B = [ 0, 1,         C = [ n, m,
      3, 4, 5 ]           2, 3,               n, o ]
                          4, 5 ]
rowsA = 2
colsArowsB = 3
colsB = 2
*/

// float arrays row-major - one row of matrix, then the next, so on
// multiply two matrices together
// COLUMNS OF FIRST MUST EQUAL ROWS OF SECOND
function float[] matrix_multB(float A[]; float B[];
    int m; int n; int l)
{ //
    // A, B - input matrix arrays
    // m - rows of A
    // n - columns of A
    // l - columns of B
    // we return a matrix of row length n
    float C[]; // initialise output matrix
    for(int i=0; i<m; i++)
      { //
          int count=0;
          for(int j=0; j<n; j++)
            { // n is number entries in A row / number columns in A
                float r = A[i*n+j]; // r is current matrix value
                if(r != 0)
                  { // A entry has value
                      for(int k=0; k<l; k++)
                      { // l must be number columns in output matrix
                          C[i*l+k] += r*B[j*l+k];
                      }
                  }
                else
                  {
                      count++;
                  }

                if(count == n-1)
                  { // if entire row of A is blank
                      for(int k=0; k<l; k++)
                      { // entire column of C is blank
                          C[i*l+k] = 0;
                      }
                  }
            }
      }
    return C;
}

function float[] matrix_mult_square(float A[]; float B[]; int rank){
      return matrix_mult(A, B, rank, rank, rank);
    }

//
//
#endif
