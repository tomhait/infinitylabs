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
	mat_t *mat1 = matrix_create(3, 3);
	double arr[] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
	matrix_set(mat1, arr, sizeof(arr)/sizeof(arr[0]));
	PrintMat(mat1);
	mat_t *mat2 = matrix_create(3, 3);
	matrix_set(mat2, arr, sizeof(arr)/sizeof(arr[0]));
	if(matrix_is_same(mat1, mat2)){
		printf("Same\n");
	} else printf("Not the same\n");
	
	mat_t *mat3 = matrix_create(3, 3);
	matrix_add(mat1, mat2, mat3);
	PrintMat(mat3);
	mat_t *mat4 = matrix_create(3, 5);
	matrix_set(mat4, arr, sizeof(arr)/sizeof(arr[0]));
	PrintMat(mat4);
	mat_t *mat5 = matrix_create(3, 3);
	matrix_multiply(mat1, mat2, mat5);
	PrintMat(mat5);
	mat_t *mat6 = matrix_create(3, 5);
	matrix_scalar_multiply(mat4, 2, mat6);
	PrintMat(mat6);
	matrix_destroy(mat1);
	matrix_destroy(mat2);
	matrix_destroy(mat3);
	matrix_destroy(mat4);
	matrix_destroy(mat5);
	matrix_destroy(mat6);
	return 0;
}
