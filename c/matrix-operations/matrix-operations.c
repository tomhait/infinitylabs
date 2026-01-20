#include "matrix-operations.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>

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
	return SUCCESS;
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

