#include "matrix-operations.h"
#include <stdio.h>

void PrintMat(mat_t* mat){
	size_t nrows = matrix_get_num_of_rows(mat);
	size_t ncols = matrix_get_num_of_cols(mat);
	for(size_t i=0; i < nrows; i++){
		for(size_t j=0; j<ncols; j++){
			if(j==0){
				printf("%.2f", matrix_get_val(mat, i, j));
				continue;
			}
			printf(" %.2f", matrix_get_val(mat, i, j));
		}
		printf("\n");
	}
	printf("\n\n");
}


int main(){
	int status = SUCCESS;
	mat_t *mat1 = matrix_create(3, 3);
	double arr[] = {1, 9, 3, 4, 5, 6, 7, 8, 9};
	matrix_set(mat1, arr, sizeof(arr)/sizeof(arr[0]));
	PrintMat(mat1);
	printf("The matrix norm is: %.2f\n", matrix_norm(mat1));
	printf("The deteminant is: %.2f\n", matrix_determinant(mat1, &status));
	mat_t *mat2 = matrix_create(3, 3);
	matrix_set(mat2, arr, sizeof(arr)/sizeof(arr[0]));
	if(matrix_is_same(mat1, mat2)){
		printf("Same\n");
	} else printf("Not the same\n");
	
	printf("Trace is: %.2f\n", matrix_trace(mat2, &status));
	mat_t *mat3 = matrix_create(3, 3);
	matrix_add(mat1, mat2, mat3);
	PrintMat(mat3);
	mat_t *mat4 = matrix_create(3, 5);
	matrix_set(mat4, arr, sizeof(arr)/sizeof(arr[0]));
	PrintMat(mat4);
	printf("The matrix norm is: %.2f\n", matrix_norm(mat4));
	mat_t *mat7 = matrix_create(5, 3);
	matrix_transpose(mat4, mat7);
	PrintMat(mat7);
	mat_t *mat5 = matrix_create(3, 3);
	matrix_multiply(mat1, mat2, mat5);
	PrintMat(mat5);
	mat_t *mat6 = matrix_create(3, 5);
	matrix_scalar_multiply(mat4, 2, mat6);
	PrintMat(mat6);
	mat_t *mat8 = matrix_create(2, 4);
	matrix_get_submatrix(mat6, 2, 4, mat8);
	PrintMat(mat8);
	printf("The matrix norm is: %.2f\n", matrix_norm(mat8));
	double arr2[] = {5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0 ,0 ,0 ,0, 5, 0, 0, 0, 0, 0, 0, 0, 5};
	mat_t *mat9 = matrix_create(7, 7);
	matrix_set(mat9, arr2, sizeof(arr2)/sizeof(arr2[0]));
	PrintMat(mat9);
	mat_t *mat10 = matrix_create(7 ,7);
	matrix_inverse(mat9, mat10);
	PrintMat(mat10);
	matrix_destroy(mat1);
	matrix_destroy(mat2);
	matrix_destroy(mat3);
	matrix_destroy(mat4);
	matrix_destroy(mat5);
	matrix_destroy(mat6);
	matrix_destroy(mat7);
	matrix_destroy(mat8);
	matrix_destroy(mat9);
	matrix_destroy(mat10);
	return 0;
}
