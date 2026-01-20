#include "matrix-operations.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <math.h>

struct mat_t{
	size_t nrow;
	size_t ncol;
	double *matrix;
};

mat_t* matrix_create(size_t rows, size_t cols){
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

void matrix_destroy(mat_t* matrix){
	assert(matrix);
	free(matrix->matrix);
	free(matrix);
}

int matrix_add(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result){
	assert(matrix_a);
	assert(matrix_b);
	assert(matrix_a->nrow == matrix_b->nrow);
	assert(matrix_a->ncol == matrix_b->ncol);
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

static void check_multiplied_matrices(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result){
	assert(matrix_a);
	assert(matrix_b);
	assert(matrix_a->ncol == matrix_b->nrow);
	assert(result);
	assert(result->nrow == matrix_a->nrow);
	assert(result->ncol == matrix_b->ncol);
}

int matrix_multiply(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result){

	check_multiplied_matrices(matrix_a, matrix_b, result);
	
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

int matrix_scalar_multiply(const mat_t* matrix, const double scalar, mat_t* result){
	assert(matrix);
	assert(result);
	assert(matrix->nrow == result->nrow);
	assert(matrix->ncol == result->ncol);
	
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

int matrix_is_same(const mat_t* matrix_a, const mat_t* matrix_b){
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

int matrix_set(mat_t* matrix, double* elements, size_t size){
	assert(matrix);
	size_t mat_size = matrix->nrow * matrix->ncol;
	if(mat_size > size) mat_size = size;
	for(size_t i=0; i< mat_size; i++) matrix->matrix[i] = elements[i];
	return SUCCESS;
}

int matrix_transpose(const mat_t* matrix, mat_t* result){
	assert(matrix);
	assert(result);
	assert(matrix->nrow == result->ncol);
	assert(matrix->ncol == result->nrow);
	
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

double matrix_trace(const mat_t* matrix, int* status){
	assert(matrix);
	assert(matrix->nrow == matrix->ncol);
	double trace = 0;
	size_t COLS = matrix->ncol;
	for(size_t i=0; i < matrix->nrow; i++) trace += matrix->matrix[i*COLS + i];
	*status = SUCCESS;
	return trace;
}

size_t matrix_get_num_of_rows(const mat_t* matrix){
	assert(matrix);
	return matrix->nrow;
}

size_t matrix_get_num_of_cols(const mat_t* matrix){
	assert(matrix);
	return matrix->ncol;
}

double matrix_get_val(const mat_t* matrix, const size_t row_idx, const size_t col_idx){
	assert(matrix);
	assert(matrix->nrow > row_idx);
	assert(matrix->ncol > col_idx);
	return matrix->matrix[row_idx*matrix->ncol + col_idx];
}

int matrix_get_submatrix(const mat_t* matrix, size_t row, size_t col, mat_t* result){
	assert(matrix);
	assert(result);
	assert(matrix->nrow-1 == result->nrow);
	assert(matrix->ncol-1 == result->ncol);
	double *output = result->matrix;
	size_t n = matrix->nrow;
	size_t m= matrix->ncol;
	size_t dest_i = 0, dest_j = 0;
	for(size_t i=0; i < n; i++){
		for(size_t j=0; j < m; j++){
			if(i==row || j==col) continue;
			size_t src_ind = i*m+j;
			size_t dest_ind = dest_i * (n-1) + dest_j;
			output[dest_ind] = matrix->matrix[src_ind];
			dest_j++;
			if(dest_j == n-1){
				dest_j = 0;
				dest_i++;
			}
		}
	}
	return SUCCESS;
}

double matrix_norm(const mat_t* matrix){
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

static double RecDetHelper(const mat_t* matrix, size_t n){
	double det = 0; 
	int sign = 1;
	if(n == 1) return matrix->matrix[0];
	if(n == 2) return (matrix->matrix[0] * matrix->matrix[3] - matrix->matrix[1] * matrix->matrix[2]);
	
	for(size_t i=0; i < n; i++){
		mat_t *subMat = matrix_create(n-1, n-1);
		matrix_get_submatrix(matrix, 0, i, subMat);
		det += sign * matrix->matrix[i]*RecDetHelper(subMat,n-1);
		sign = -sign;
		matrix_destroy(subMat);
	}
	return det;
}

double matrix_determinant(const mat_t* matrix, int* status){
	assert(matrix);
	assert(matrix->nrow == matrix->ncol);
	*status = SUCCESS;
	return RecDetHelper(matrix, matrix->nrow);	
}
int matrix_inverse(const mat_t* matrix, mat_t* result);


