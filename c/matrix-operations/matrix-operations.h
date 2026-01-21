#include <stdlib.h>

typedef struct mat_t mat_t;

enum Status{
	FAILURE = 0,
	SUCCESS = 1,
	DIMENSIONS_ERROR = -1,
	NULL_PTR_ERROR = 2
};

enum Bool{
	FALSE,
	TRUE
};

/*
* Creates a mat_t structure that holds a pointer to matrix of dimensions "nrow" and "ncol"
* nrow and nrow are greater than 0
* Returns a mat_t pointer if successful (NULL pointer otherwise)
* O(n*m) time complexity (n-#rows, m - #columns)
*/
mat_t* matrix_create(size_t rows, size_t cols);

/*
* Frees the mat_t allocated memory (including the matrix)
*/
void matrix_destroy(mat_t* matrix);

/*
* Adds the values of two matrices and stores the output in a result matrix
* Requires that the two matrices and the result matrix have equivalent dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_add(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result);

/*
* Sets the elements in the matrix
* If matrix is nXm and size is bigger, the function will only set the first n*m values
* Returns a status code: SUCCESS, FAILURE or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_set(mat_t* matrix, double* elements, size_t size);

/*
* Returns the number of rows in mat
* O(1) time complexity
*/
size_t matrix_get_num_of_rows(const mat_t* mat);

/*
* Returns the number of columns in mat
* O(1) time complexity
*/
size_t matrix_get_num_of_cols(const mat_t* mat);

/*
* Returns the value in (row_idx, col_idx) cell in the matrix
* O(1) time complexity
*/
double matrix_get_val(const mat_t* matrix, const size_t row_idx, const size_t col_idx);

/*
* Multiplies two matrices and stroes the output in a result matrix
* Requires that the two matrices and the result matrix have appropriate dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_multiply(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result);

/*
* Multiplies a matrix with the given scalar and stroes the output in a result matrix
* Requires that the matrix and the result matrix have appropriate dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_scalar_multiply(const mat_t* matrix, const double scalar, mat_t* result);

/*
* Returns TRUE is the matrices are the same (FALSE otherwise)
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_is_same(const mat_t* matrix_a, const mat_t* matrix_b);

/*
* Returns a transposed matrix in a result matrix
* Requires that the matrix (mXn) and the result matrix (nXm) have appropriate dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_transpose(const mat_t* matrix, mat_t* result);

/*
* Returns the trace of a matrix
* Requires a square matrix
* Sets in a status code: SUCCESS or DIMENSIONS_ERROR
* O(n) time complexity (n-#rows, n - #columns)
*/
double matrix_trace(const mat_t* matrix, int* status);

/*
* Calculated the determinant of the matrix
* Requires a square matrix
* Sets in a status code: SUCCESS or DIMENSIONS_ERROR
* O(n^3) time complexity (n-#rows, n - #columns) - using LU decomposition
*/
double matrix_determinant(const mat_t* matrix, int* status);

/*
* Returns a sub matrix of matrix without row and col and stroes it a result matrix
* Requires that the matrix (nXm) and the result matrix (nXm) have appropriate dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n*m) time complexity (n-#rows, m - #columns)
*/
int matrix_get_submatrix(const mat_t* matrix, size_t row, size_t col, mat_t* result);

/*
* Returns Forbenius /norm of the matrix 
* Returns a status code: SUCCESS or FAILURE
* O(n*m) time complexity (n-#rows, m - #columns)
*/
double matrix_norm(const mat_t* matrix);

/*
* Calculates the inverse matrix of matrix and stroes it a result matrix
* Requires both square matrices with the same dimensions
* Returns a status code: SUCCESS or DIMENSIONS_ERROR
* O(n^5) time complexity (n-#rows, n - #columns)
*/
int matrix_inverse(const mat_t* matrix, mat_t* result);


