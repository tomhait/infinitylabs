#include "matrix-operations.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <math.h>

#define UNUSED_FUNCTION __attribute__((unused))

struct mat_t{
	size_t nrow;
	size_t ncol;
	double *matrix;
};

mat_t* matrix_create(size_t rows, size_t cols)
{
	assert(rows > 0);
	assert(cols > 0);
	mat_t *mat = malloc(sizeof(mat_t));
	if(!mat) return NULL;
	mat->matrix = calloc(rows*cols, sizeof(double));
	if(!mat->matrix){
		free(mat);
		return NULL;
	}
	mat->nrow = rows;
	mat->ncol = cols;
	return mat;
}

void matrix_destroy(mat_t* matrix)
{
	assert(matrix);
	free(matrix->matrix);
	free(matrix);
}

int matrix_add(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result)
{
	assert(matrix_a);
	assert(matrix_b);
	if(matrix_a->nrow != matrix_b->nrow) return DIMENSIONS_ERROR;
	if(matrix_a->ncol != matrix_b->ncol) return DIMENSIONS_ERROR;
	double *output = result->matrix;
	size_t COLS = matrix_a->ncol;
	for(size_t i=0; i < matrix_a->nrow; i++)
	{
		for(size_t j=0; j < matrix_a->ncol; j++)
		{
			output[i*COLS+j] = matrix_a->matrix[i*COLS+j]+matrix_b->matrix[i*COLS+j];
		}
	}
	return SUCCESS;
}

static int Check_multiplied_matrices(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result)
{
	assert(matrix_a);
	assert(matrix_b);
	assert(result);
	if(matrix_a->ncol != matrix_b->nrow) return DIMENSIONS_ERROR;
	if(result->nrow != matrix_a->nrow) return DIMENSIONS_ERROR;
	if(result->ncol != matrix_b->ncol) return DIMENSIONS_ERROR;
	return SUCCESS;
}

int matrix_multiply(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result)
{

	if(Check_multiplied_matrices(matrix_a, matrix_b, result) == DIMENSIONS_ERROR) return DIMENSIONS_ERROR;
	
	double *output = result->matrix;
	size_t n = matrix_a->ncol;
	size_t p = matrix_b->ncol;
	for(size_t i=0; i < matrix_a->nrow; i++)
	{
		for(size_t j=0; j < matrix_b->ncol; j++)
		{
			output[i*p+j] = 0.0;
			for(size_t k=0; k < n; k++)
			{
				output[i*p+j] += matrix_a->matrix[i*n+k]*matrix_b->matrix[k*p+j];
			}
			
		}
	}
	return SUCCESS;	
}

int matrix_scalar_multiply(const mat_t* matrix, const double scalar, mat_t* result)
{
	assert(matrix);
	assert(result);
	if(matrix->nrow != result->nrow) return DIMENSIONS_ERROR;
	if(matrix->ncol != result->ncol) return DIMENSIONS_ERROR;
	
	double *output = result->matrix;
	size_t COLS = matrix->ncol;
	for(size_t i=0; i < matrix->nrow; i++)
	{
		for(size_t j=0; j < matrix->ncol; j++)
		{
			output[i*COLS+j] = matrix->matrix[i*COLS+j]*scalar;
		}
	}
	return SUCCESS;	
}

int matrix_is_same(const mat_t* matrix_a, const mat_t* matrix_b)
{
	assert(matrix_a);
	assert(matrix_b);
	if(matrix_a->nrow != matrix_b->nrow) return FALSE;
	if(matrix_a->ncol != matrix_b->ncol) return FALSE;
	size_t COLS = matrix_a->ncol;
	for(size_t i=0; i < matrix_a->nrow; i++)
	{
		for(size_t j=0; j < matrix_b->ncol; j++)
		{
			if(matrix_a->matrix[i*COLS+j] != matrix_b->matrix[i*COLS+j]) return FALSE;
		}
	}	
	return TRUE;
}

int matrix_set(mat_t* matrix, double* elements, size_t size)
{
	assert(matrix);
	size_t mat_size = matrix->nrow * matrix->ncol;
	if(mat_size > size) mat_size = size;
	for(size_t i=0; i< mat_size; i++) matrix->matrix[i] = elements[i];
	return SUCCESS;
}

int matrix_transpose(const mat_t* matrix, mat_t* result)
{
	assert(matrix);
	assert(result);
	if(matrix->nrow != result->ncol) return DIMENSIONS_ERROR;
	if(matrix->ncol != result->nrow) return DIMENSIONS_ERROR;
	
	double *output = result->matrix;
	size_t COLS = matrix->ncol;
	size_t ROWS = matrix->nrow;
	for(size_t i=0; i < ROWS; i++)
	{
		for(size_t j=0; j < COLS; j++)
		{
			output[j*ROWS+i] = matrix->matrix[i*COLS+j];
		}
	}	
	return SUCCESS;
}

double matrix_trace(const mat_t* matrix, int* status)
{
	assert(matrix);
	assert(matrix->nrow == matrix->ncol);
	double trace = 0;
	size_t COLS = matrix->ncol;
	for(size_t i=0; i < matrix->nrow; i++) trace += matrix->matrix[i*COLS + i];
	*status = SUCCESS;
	return trace;
}

size_t matrix_get_num_of_rows(const mat_t* matrix)
{
	assert(matrix);
	return matrix->nrow;
}

size_t matrix_get_num_of_cols(const mat_t* matrix)
{
	assert(matrix);
	return matrix->ncol;
}

double matrix_get_val(const mat_t* matrix, const size_t row_idx, const size_t col_idx)
{
	assert(matrix);
	assert(matrix->nrow > row_idx);
	assert(matrix->ncol > col_idx);
	return matrix->matrix[row_idx*matrix->ncol + col_idx];
}

static void Check_submatrix_validity(const mat_t* matrix, mat_t* result)
{
	assert(matrix);
	assert(result);
	assert(matrix->nrow-1 == result->nrow);
	assert(matrix->ncol-1 == result->ncol);
}

int matrix_get_submatrix(const mat_t* matrix, size_t row, size_t col, mat_t* result)
{
	Check_submatrix_validity(matrix, result);
	double *output = result->matrix;
	size_t n = matrix->nrow;
	size_t m= matrix->ncol;
	size_t dest_i = 0, dest_j = 0;
	for(size_t i=0; i < n; i++)
	{
		for(size_t j=0; j < m; j++)
		{
			if(i==row || j==col) continue;
			size_t src_ind = i*m+j;
			size_t dest_ind = dest_i * (n-1) + dest_j;
			output[dest_ind] = matrix->matrix[src_ind];
			dest_j++;
			if(dest_j == n-1)
			{
				dest_j = 0;
				dest_i++;
			}
		}
	}
	return SUCCESS;
}

double matrix_norm(const mat_t* matrix)
{
	assert(matrix);
	mat_t *trMat = matrix_create(matrix->ncol, matrix->nrow);
	mat_t *mult = matrix_create(trMat->nrow, matrix->ncol);
	matrix_transpose(matrix, trMat);
	matrix_multiply(trMat, matrix, mult);
	int status = SUCCESS;
	double trace = matrix_trace(mult, &status);
	matrix_destroy(trMat);
	matrix_destroy(mult);
	return sqrt(trace);
}

static void Swap(double *x, double *y)
{
	double tmp = *x;
	*x = *y;
	*y = tmp;
}

static void matrix_swap_rows(mat_t* matrix, size_t i, size_t j)
{
	size_t n = matrix->ncol;
	for(size_t k = 0; k < n; k++)
	{
		Swap(&(matrix->matrix[i*n+k]),&(matrix->matrix[j*n+k]));
	}
}

static double matrix_LU_det(const mat_t* matrix, size_t n)
{
	mat_t *tmp = matrix_create(n, n);
	matrix_set(tmp, matrix->matrix, n*n);
	
	double det = 1.0;
	double tol = 1e-9;
	int num_swaps = 0;
	
	for(size_t i = 0; i < n; i++)
	{
		//find the largest element in the current column
		size_t pivot = i;
		for(size_t j = i + 1; j < n; j++)
		{
			if(fabs(matrix_get_val(tmp, j, i)) > fabs(matrix_get_val(tmp, pivot, i))) pivot = j;
		}
		// swap rows to bring pivot to the main diagonal
		if(pivot != i)
		{
			matrix_swap_rows(tmp, i, pivot);
			num_swaps++;
		}
		//if the diagonal element is zero or degenerated. determinant is zero
		if(fabs(matrix_get_val(tmp, i ,i)) < tol)
		{
			matrix_destroy(tmp);
			return 0;
		}
		// elimination - zero out elements below the diagnoal
		for(size_t j = i + 1; j < n; j++)
		{
			double factor = matrix_get_val(tmp, j, i) / matrix_get_val(tmp, i ,i);
			for(size_t k = i + 1; k < n; k++)
			{
				double val = matrix_get_val(tmp, j, k) - factor * matrix_get_val(tmp, i, k);
				tmp->matrix[j*tmp->ncol + k] = val;
			}
		}
		//determinant is the product of the diagnoal elements
		det *= matrix_get_val(tmp, i, i);
	}
	matrix_destroy(tmp);
	return (num_swaps%2 == 0)?det:-det;
}

static double RecDetHelper(const mat_t* matrix, size_t n)
{
	if(n == 1) return matrix->matrix[0];
	if(n == 2) return (matrix->matrix[0] * matrix->matrix[3] - matrix->matrix[1] * matrix->matrix[2]);
	double det = 0; 
	int sign = 1;
	for(size_t i=0; i < n; i++)
	{
		mat_t *subMat = matrix_create(n-1, n-1);
		matrix_get_submatrix(matrix, 0, i, subMat);
		det += sign * matrix->matrix[i]*RecDetHelper(subMat,n-1);
		sign = -sign;
		matrix_destroy(subMat);
	}
	return det;
}

UNUSED_FUNCTION static double RecDetHelper(const mat_t* matrix, size_t n);

double matrix_determinant(const mat_t* matrix, int* status)
{
	assert(matrix);
	assert(matrix->nrow == matrix->ncol);
	*status = SUCCESS;
	//return RecDetHelper(matrix, matrix->nrow);
	return matrix_LU_det(matrix, matrix->nrow);	
}

static double ComputeMinor(const mat_t* matrix, size_t row, size_t col)
{
	size_t n = matrix->nrow;
	mat_t *minorMat = matrix_create(n-1, n-1);
	matrix_get_submatrix(matrix, row, col, minorMat);
	int status = SUCCESS;
	double minor = matrix_determinant(minorMat, &status);
	matrix_destroy(minorMat);
	return minor;
}

static int ComputeCofactors(const mat_t* matrix, mat_t* result)
{
	int sign = 1;
	size_t n = matrix->nrow;
	double *output = result->matrix;
	for(size_t i=0; i < n; i++)
	{
		sign = (i%2==0)?1:-1;
		for(size_t j = 0; j < n; j++)
		{
			output[i*n+j] = matrix->matrix[i*n+j] * sign;
			if(output[i*n+j] == 0) output[i*n+j] = 0;
			sign = -sign;
		}
	}
	return SUCCESS;
}

int matrix_inverse(const mat_t* matrix, mat_t* result)
{
	assert(matrix);
	if(matrix->nrow != matrix->ncol) return DIMENSIONS_ERROR;
	size_t n = matrix->nrow;
	int status = SUCCESS;
	mat_t *minorsMat = matrix_create(n, n);
	for(size_t i=0; i < n; i++)
	{
		for(size_t j = 0; j < n; j++)
		{
			minorsMat->matrix[i*n+j] = ComputeMinor(matrix, i, j);
		}
	}
	mat_t *cofactorMat = matrix_create(n, n);
	ComputeCofactors(minorsMat, cofactorMat);
	mat_t *adjuMat = matrix_create(n, n);
	matrix_transpose(cofactorMat, adjuMat);
	matrix_scalar_multiply(adjuMat, 1 / matrix_determinant(matrix, &status), result);
	
	matrix_destroy(minorsMat);
	matrix_destroy(cofactorMat);
	matrix_destroy(adjuMat);
	return status;
}

void matrix_set_element(mat_t* matrix, size_t row_id, size_t col_id, double value){
	assert(matrix);
	matrix->matrix[row_id*matrix->ncol + col_id] = value;
}


